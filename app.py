from flask import Flask, render_template, request
from utilities.models import db, Annotation

import pandas as pd
import spacy
from spacy import displacy
from sqlalchemy import select
from flask import redirect, url_for
from sqlalchemy import func
import random

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "instance" / "annotation.db"

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"]  = f"sqlite:///{DB_PATH}" 
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

#nlp = spacy.load("en_core_web_sm") #### Toggle back to spacy model to see the difference

nlp = spacy.load(r"./output/model-last") #### Toggle to trained model




LABELS = [
    "PERSON",
    "ORG",
    "GPE",
    "LOC",
    "DATE",
    "TIME",
    "MONEY",
    "PRODUCT",
    "EVENT",
    "LAW",
    "LANGUAGE",
    "WORK_OF_ART",
    "NORP",
    "FAC",
    "ORDINAL",
    "CARDINAL",
    "PERCENT",
    "QUANTITY",
    "CUSTOM"
]

def get_entities(doc):
    ents = []
    index = 0

    for sent in doc.sents:
        # Named entities in the sentence
        for ent in sent.ents:
            ents.append(
                {
                    "index": index,
                    "sentence": sent.text,
                    "text": ent.text,
                    "start": ent.start_char - sent.start_char,
                    "end": ent.end_char - sent.start_char,
                    "label": ent.label_,
                }
            )
            index += 1

        # Noun chunks in the sentence
        for chunk in sent.noun_chunks:
            ents.append(
                {
                    "index": index,
                    "sentence": sent.text,
                    "text": chunk.text,
                    "start": chunk.start_char - sent.start_char,
                    "end": chunk.end_char - sent.start_char,                    
                    "label": "",
                }
            )
            index += 1

    return remove_duplicates(ents)


def remove_duplicates(entities):
    """
    Remove duplicate entities based on their text span.
    """
    seen = set()
    unique = []

    for ent in entities:
        key = (ent["start"], ent["end"], ent["text"].lower())

        if key not in seen:
            seen.add(key)
            unique.append(ent)

    # Reassign indices after removing duplicates
    for i, ent in enumerate(unique):
        ent["index"] = i

    return unique

from collections import Counter

def bag_of_words(doc):
    return Counter(
        token.lemma_.lower()
        for token in doc
        if token.is_alpha and not token.is_stop and not token.is_punct
    )

@app.route("/")
def home():

    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process():

    text = request.form["text"]

    doc = nlp(text)

    html = displacy.render(
        doc,
        style="ent",
        page=False
    )
    
    for label in set(ent.label_ for ent in doc.ents):
        html = html.replace(
            f">{label}</span>",
            f' title="{spacy.explain(label)}">{label}</span>'
        )

    ents = get_entities(doc)
    
    bow = bag_of_words(doc)
    
    words = [
        {
            "text": word,
            "count": count,
            "size": 16 + count * 12,              # font size
            "color": random.choice([
                "#1976d2", "#388e3c", "#d32f2f",
                "#7b1fa2", "#f57c00"
            ])
        }
        for word, count in bow.items()
    ]
     
    
    return render_template(
        "index.html",
        html=html,
        entities=ents,
        labels=LABELS,
        text=text,words=words,
    )


@app.route("/save", methods=["POST"])
def save():

    text = request.form["text"]

    doc = nlp(text)
    
    entities = get_entities(doc)

    training_entities = []

    for ent in entities:

        label = request.form.get(f"label_{ent['index']}")

        # Skip unlabelled noun chunks
        if not label:
            continue

        existing = Annotation.query.filter(
            func.lower(Annotation.sentence) == ent["sentence"].lower(),
            func.lower(Annotation.entity_text) == ent["text"].lower(),
            Annotation.start==ent["start"],
            Annotation.end==ent["end"]
        ).first()

        if existing:
            continue

        ann = Annotation(
            sentence=ent["sentence"],
            entity_text=ent["text"],
            start=ent["start"],
            end=ent["end"],
            label=label,
        )
        

        db.session.add(ann)

        training_entities.append(
            (
                ent["start"],
                ent["end"],
                label,
            )
        )

    db.session.commit()

    print(
        (
            text,
            {
                "entities": training_entities
            },
        )
    )

    return "Saved!"


@app.route("/dataframe")
def dataframe():

    stmt = select(
        Annotation.id,
        Annotation.sentence,
        Annotation.entity_text,
        Annotation.start,
        Annotation.end,
        Annotation.label
    )

    with db.engine.connect() as conn:
        df = pd.read_sql(stmt, conn)
        
    # Add delete buttons
    html = df.to_html(
        index=False,
        escape=False
    )

    # Insert a delete column
    rows = ""

    for _, row in df.iterrows():
        rows += f"""
        <tr>
            <td>{row['id']}</td>
            <td>{row['sentence']}</td>
            <td>{row['entity_text']}</td>
            <td>{row['start']}</td>
            <td>{row['end']}</td>
            <td>{row['label']}</td>
            <td>
                <form method="POST" action="/delete_annotation/{row['id']}">
                    <button type="submit">Delete</button>
                </form>
            </td>
        </tr>
        """

    table = f"""
    <table border="1">
        <thead>
            <tr>
                <th>ID</th>
                <th>Sentence</th>
                <th>Entity Text</th>
                <th>Start</th>
                <th>End</th>
                <th>Label</th>
                <th>Action</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
    """

    return table



@app.route("/delete_annotation/<int:id>", methods=["POST"])
def delete_annotation(id):

    annotation = Annotation.query.get_or_404(id)

    db.session.delete(annotation)
    db.session.commit()

    return redirect(url_for("dataframe"))

if __name__ == "__main__":
    app.run(debug=True)
