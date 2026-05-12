import numpy as np

# 1. Embedding
class Embedding:
    def __init__(self, vocab_size, d_model):
        # Init a random small weight matrix with the size of vocab and d_model
        # vocab_size: number of vocab in a dataset
        # d_model: dimension size of the model, more dimensions, more meaning
        self.W = np.random.randn(vocab_size, d_model) * 0.01

    def forward(self, token_ids):
        # Return the embedding vector of the token, used for learning
        return self.W[token_ids]

# 2. Positional encoding
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


# 3. Linear projection (Q - Query, K - Key, V - Values)
# We would uses this 3 times for Q, K, V matrix
# Q = what this token is looking for
# K = what this token contains
# V = the information this token provides
class Linear:
    def __init__(self, in_dim, out_dim):
        # Init a random small weight matrix with the size of in_dim and out_dim
        self.W = np.random.randn(in_dim, out_dim) * 0.01

        # Init a zero array with the size of out_dim
        self.b = np.zeros(out_dim)

    def forward(self, x):
        return x @ self.W + self.b  # (seq_len, out_dim)

# 4. Scaled dot-product attention
# Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V
def softmax(x, axis=-1):
    x = x - x.max(axis=axis, keepdims=True)   # numerical stability
    e = np.exp(x)
    return e / e.sum(axis=axis, keepdims=True)

def attention(Q, K, V, mask=None):
    # Takes the last dimension, in this code, Q.shape[-1] = d_model
    # Which is equal the meaning each word can hold
    # Which mean takes all the information of the sequence
    d_k = Q.shape[-1]

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
    scores = Q @ K.swapaxes(-2, -1) / np.sqrt(d_k)  # (seq, seq)

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
        scores = np.where(mask == 0, -1e9, scores)   # causal mask

    weights = softmax(scores)          # (seq, seq)
    # Weights @ V is the new token representation after mixing information
    # Key point: Produces a new token vector according to the attention weights
    return weights @ V, weights        # (seq, d_v), (seq, seq)


# 5. Multi-head attention
# Run H attention heads in parallel, concat results
class MultiHeadAttention:
    def __init__(self, d_model, num_heads):
        assert d_model % num_heads == 0
        self.h  = num_heads

        # Split the model dimension; Each head worked on a (d_model // num_heads)-dim vectors
        self.dk = d_model // num_heads

        # One projection per head (simplified: could use single large matrix)
        # Each head has it owns Q, K, V matrices
        self.Wq = [Linear(d_model, self.dk) for _ in range(num_heads)]
        self.Wk = [Linear(d_model, self.dk) for _ in range(num_heads)]
        self.Wv = [Linear(d_model, self.dk) for _ in range(num_heads)]
        self.Wo = Linear(d_model, d_model)   # output projection

    def forward(self, x, mask=None):
        heads = []
        for i in range(self.h):
            Q = self.Wq[i].forward(x)   # (seq, dk)
            K = self.Wk[i].forward(x)
            V = self.Wv[i].forward(x)
            out, _ = attention(Q, K, V, mask)
            heads.append(out)

        concat = np.concatenate(heads, axis=-1)  # (seq, d_model)
        return self.Wo.forward(concat)


# 6. Feed-forward layer
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
        return self.l2.forward(np.maximum(0, self.l1.forward(x)))  # ReLU


# 7. Layer norm
class LayerNorm:
    def __init__(self, d_model, eps=1e-6):
        self.gamma = np.ones(d_model)
        self.beta  = np.zeros(d_model)
        self.eps   = eps

    def forward(self, x):
        mean = x.mean(axis=-1, keepdims=True)
        std  = x.std(axis=-1,  keepdims=True)
        # Adding beta and gamma to
        # learn the optimal scale and shift for each feature after normalization
        return self.gamma * (x - mean) / (std + self.eps) + self.beta

# 8. Transformer encode block
class EncoderBlock:
    def __init__(self, d_model, num_heads, d_ff):
        self.attn  = MultiHeadAttention(d_model, num_heads)
        self.ff    = FeedForward(d_model, d_ff)
        self.norm1 = LayerNorm(d_model)
        self.norm2 = LayerNorm(d_model)

    def forward(self  , x, mask=None):
        # Adding 'x' before each layer to keep the old 'x' weight
        # of the before layer or else, after 12 layers, the original information 
        # from embedding is gone. Leading to gradients vanishing during training. Thus, model can't learn. 
        # Fun fact: This was actually a huge breakthrough in deep learning (ResNet, 2015),
        # before this, training networks deeper than ~10 layers was nearly impossible.
        # Sub-layer 1: Multi-Head Attention + residual
        x = self.norm1.forward(x + self.attn.forward(x, mask))
        # Sub-layer 2: Feed-Forward + residual
        x = self.norm2.forward(x + self.ff.forward(x))
        return x


# 9. Full transformer (Encoder only)
class Transformer:
    def __init__(self, vocab_size, d_model=32, num_heads=4, d_ff=64, num_layers=2):
        self.embed  = Embedding(vocab_size, d_model)
        self.layers = [EncoderBlock(d_model, num_heads, d_ff) for _ in range(num_layers)]

    def forward(self, token_ids):
        x  = self.embed.forward(token_ids)              # Embedding
        x += positional_encoding(len(token_ids), x.shape[-1])  # + Pos Enc

        for layer in self.layers:
            x = layer.forward(x)

        return x   # (seq_len, d_model)


# Demo
if __name__ == "__main__":
    np.random.seed(42)

    vocab_size = 100
    token_ids  = np.array([5, 23, 1, 77, 42])   # a 5-token sentence

    model  = Transformer(vocab_size, d_model=16, num_heads=4, d_ff=32, num_layers=2)
    output = model.forward(token_ids)

    print("Input  tokens :", token_ids)
    print("Output shape  :", output.shape)   # (5, 16)
    print("Output (first token):", output[0].round(4))