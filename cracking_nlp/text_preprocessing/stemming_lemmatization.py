# Simple stemmer: chop suffixes by rules
def stem(word):
    suffixes = ["ing", "ly", "ed", "ies", "es", "s"]   # longer suffixes first
    for suf in suffixes:
        if word.endswith(suf) and len(word) - len(suf) >= 3:   # keep at least 3 letters
            return word[:-len(suf)]
    return word

# Simple lemmatizer: dictionary lookup
lemma_dict = {
    "running": "run", "ran": "run", "runs": "run",
    "better": "good", "best": "good",
    "studies": "study", "studied": "study",
    "mice": "mouse", "children": "child",
    "is": "be", "was": "be", "were": "be",
}

def lemmatize(word):
    if word in lemma_dict:
        return lemma_dict[word]
    return word          # not in dict -> leave as is

words = ["running", "studies", "better", "ran", "mice", "quickly"]
for w in words:
    print(w, "-> stem:", stem(w), "| lemma:", lemmatize(w))

# running -> stem: runn   | lemma: run     <- simple stemmer even worse than Porter
# studies -> stem: stud   | lemma: study
# better  -> stem: better | lemma: good
# ran     -> stem: ran    | lemma: run
# mice    -> stem: mice   | lemma: mouse
# quickly -> stem: quick  | lemma: quickly