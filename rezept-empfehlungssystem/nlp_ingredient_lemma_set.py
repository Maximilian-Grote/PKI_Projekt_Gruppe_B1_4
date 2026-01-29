import spacy

nlp = spacy.load("en_core_web_sm")

def get_lemma_set(text):
    # Erstellt eine Menge der Grundformen aller Wörter im Text
    doc = nlp(text.lower())
    return {token.lemma_ for token in doc if not token.is_stop}

# Beispiel
user_input = get_lemma_set("Basil Leaves") # {'basil', 'leaf'}
db_ingredient = get_lemma_set("Basil")     # {'basil'}

# Logik: Wenn alle Wörter des DB-Eintrags im User-Input vorkommen (oder umgekehrt)
if db_ingredient.issubset(user_input) or user_input.issubset(db_ingredient):
    print("Match gefunden!")