docs = [
    "i love nlp",
    "i love love pizza",
    "nlp is fun",
]

# Step 1: build vocab (every unique word gets a column)
vocab = {}
for doc in docs:
    for word in doc.split():
        if word not in vocab:
            vocab[word] = len(vocab)
# {'i': 0, 'love': 1, 'nlp': 2, 'pizza': 3, 'is': 4, 'fun': 5}

# Step 2: count words per doc
bow = []
for doc in docs:
    vec = [0] * len(vocab)          # one slot per vocab word
    for word in doc.split():
        idx = vocab[word]
        vec[idx] += 1               # count it
    bow.append(vec)

print("Vocab:", vocab)
for doc, vec in zip(docs, bow):
    print(f"{doc:20s} -> {vec}")

# i love nlp           -> [1, 1, 1, 0, 0, 0]
# i love love pizza    -> [1, 2, 0, 1, 0, 0]
# nlp is fun           -> [0, 0, 1, 0, 1, 1]

# binary BoW: just 1 if word appears, 0 if not
binary = []
for vec in bow:
    binary.append([1 if c > 0 else 0 for c in vec])

# new doc: words not in vocab are ignored
new_doc = "i love sushi"
vec = [0] * len(vocab)
for word in new_doc.split():
    if word in vocab:               # "sushi" unknown -> skipped
        vec[vocab[word]] += 1
print(new_doc, "->", vec)           # [1, 1, 0, 0, 0, 0]