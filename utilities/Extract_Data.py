
from sqlalchemy import select
from sqlalchemy import func
from sqlalchemy import create_engine
from models import db, Annotation
from sqlalchemy.orm import sessionmaker
import pandas as pd
from tqdm import tqdm
import spacy
from spacy.tokens import DocBin
import json
from collections import defaultdict

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "instance" / "annotation.db"

db = DocBin()
nlp = spacy.load("en_core_web_sm") # load other spacy model

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    echo=True,  # Optional: logs SQL queries
)


stmt = select(
    Annotation.id,
    Annotation.sentence,
    Annotation.entity_text,
    Annotation.start,
    Annotation.end,
    Annotation.label
)

Session = sessionmaker(bind=engine)

session = Session()
    
with Session() as session:
    rows = session.execute(stmt).all()

grouped = defaultdict(list)

for row in rows:
    grouped[row.sentence].append({
        "start": row.start,
        "end": row.end,
        "label": row.label
    })

result = [
    {
        "sentence": sentence,
        "entities": entities
    }
    for sentence, entities in grouped.items()
]


for item in result:
    doc = nlp.make_doc(item["sentence"])

    ents = []
    for entity in item["entities"]:
        span = doc.char_span(
            entity["start"],
            entity["end"],
            label=entity["label"]
        )


        if span is not None:
            ents.append(span)

    doc.ents = ents
    db.add(doc)


#os.chdir(r'XXXX\XXXXX')
db.to_disk("../trainingData/train_self.spacy")
