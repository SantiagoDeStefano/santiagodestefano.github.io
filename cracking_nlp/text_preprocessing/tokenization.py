import re

text = "I love NLP! NLP loves me, I think."

# Step 1: lower case
text = text.lower()

# Step 2: tokenize
# naive:
token_simple = text.split()
print(token_simple)

# better:
# \w+    = a word (letters/digits)
# [^\w\s] = a single punctuation char
tokens = re.findall(r"\w+|[^\w\s]", text)
print(tokens)

# Step 3: build vocab (word -> id)
vocab = {"<pad>": 0, "<unk>": 1}
for tok in tokens:
    if tok not in vocab:
        vocab[tok] = len(vocab)     # next free id
# {'<pad>':0, '<unk>':1, 'i':2, 'love':3, 'nlp':4, '!':5, ...}
print(vocab)

# reverse: id -> word (for decoding)
id_to_word = {}
for word, idx in vocab.items():
    id_to_word[idx] = word
print(id_to_word)

# Step 4: encode (text -> ids)
def encode(sentence):
    toks = re.findall(r"\w+|[^\w\s]", sentence.lower())
    ids = []
    for t in toks:
        if t in vocab:
            ids.append(vocab[t])
        else:
            ids.append(vocab["<unk>"])   # word never seen -> unknown
    return ids

# Step 5: decode (ids -> text)
def decode(ids):
    words = []
    for i in ids:
        words.append(id_to_word[i])
    return " ".join(words)

ids = encode("I love pizza!")
print(ids)            # [2, 3, 1, 5]  -> "pizza" unknown = 1
print(decode(ids))    # "i love <unk> !"

chars = list("nlp")