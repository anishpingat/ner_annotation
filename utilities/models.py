from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Annotation(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    sentence = db.Column(db.Text)

    entity_text = db.Column(db.String(200))

    start = db.Column(db.Integer)

    end = db.Column(db.Integer)

    label = db.Column(db.String(50))