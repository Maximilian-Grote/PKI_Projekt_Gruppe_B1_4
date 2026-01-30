import spacy
from collections import defaultdict

try:
    nlp = spacy.load("en_core_web_trf")
except:
    nlp = spacy.load("en_core_web_md")

# 1. NOISE (Ignorieren wir komplett)
NOISE_WORDS = {
    "chopped", "sliced", "diced", "minced", "fresh", "raw", "organic", 
    "large", "small", "whole", "halves", "pieces", "ground", "crushed", 
    "leaves", "leaf", "seed", "seeds", "nuts", "dark", "white", "yolks",
    "free-range", "beat", "stoned"  # Leaves/Seeds hier als Noise, da oft optional
}

# 2. STATES / FORMS (Definieren eine NEUE Gruppe)
# Wenn eines dieser Wörter auftaucht, ändert sich die Bedeutung fundamental.
# Das sind die "Zusätze", die den Kern verändern.
# FORM_MODIFIERS = {
#     "oil", "sauce", "paste", "puree", "juice", "extract", 
#     "butter", "flour", "liver", "heart", "stock", "broth", "vinegar", "soup"
# }
FORM_MODIFIERS = {
    # "sauce",  "puree", "juice", "extract", 
    # "butter", "flour", "liver", "heart", "stock", "broth",  "soup"
}

MANUAL_CORRECTIONS = {"leaves": "leaf", "leave": "leaf", "nuts": "nut", "yolks": "yolk"}

class SemanticGrouper:
    def __init__(self, all_ingredients_list):
        # Der Key ist jetzt ein Tuple: (Hauptzutat, Verarbeitungsform)
        # z.B. ('walnut', None) oder ('walnut', 'oil')
        self.groups = defaultdict(list)
        self._build_index(all_ingredients_list)
        
    def analyze_grammar(self, text):
        doc = nlp(text.lower())
        

    
        # Debugging: Schau mal, was spaCy denkt
        # print([(t.text, t.pos_, t.dep_, t.head.text) for t in doc])

        # STRATEGIE A: Nimm das letzte Wort, das ein Nomen ist.
        # Das funktioniert bei "Sugar Snap Peas" perfekt -> "peas"
        nouns = [t for t in doc if t.pos_ in ["NOUN", "PROPN"]]
        
        if nouns:
            head_token = nouns[-1] # Das letzte Nomen ist meist der Head/Kern
            found_form = MANUAL_CORRECTIONS.get(head_token.text, head_token.lemma_)
            nouns.remove(head_token)
        else:
            # Kein Nomen gefunden (z.B. nur Adjektive?) -> Nimm das letzte Token
            head_token = doc[-1]
            found_form = MANUAL_CORRECTIONS.get(head_token.text, head_token.lemma_)
        
        
        # 2. Modifiers sammeln (Die Kinder des Chefs)
        compounds = [] # Nomen, die den Typ bestimmen (Walnut -> Oil)

        
        for compound in nouns:
            if compound.dep_ == "compound":
                compounds.append(compound.lemma_)
        
        compounds.sort()
        entity_str = " ".join(compounds)
         
        if found_form in NOISE_WORDS:
            found_form = entity_str
        
        return (found_form, entity_str)
      
    def _build_index(self, ingredients):
        for raw_name in ingredients:
            key = self.analyze_grammar(raw_name)
            if key[0]: # Nur hinzufügen, wenn eine Substanz gefunden wurde
                self.groups[key].append(raw_name)

    def get_similar_ingredients(self, user_search):
        search_key = self.analyze_grammar(user_search)
        search_entity, search_form = search_key
        
        # print(f"DEBUG: Suche nach Substanz='{search_entity}' | Form='{search_form}'")
        
        # Logik: Exakter Match auf die Gruppe
        # Wer "Walnut Oil" sucht, kriegt nur die Gruppe ('walnut', 'oil')
        if search_key in self.groups:
            return self.groups[search_key]
        
        # FALLBACK (Optional):
        # Wenn User nur "Walnut" sucht (Form=None), 
        # wollen wir vielleicht NUR die reine Nuss, oder?
        # Ja -> return [] (Strict)
        
        return []


