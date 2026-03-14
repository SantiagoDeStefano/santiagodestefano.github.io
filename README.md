# Transformer From Scratch
> Built with NumPy only, for learning purposes.

---

## What is a Transformer?
A transformer is a neural network architecture that processes sequences of tokens (words). It learns relationships between tokens using **attention** - instead of reading left to right like older models, it looks at all tokens at once.

---

## Architecture Overview
```
tokens → Embedding → Positional Encoding → N × EncoderBlock → output
                                                    ↓
                                         MultiHeadAttention
                                         FeedForward
                                         LayerNorm + Residual
```

---

## Components

### 1. Embedding
Maps token IDs (integers) to dense vectors.

```python
self.W = np.random.randn(vocab_size, d_model) * 0.01
```

- `self.W` is a lookup table of shape `(vocab_size, d_model)`
- `self.W[token_ids]` just returns rows by index - no math, just lookup
- `W` starts random, learns meaning during training via backprop
- `* 0.01` keeps initial values small → prevents exploding values at start

**Key point:** `d_model` = how many dimensions each token is represented in. More dimensions = more capacity to encode meaning.

---

### 2. Positional Encoding
Transformers have no sense of order - "I love cats" and "cats love I" look identical without position info. PE fixes this.

```python
PE[:, 0::2] = np.sin(pos * div)   # even dims
PE[:, 1::2] = np.cos(pos * div)   # odd dims
```

- Each position gets a **unique vector** using sine/cosine waves
- Each dimension oscillates at a **different frequency** - like a clock using seconds, minutes, hours
- Sin and cos are **paired per frequency**: `(col0, col1)` share freq0, `(col2, col3)` share freq1, etc.
- Values stay between -1 and 1 → stable for training

**Why sin/cos specifically?**
- Absolute position: every position gets a unique vector
- Relative position: due to trig identities, the model can compute "token B is 2 steps from token A" purely from their vectors, without knowing absolute positions

```
sin(pos + k) = sin(pos)*cos(k) + cos(pos)*sin(k)
→ PE[pos+k] = linear_function(PE[pos])
→ offset k has a consistent signature regardless of absolute position
```

---

### 3. Linear Projection (Q, K, V)
A general matrix multiplication layer, used 3 times to project input into Query, Key, Value spaces.

```python
return x @ self.W + self.b
```

- `@` = matrix multiply → transforms shape `(seq, in_dim) → (seq, out_dim)`
- `+ self.b` = bias, lets output shift independently of input
- Each of Wq, Wk, Wv has its **own independent W**, initialized separately

```
x → Wq → Q   "what am I looking for?"
x → Wk → K   "what do I contain?"
x → Wv → V   "what information do I give out?"
```

All three come from the **same input x**, just projected through different weight matrices.

---

### 4. Scaled Dot-Product Attention
```
Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) · V
```

```python
scores  = Q @ K.swapaxes(-2, -1) / np.sqrt(d_k)  # (seq, seq)
weights = softmax(scores)
out     = weights @ V
```

- `Q @ K^T` → dot product of every token pair → shape `(seq, seq)`
- `/ sqrt(d_k)` → prevents large values that make softmax saturate (e.g. `softmax([15,2,1]) = [0.999, 0.0007, 0.0003]` - bad gradients)
- `softmax` → converts scores to probabilities that **sum to 1** (e.g. "attend 70% to token A, 30% to token B")
- `weights @ V` → retrieve value vectors weighted by relevance → new token representation

**Causal mask** (optional): prevents tokens from attending to future positions.
```
scores before mask:      scores after mask:
2.1   0.5   0.3          2.1  -1e9  -1e9
1.2   0.8   0.4    →     1.2   0.8  -1e9
0.9   1.1   1.5          0.9   1.1   1.5
```

---

### 5. Multi-Head Attention
Instead of one attention pass on the full `d_model`, split into H smaller heads.

```python
self.dk = d_model // num_heads   # e.g. 768 / 12 = 64
```

Each head works on a `dk`-dimensional slice and learns a **different type of relationship**:
```
head 0  → maybe learns grammar
head 1  → maybe learns semantic meaning
head 2  → maybe learns positional patterns
...
```

All heads are concatenated and projected back via `Wo`:
```
H × (seq, dk) → concat → (seq, d_model) → @ Wo → (seq, d_model)
```

`Wo` learns how to **blend** all head perspectives into one unified representation.

---

### 6. Feed-Forward Layer
Applied independently to each token after attention.

```python
FFN(x) = ReLU(x @ W1 + b1) @ W2 + b2
```

```
d_model (768) → expand to d_ff (3072) → ReLU → contract back to d_model (768)
```

- `d_ff` = internal workspace, never seen outside this layer (usually `d_model * 4`)
- **Why expand then contract?** Gives the model a wider thinking space per token - like using scratch paper to solve a problem, then writing only the final answer
- **Why ReLU?** Without it, two linear layers collapse into one → no extra capacity gained

---

### 7. Layer Normalization
Normalizes each token vector to mean=0, std=1, then applies learned scale and shift.

```python
return self.gamma * (x - mean) / (std + self.eps) + self.beta
```

- After attention/feedforward, values can drift far from origin → unstable training
- LayerNorm brings them back to a stable range before the next layer
- `gamma` and `beta` are **learned** - let the model shift/scale after normalization if needed ("normalize, but then adjust to whatever is best")

---

### 8. Residual Connection
Each sub-layer adds the original input back before normalizing:

```python
x = norm(x + attn(x))   # not just norm(attn(x))
x = norm(x + ff(x))
```

**Why?** Without residuals, after 12 layers the original embedding information is completely gone → gradients vanish → model can't learn.

With residuals, original information flows through every layer via the shortcut:
```
x0 info → present in x1 → present in x2 → ... → present in x12
```

> **Fun fact:** Residual connections were a breakthrough in deep learning (ResNet, 2015). Before this, training networks deeper than ~10 layers was nearly impossible.

---

### 9. Encoder Block
Combines everything into one reusable block, stacked N times.

```python
x = norm1(x + MultiHeadAttention(x))
x = norm2(x + FeedForward(x))
```

---

## Key Concepts Summary

| Concept | One Line |
|---|---|
| Embedding | Token ID → dense vector lookup table |
| Positional Encoding | Unique sine/cosine fingerprint per position |
| Q, K, V | Same input, 3 different projections for attention |
| Attention | Weighted retrieval: which tokens matter to which |
| Multi-Head | H heads learn H different relationship types |
| FeedForward | Per-token thinking space, expand→activate→contract |
| LayerNorm | Stabilize values between layers |
| Residual | Keep original info flowing, prevent vanishing gradients |

---

## Usage
```python
import numpy as np

vocab_size = 100
token_ids  = np.array([5, 23, 1, 77, 42])

model  = Transformer(vocab_size, d_model=16, num_heads=4, d_ff=32, num_layers=2)
output = model.forward(token_ids)

print(output.shape)   # (5, 16) one 16-dim vector per token
```

---

## Next Steps
- Add backpropagation to make the model actually train
- Build a text classifier (e.g. bad word detector) using this encoder + a classification head
- Extend to a decoder (GPT-style) with causal masking for text generation
- Re-implement using PyTorch's autograd for automatic backprop