import numpy as np

docs = [
    "i love nlp",
    "i love pizza",
    "i hate bugs",
]

# step 1: vocab
vocab = {}
for doc in docs:
    for word in doc.split():
        if word not in vocab:
            vocab[word] = len(vocab)

N = len(docs)

# step 2: document frequency (how many docs contain each word)
df = [0] * len(vocab)
for doc in docs:
    for word in set(doc.split()):          # set -> count each word once per doc
        df[vocab[word]] += 1

# step 3: IDF
idf = []
for d in df:
    idf.append(np.log(N / d))

# step 4: TF-IDF per doc
tfidf = []
for doc in docs:
    words = doc.split()
    vec = [0.0] * len(vocab)
    for word in words:
        tf = words.count(word) / len(words)
        vec[vocab[word]] = tf * idf[vocab[word]]
    tfidf.append(vec)

print("Vocab:", vocab)
print("IDF:", np.round(idf, 2))
for doc, vec in zip(docs, tfidf):
    print(f"{doc:15s} -> {np.round(vec, 2)}")