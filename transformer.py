import numpy as np

# Utils
# 4. Scaled dot-product attention
# Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V
def softmax(x, axis=-1):
    x = x - x.max(axis=axis, keepdims=True)   # numerical stability
    e = np.exp(x)
    return e / e.sum(axis=axis, keepdims=True)

def softmax_backward(dout, out):
    # Example: softmax = [0.05, 0.95] while true label: positive (index = 0)
    # Which would cause a high loss, the gradient should answer:
    # scores[0] should increase, while scores[1] should decrease;
    # So softmax return something like: dscores = [−0.95, +0.95]
    # Meaning 
    # score[0] += 0.95: push up
    # score[1] -= 0.95: push down
    
    # dout: gradient flowing in (seq, seq) (from cross-entropy loss)
    # out:  softmax output (seq, seq) 
    # For each row: dL/dx_i = out_i * (dout_i - sum(dout * out))

    # Example: 
    # out = [0.05, 0.95]
    # dout = [-1.0, 0.0]
    s = np.sum(dout * out, axis=-1, keepdims=True)
    return out * (dout - s)

def cross_entropy_loss(probs, label):
    # probs: (1, num_classes) — model output after softmax
    # label: int — correct class index
    #
    # Loss = -log(prob of correct class)
    loss = -np.log(probs[0, label] + 1e-9)

    # Backward: gradient of cross-entropy + softmax combined
    # dL/dlogits = probs - one_hot(label)  (very clean formula)
    dlogits = probs.copy()
    dlogits[0, label] -= 1.0
    return loss, dlogits


# ─────────────────────────────────────────────────────────────
# 1. EMBEDDING
# ─────────────────────────────────────────────────────────────

class Embedding:
    def __init__(self, vocab_size, d_model):
        # Init a random small weight matrix with the size of vocab and d_model
        # vocab_size: number of vocab in a dataset
        # d_model: dimension size of the model, more dimensions, more meaning
        self.W  = np.random.randn(vocab_size, d_model) * 0.01
        self.dW = np.zeros_like(self.W)   # accumulated gradients

    def forward(self, token_ids):
        # Return the embedding vector of the token, used for learning
        self.token_ids = token_ids        # cache for backward
        return self.W[token_ids]

    def backward(self, dout):
        # dout: (seq, d_model) — gradient from next layer
        # Each token_id row in W receives gradient from dout
        # np.add.at handles repeated indices correctly
        self.dW = np.zeros_like(self.W)
        np.add.at(self.dW, self.token_ids, dout)
        # No gradient to pass further back (token_ids are integers, not differentiable)

    def step(self, lr):
        self.W -= lr * self.dW


# ─────────────────────────────────────────────────────────────
# 2. POSITIONAL ENCODING
# ─────────────────────────────────────────────────────────────

def positional_encoding(seq_len, d_model):
    # Init a zeros array with the size of seq_len and d_model
    # seq_len: number of tokens in the input sentence
    # d_model: dimension size of the model, more dimensions, more meaning
    PE = np.zeros((seq_len, d_model))

    # Arrange the array from (seq_len,) to (seq_len, 1)
    pos = np.arange(seq_len)[:, None]

    # arange(start, stop, step)
    # Arrange array to only have even index, size: (1, d_model/2)
    i   = np.arange(0, d_model, 2)[None, :]

    # How far each token is from the first token in a sequence
    div = np.exp(i * -(np.log(10000.0) / d_model))

    # 1. Each position have a unique vector, serving absolute position
    # 2. Relative position, example:
    # sin(5) = sin(3+2) = sin(3)*cos(2) + cos(3)*sin(2)
    # PE[5] = PE[3] * cos(2) + PE[3]_flipped * sin(2)
    # cos(2) and sin(2) are the same constants for any pair 2 steps apart
    PE[:, 0::2] = np.sin(pos * div)   # even dims
    PE[:, 1::2] = np.cos(pos * div)   # odd dims
    return PE  # (seq_len, D)
    # Backward: PE is a constant (no learned params), gradient passes through unchanged


# ─────────────────────────────────────────────────────────────
# 3. LINEAR PROJECTION (Q - Query, K - Key, V - Values)
# ─────────────────────────────────────────────────────────────

# We would uses this 3 times for Q, K, V matrix
# Q = what this token is looking for
# K = what this token contains
# V = the information this token provides
class Linear:
    def __init__(self, in_dim, out_dim):
        # Init a random small weight matrix with the size of in_dim and out_dim
        # He init: better for deep networks than * 0.01
        self.W  = np.random.randn(in_dim, out_dim) * np.sqrt(2.0 / in_dim)

        # Init a zero array with the size of out_dim
        self.b  = np.zeros(out_dim)
        self.dW = np.zeros_like(self.W)
        self.db = np.zeros_like(self.b)

    def forward(self, x):
        self.x = x                        # cache input for backward
        return x @ self.W + self.b        # (seq_len, out_dim)

    def backward(self, dout):
        # dout: gradient of loss w.r.t. output, shape (seq, out_dim)
        #
        # forward:  out = x @ W + b
        # backward:
        #   dL/dW = x.T @ dout          — how much each weight contributed
        #   dL/db = sum(dout, axis=0)   — bias gradient = sum over sequence
        #   dL/dx = dout @ W.T          — pass gradient back to previous layer
        self.dW = self.x.T @ dout
        self.db = dout.sum(axis=0)
        return dout @ self.W.T            # (seq, in_dim)

    def step(self, lr):
        self.W -= lr * self.dW
        self.b -= lr * self.db


# ─────────────────────────────────────────────────────────────
# 4. ATTENTION
# ─────────────────────────────────────────────────────────────

class AttentionHead:
    def __init__(self, d_model, dk):
        self.Wq = Linear(d_model, dk)
        self.Wk = Linear(d_model, dk)
        self.Wv = Linear(d_model, dk)

    def forward(self, x, mask=None):
        self.x  = x
        self.dk = self.Wq.W.shape[1]

        # Project input to Q, K, V
        self.Q = self.Wq.forward(x)      # (seq, dk)
        self.K = self.Wk.forward(x)      # (seq, dk)
        self.V = self.Wv.forward(x)      # (seq, dk)

        # Swaps the last two dimensions; which means transpose (row to column)
        # As Q : (seq, d_model); K : (seq, d_model)
        # If not transpose, @ would not be possible
        # Each items in scores is a dot product so it would be large;
        # Dividing it by /np.sqrt(d_k) because d_k is magnitude of attention and
        # it is a must for softmax to smoothen.
        # Thus, better gradient.
        # Ex: softmax([15, 2, 1]) == [0.999, 0.0007, 0.0003]
        # Key point: every elements of Q and K interact with each other
        # I really recommended to watch: Matrix multiplication as composition | Chapter 4, Essence of linear algebra - 3Blue1Brown
        self.scores_raw = self.Q @ self.K.T / np.sqrt(self.dk)  # (seq, seq)

        # Causal attention
        if mask is not None:
            # Example mask
            # 1 0 0
            # 1 1 0
            # 1 1 1
            # After masking:
            # 2.1  -1e9 -1e9
            # 0.5   1.2 -1e9
            # 0.3   0.8  1.5
            self.scores_raw = np.where(mask == 0, -1e9, self.scores_raw)
        self.mask = mask

        # Weights @ V is the new token representation after mixing information
        # Key point: Produces a new token vector according to the attention weights
        self.weights = softmax(self.scores_raw)   # (seq, seq)
        return self.weights @ self.V              # (seq, dk)

    def backward(self, dout):
        # dout: (seq, dk)

        # ── Backward through weights @ V ──────────────────────
        # forward:  out     = weights @ V
        # backward: dweights = dout @ V.T
        #           dV       = weights.T @ dout
        dweights = dout @ self.V.T                          # (seq, seq)
        dV       = self.weights.T @ dout                    # (seq, dk)

        # ── Backward through softmax ──────────────────────────
        dscores = softmax_backward(dweights, self.weights)  # (seq, seq)

        # ── Backward through masking ──────────────────────────
        # Masked positions had -1e9, gradient there is ~0 anyway
        if self.mask is not None:
            dscores = np.where(self.mask == 0, 0, dscores)

        # ── Backward through Q @ K.T / sqrt(dk) ──────────────
        # forward:  scores = Q @ K.T / sqrt(dk)
        # backward: dQ = dscores @ K / sqrt(dk)
        #           dK = dscores.T @ Q / sqrt(dk)
        dQ = dscores @ self.K / np.sqrt(self.dk)            # (seq, dk)
        dK = dscores.T @ self.Q / np.sqrt(self.dk)          # (seq, dk)

        # ── Backward through Q, K, V projections ─────────────
        dx_q = self.Wq.backward(dQ)
        dx_k = self.Wk.backward(dK)
        dx_v = self.Wv.backward(dV)

        # All three projections came from the same x, so sum their gradients
        return dx_q + dx_k + dx_v                           # (seq, d_model)

    def step(self, lr):
        self.Wq.step(lr)
        self.Wk.step(lr)
        self.Wv.step(lr)


# ─────────────────────────────────────────────────────────────
# 5. MULTI-HEAD ATTENTION
# ─────────────────────────────────────────────────────────────

# Run H attention heads in parallel, concat results
class MultiHeadAttention:
    def __init__(self, d_model, num_heads):
        assert d_model % num_heads == 0
        self.h  = num_heads

        # Split the model dimension; Each head worked on a (d_model // num_heads)-dim vectors
        self.dk = d_model // num_heads

        # One projection per head (simplified: could use single large matrix)
        # Each head has it owns Q, K, V matrices
        self.heads = [AttentionHead(d_model, self.dk) for _ in range(num_heads)]
        self.Wo = Linear(d_model, d_model)   # output projection

    def forward(self, x, mask=None):
        # Each head produces (seq, dk); concat → (seq, d_model)
        self.head_outs = [h.forward(x, mask) for h in self.heads]
        self.concat = np.concatenate(self.head_outs, axis=-1)  # (seq, d_model)
        return self.Wo.forward(self.concat)

    def backward(self, dout):
        # ── Backward through Wo ───────────────────────────────
        dconcat = self.Wo.backward(dout)                   # (seq, d_model)

        # ── Split gradient back to each head ──────────────────
        # Each head contributed dk columns to concat
        dhead_outs = np.split(dconcat, self.h, axis=-1)   # list of (seq, dk)

        # ── Backward through each head, sum dx ────────────────
        dx = sum(head.backward(dh) for head, dh in zip(self.heads, dhead_outs))
        return dx   # (seq, d_model)

    def step(self, lr):
        for h in self.heads:
            h.step(lr)
        self.Wo.step(lr)


# ─────────────────────────────────────────────────────────────
# 6. FEED-FORWARD LAYER
# ─────────────────────────────────────────────────────────────

# Two linear layers with ReLU: FFN(x) = ReLU(xW1 + b1)W2 + b2
class FeedForward:
    def __init__(self, d_model, d_ff):
        # Reminder:
        # d_model: information each token carries (input/output)
        # d_ff: workspace to transform that information (internal only)
        # Key point: d_model (768) -> expand to d_ff (3072) -> contract back to d_model (768)
        self.l1 = Linear(d_model, d_ff)
        self.l2 = Linear(d_ff, d_model)

    def forward(self, x):
        # 1. Apply first linear layer (d_model to d_ff)
        # 2. Apply ReLU
        # 3. Apply second linear layer (d_ff back to d_model)
        self.h        = self.l1.forward(x)          # (seq, d_ff)
        self.relu_out = np.maximum(0, self.h)
        return self.l2.forward(self.relu_out)

    def backward(self, dout):
        # ── Backward through l2 ───────────────────────────────
        drelu = self.l2.backward(dout)              # (seq, d_ff)

        # ── Backward through ReLU ─────────────────────────────
        # ReLU passes gradient only where input > 0
        dh = drelu * (self.h > 0)                   # (seq, d_ff)

        # ── Backward through l1 ───────────────────────────────
        return self.l1.backward(dh)                 # (seq, d_model)

    def step(self, lr):
        self.l1.step(lr)
        self.l2.step(lr)


# ─────────────────────────────────────────────────────────────
# 7. LAYER NORM
# ─────────────────────────────────────────────────────────────

class LayerNorm:
    def __init__(self, d_model, eps=1e-6):
        self.gamma  = np.ones(d_model)
        self.beta   = np.zeros(d_model)
        self.eps    = eps
        self.dgamma = np.zeros_like(self.gamma)
        self.dbeta  = np.zeros_like(self.beta)

    def forward(self, x):
        self.x    = x
        self.mean = x.mean(axis=-1, keepdims=True)
        self.std  = x.std(axis=-1,  keepdims=True)
        self.xhat = (x - self.mean) / (self.std + self.eps)   # normalized
        # Adding beta and gamma to
        # learn the optimal scale and shift for each feature after normalization
        return self.gamma * self.xhat + self.beta

    def backward(self, dout):
        N = self.x.shape[-1]   # d_model

        # ── Gradients for gamma and beta ──────────────────────
        self.dgamma = (dout * self.xhat).sum(axis=0)   # (d_model,)
        self.dbeta  = dout.sum(axis=0)                 # (d_model,)

        # ── Gradient for x (through normalization) ────────────
        # Full LayerNorm backward formula:
        dxhat = dout * self.gamma
        dx = (1.0 / (N * (self.std + self.eps))) * (
            N * dxhat
            - dxhat.sum(axis=-1, keepdims=True)
            - self.xhat * (dxhat * self.xhat).sum(axis=-1, keepdims=True)
        )
        return dx   # (seq, d_model)

    def step(self, lr):
        self.gamma -= lr * self.dgamma
        self.beta  -= lr * self.dbeta


# ─────────────────────────────────────────────────────────────
# 8. ENCODER BLOCK
# ─────────────────────────────────────────────────────────────

class EncoderBlock:
    def __init__(self, d_model, num_heads, d_ff):
        self.attn  = MultiHeadAttention(d_model, num_heads)
        self.ff    = FeedForward(d_model, d_ff)
        self.norm1 = LayerNorm(d_model)
        self.norm2 = LayerNorm(d_model)

    def forward(self, x, mask=None):
        # Adding 'x' before each layer to keep the old 'x' weight
        # of the before layer or else, after 12 layers, the original information
        # from embedding is gone. Leading to gradients vanishing during training. Thus, model can't learn.
        # Fun fact: This was actually a huge breakthrough in deep learning (ResNet, 2015),
        # before this, training networks deeper than ~10 layers was nearly impossible.

        # Sub-layer 1: Multi-Head Attention + residual
        self.x1      = x
        attn_out     = self.attn.forward(x, mask)
        self.res1    = x + attn_out                    # residual
        x            = self.norm1.forward(self.res1)

        # Sub-layer 2: Feed-Forward + residual
        self.x2      = x
        ff_out       = self.ff.forward(x)
        self.res2    = x + ff_out                      # residual
        x            = self.norm2.forward(self.res2)
        return x

    def backward(self, dout):
        # ── Sub-layer 2 backward ──────────────────────────────
        # forward: out = norm2(x2 + ff(x2))
        dres2 = self.norm2.backward(dout)              # through norm2
        dff   = self.ff.backward(dres2)                # through ff
        dx2   = dres2 + dff                            # through residual (+)

        # ── Sub-layer 1 backward ──────────────────────────────
        # forward: x2 = norm1(x1 + attn(x1))
        dres1 = self.norm1.backward(dx2)               # through norm1
        dattn = self.attn.backward(dres1)              # through attention
        dx1   = dres1 + dattn                          # through residual (+)
        return dx1   # (seq, d_model)

    def step(self, lr):
        self.attn.step(lr)
        self.ff.step(lr)
        self.norm1.step(lr)
        self.norm2.step(lr)


# ─────────────────────────────────────────────────────────────
# 9. CLASSIFICATION HEAD
# ─────────────────────────────────────────────────────────────
# Takes the first token ([CLS]) and predicts a class label

class ClassificationHead:
    def __init__(self, d_model, num_classes):
        self.linear = Linear(d_model, num_classes)

    def forward(self, x):
        # x: (seq, d_model) — take only first token as sentence representation
        self.cls   = x[0:1]                           # (1, d_model)
        logits     = self.linear.forward(self.cls)    # (1, num_classes)
        self.probs = softmax(logits)                  # (1, num_classes)
        return self.probs

    def backward(self, dout):
        # dout: (1, num_classes)
        dcls      = self.linear.backward(dout)        # (1, d_model)
        # Only first token receives gradient; rest get zero
        dx        = np.zeros_like(self.cls)
        dx[0]     = dcls
        return dx   # (1, d_model)

    def step(self, lr):
        self.linear.step(lr)


# ─────────────────────────────────────────────────────────────
# 10. FULL TRANSFORMER (Encoder + Classifier)
# ─────────────────────────────────────────────────────────────

class Transformer:
    def __init__(self, vocab_size, d_model=32, num_heads=4, d_ff=64,
                 num_layers=2, num_classes=2):
        self.embed  = Embedding(vocab_size, d_model)
        self.layers = [EncoderBlock(d_model, num_heads, d_ff) for _ in range(num_layers)]
        self.head   = ClassificationHead(d_model, num_classes)

    def forward(self, token_ids):
        x  = self.embed.forward(token_ids)                          # Embedding
        x += positional_encoding(len(token_ids), x.shape[-1])      # + Pos Enc

        for layer in self.layers:
            x = layer.forward(x)

        self.encoder_out = x
        return self.head.forward(x)   # (1, num_classes)

    def backward(self, dlogits):
        # ── Backward through classification head ──────────────
        dcls = self.head.backward(dlogits)             # (1, d_model)

        # Pad gradient to full sequence length (only cls token has gradient)
        dx      = np.zeros_like(self.encoder_out)
        dx[0:1] = dcls

        # ── Backward through encoder blocks (reverse order) ───
        for layer in reversed(self.layers):
            dx = layer.backward(dx)

        # ── Backward through positional encoding ──────────────
        # PE has no params, gradient passes unchanged

        # ── Backward through embedding ────────────────────────
        self.embed.backward(dx)

    def step(self, lr):
        self.embed.step(lr)
        for layer in self.layers:
            layer.step(lr)
        self.head.step(lr)

    def train_step(self, token_ids, label, lr=0.01):
        # 1. Forward pass
        probs = self.forward(token_ids)

        # 2. Compute loss
        loss, dlogits = cross_entropy_loss(probs, label)

        # 3. Backward pass
        self.backward(dlogits)

        # 4. Update weights
        self.step(lr)

        return loss, probs


# ─────────────────────────────────────────────────────────────
# DEMO
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    np.random.seed(42)

    # Tiny vocab
    # 0=<pad>, 1=hello, 2=world, 3=damn, 4=stupid, 5=nice, 6=great
    vocab_size  = 20
    num_classes = 2   # 0=clean, 1=bad

    dataset = [
        ([1, 2], 0),      # "hello world" → clean
        ([5, 2], 0),      # "nice world"  → clean
        ([6, 1], 0),      # "great hello" → clean
        ([3, 2], 1),      # "damn world"  → bad
        ([4, 1], 1),      # "stupid hello"→ bad
        ([3, 4], 1),      # "damn stupid" → bad
    ]

    model = Transformer(vocab_size, d_model=16, num_heads=4,
                        d_ff=32, num_layers=2, num_classes=2)

    print("Training...\n")
    for epoch in range(200):
        total_loss = 0
        for tokens, label in dataset:
            loss, _ = model.train_step(np.array(tokens), label, lr=0.005)
            total_loss += loss

        if (epoch + 1) % 50 == 0:
            print(f"Epoch {epoch+1:3d} | Loss: {total_loss/len(dataset):.4f}")

    print("\nPredictions:")
    labels = ["clean", "bad"]
    for tokens, true_label in dataset:
        probs = model.forward(np.array(tokens))
        pred  = np.argmax(probs)
        print(f"  tokens {str(tokens):10s} → {labels[pred]:5s} (true: {labels[true_label]}) | probs: {probs[0].round(3)}")