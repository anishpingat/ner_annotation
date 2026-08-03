import random
from spacy.tokens import DocBin
import spacy

nlp = spacy.blank("en")

doc_bin = DocBin().from_disk("../trainingData/train_self.spacy") #"data.spacy")
docs = list(doc_bin.get_docs(nlp.vocab))

random.seed(42)
random.shuffle(docs)

split_idx = int(0.8 * len(docs))
train_docs = docs[:split_idx]
test_docs = docs[split_idx:]

train_bin = DocBin(store_user_data=True)
for doc in train_docs:
    train_bin.add(doc)
train_bin.to_disk("../trainingData/train_data.spacy")

test_bin = DocBin(store_user_data=True)
for doc in test_docs:
    test_bin.add(doc)
test_bin.to_disk("../trainingData/test_data.spacy")
