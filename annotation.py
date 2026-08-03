import spacy

nlp = spacy.load("en_core_web_sm")


def process_document(text):

    doc = nlp(text)

    annotations = []

    for sent in doc.sents:

        for ent in sent.ents:

            annotations.append(
                {
                    "sentence": sent.text,
                    "entity": ent.text,
                    "original_label": ent.label_,
                    "corrected_label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "iob": ent.ent_iob_
                }
            )

    return annotations