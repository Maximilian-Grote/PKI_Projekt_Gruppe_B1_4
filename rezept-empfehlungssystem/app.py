"""
Flask-Anwendung - Haupteinstiegspunkt
Rezept-Empfehlungssystem mit Zutatenwahl und Fuzzy-Matching
"""
from flask import Flask, render_template, request, abort, jsonify
from themealdb_client import TheMealDBClient
import logging
import difflib
import unicodedata
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ============================================================================
# SETUP
# ============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
client = TheMealDBClient()

# Globale Zutaten (beim Start laden)
ALL_INGREDIENTS = []
ALL_SIMILAR_INGREDIENTS = {}


# ============================================================================
# HILFSFUNKTIONEN: Text-Normalisierung & Fuzzy-Matching
# ============================================================================

def _normalize(text: str) -> str:
    """
    Normalisiert Text für Vergleich:
    - Kleinbuchstaben
    - Akzente entfernen (ä → a)
    
    Args:
        text: Zu normalisierender Text
        
    Returns:
        Normalisierter Text
    """
    text = (text or "").strip().lower()
    return "".join(
        ch for ch in unicodedata.normalize("NFD", text)
        if unicodedata.category(ch) != "Mn"
    )


def score_ingredient(query: str, candidate: str) -> float:
    """
    Berechnet Fuzzy-Match-Score zwischen Query und Kandidat (0.0 - 1.0).
    Bonus-Punkte für Präfix-Match oder Substring-Match.
    
    Args:
        query: Benutzereingabe
        candidate: Zutatename zum Vergleichen
        
    Returns:
        Score zwischen 0.0 und 1.0
    """
    q = _normalize(query)
    c = _normalize(candidate)
    
    if not q or not c:
        return 0.0

    # SequenceMatcher für Basis-Ähnlichkeit
    base = difflib.SequenceMatcher(None, q, c).ratio()
    
    # Bonuspunkte für Präfix/Substring
    bonus = 0.1 if c.startswith(q) else (0.05 if q in c else 0.0)
    
    score = max(0.0, min(1.0, base + bonus))
    return score


# ============================================================================
# HILFSFUNKTIONEN: Rezept-Verarbeitung & Ähnlichkeit
# ============================================================================

def _ingredient_text(recipe_detail: dict) -> str:
    """
    Extrahiert Zutaten + Mengen + Anleitung als Text für TF-IDF-Vergleich.
    
    Args:
        recipe_detail: Rezept-Details (von API)
        
    Returns:
        Kombinierter Text aller Zutaten und Anleitung
    """
    parts = []
    
    # Zutaten und Mengen sammeln (max. 20)
    for i in range(1, 21):
        ingredient = recipe_detail.get(f"strIngredient{i}")
        measure = recipe_detail.get(f"strMeasure{i}")
        
        if ingredient and ingredient.strip():
            token = ingredient.strip()
            if measure and measure.strip():
                token = f"{token} {measure.strip()}"
            parts.append(token)

    # Anleitung hinzufügen
    instructions = recipe_detail.get("strInstructions", "") or ""
    
    return " ".join(parts + [instructions])


def recommend_similar_recipes(
    target_detail: dict,
    candidate_recipes: list,
    top_n: int = 4
) -> list:
    """
    Empfiehlt ähnliche Rezepte zur Detailansicht mittels TF-IDF + Cosine-Similarity.
    
    Args:
        target_detail: Aktuell angezeigtes Rezept
        candidate_recipes: Pool an Kandidaten
        top_n: Anzahl Empfehlungen
        
    Returns:
        Liste der ähnlichsten Rezepte (max. top_n)
    """
    if not target_detail or not candidate_recipes:
        return []

    target_id = target_detail.get("idMeal")
    enriched = []

    # Target-Rezept vorbereiten
    target_text = _ingredient_text(target_detail)
    if target_text.strip():
        enriched.append({"recipe": target_detail, "text": target_text})

    # Kandidaten anreichern (mit API-Daten)
    for recipe in candidate_recipes:
        meal_id = recipe.get("idMeal")
        if not meal_id or meal_id == target_id:
            continue

        details = client.get_recipe_details(meal_id)
        if not details:
            continue

        text_repr = _ingredient_text(details)
        if not text_repr.strip():
            continue

        enriched.append({"recipe": recipe, "text": text_repr})

    # Mindestens 2 Rezepte nötig für Vergleich
    if len(enriched) < 2:
        return []

    # TF-IDF + Cosine-Similarity
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(entry["text"] for entry in enriched)
    similarity = cosine_similarity(matrix)

    # Ähnlichkeit zum Target berechnen
    anchor_index = 0  # erstes Element = Target-Rezept
    scored = []
    for idx, score in enumerate(similarity[anchor_index]):
        if idx == anchor_index:
            continue
        scored.append((idx, float(score)))

    # Top-N auswählen
    scored.sort(key=lambda item: item[1], reverse=True)
    return [enriched[idx]["recipe"] for idx, _ in scored[:top_n]]


# ============================================================================
# HILFSFUNKTIONEN: Zutat-Deduplication & Rezeptsuche
# ============================================================================

def _deduplicate_similar_ingredients(ingredients: list) -> list:
    """
    Entfernt ähnliche/doppelte Zutaten aus der Liste.
    Nutzt ALL_SIMILAR_INGREDIENTS um Redundanz zu vermeiden.
    Die erste Zutat einer Ähnlichkeitsgruppe bleibt erhalten.
    
    Args:
        ingredients: Liste gewählter Zutaten
        
    Returns:
        Deduplizierte Liste
    """
    if not ingredients or not ALL_SIMILAR_INGREDIENTS:
        return ingredients

    deduplicated = ingredients.copy()
    to_remove = set()

    for ingredient in ingredients:
        if ingredient in to_remove:
            continue
            
        if ingredient in ALL_SIMILAR_INGREDIENTS:
            similar_list = ALL_SIMILAR_INGREDIENTS.get(ingredient, [])
            for similar_entry in similar_list:
                similar_ingredient = (
                    similar_entry[0]
                    if isinstance(similar_entry, (list, tuple))
                    else similar_entry
                )
                if similar_ingredient in deduplicated and similar_ingredient != ingredient:
                    to_remove.add(similar_ingredient)
    
    logger.debug(f"Removed similar ingredients: {to_remove}")
    return [ing for ing in deduplicated if ing not in to_remove]


def get_recipes_for_ingredients(ingredients: list) -> list:
    """
    Sucht Rezepte, die ALLE angegebenen Zutaten enthalten (Schnittmenge).
    
    Args:
        ingredients: Liste gewählter Zutaten
        
    Returns:
        Liste von Rezepten (mit allen Zutaten)
    """
    if not ingredients:
        return []

    # Ähnliche Zutaten entfernen
    ingredients = _deduplicate_similar_ingredients(ingredients)

    recipes_by_id = {}
    intersect_ids = None

    # Für jede Zutat Rezepte abrufen
    for ingredient in ingredients:
        recipes = client.search_recipes_by_ingredient(ingredient) or []
        current_ids = set()

        for recipe in recipes:
            meal_id = recipe.get("idMeal")
            if meal_id:
                current_ids.add(meal_id)
                recipes_by_id.setdefault(meal_id, recipe)

        # Schnittmenge berechnen
        if intersect_ids is None:
            intersect_ids = current_ids
        else:
            intersect_ids &= current_ids

        if not intersect_ids:
            break

    return [recipes_by_id[mid] for mid in intersect_ids] if intersect_ids else []


# ============================================================================
# REQUEST-HOOKS
# ============================================================================

@app.before_request
def init_ingredients():
    """Zutaten beim ersten Request laden (Caching)"""
    global ALL_INGREDIENTS
    global ALL_SIMILAR_INGREDIENTS
    
    if not ALL_INGREDIENTS:
        ALL_INGREDIENTS = client.get_all_ingredients()
    
    if not ALL_SIMILAR_INGREDIENTS:
        ALL_SIMILAR_INGREDIENTS = client.load_similarity_cache()


# ============================================================================
# ROUTES
# ============================================================================

@app.route("/")
def index():
    """
    Startseite - Zutatenwahl.
    Zeigt alle verfügbaren Zutaten als Kacheln an.
    """
    selected_ingredients = request.args.getlist("ingredients")
    
    return render_template(
        "index.html",
        ingredients=ALL_INGREDIENTS,
        selected_ingredients=selected_ingredients
    )


@app.route("/ingredient_suggestions")
def ingredient_suggestions():
    """
    JSON-API für Zutat-Vorschläge (Autocomplete).
    Nutzt Fuzzy-Matching mit Scoring.
    
    Query-Param:
        q: Benutzereingabe
        
    Returns:
        JSON-Liste mit Name + Bild-URL
    """
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])

    # Score für alle Zutaten berechnen
    scored = []
    for item in ALL_INGREDIENTS:
        name = item.get("strIngredient", "")
        score = score_ingredient(query, name)
        
        if score > 0.5:
            scored.append({
                "name": name,
                "image_url": item.get("image_url"),
                "score": score,
            })

    # Top 8 nach Score sortiert
    top = sorted(scored, key=lambda x: x["score"], reverse=True)[:8]
    for entry in top:
        entry.pop("score", None)

    return jsonify(top)


@app.route("/recipes")
def recipes_page():
    """
    Rezept-Übersicht für gewählte Zutaten.
    Zeigt alle Rezepte, die die gewählten Zutaten enthalten.
    
    Query-Param:
        ingredients: Gewählte Zutaten (mehrfach)
    """
    selected_ingredients = request.args.getlist("ingredients")

    if not selected_ingredients:
        return render_template(
            "recipes.html",
            recipes=[],
            selected_ingredients=[],
            error="Bitte wähle mindestens eine Zutat aus.",
        )

    recipes_list = get_recipes_for_ingredients(selected_ingredients)
    logger.info(
        f"Found {len(recipes_list)} recipes for ingredients: {selected_ingredients}"
    )

    return render_template(
        "recipes.html",
        recipes=recipes_list,
        selected_ingredients=selected_ingredients,
        error=None,
    )


@app.route("/recipe/<meal_id>")
def recipe_detail_page(meal_id):
    """
    Rezept-Detailseite mit Zutaten, Anleitung und ähnlichen Rezepten.
    
    URL-Param:
        meal_id: ID des Rezepts
        
    Query-Param:
        ingredients: Gewählte Zutaten (für Kontext)
    """
    recipe = client.get_recipe_details(meal_id)
    if not recipe:
        abort(404)

    selected_ingredients = request.args.getlist("ingredients")
    
    # Zutatenbasis für ähnliche Rezepte
    ingredient_basis = selected_ingredients
    if not ingredient_basis:
        # Fallback: erste 3 Zutaten aus aktuellem Rezept
        derived = [recipe.get(f"strIngredient{i}") for i in range(1, 21)]
        ingredient_basis = [ing for ing in derived if ing and ing.strip()][:3]

    # Kandidaten für ähnliche Rezepte
    candidates = []
    if ingredient_basis:
        candidates = get_recipes_for_ingredients(ingredient_basis) or []
        if not candidates and ingredient_basis:
            candidates = client.search_recipes_by_ingredient(ingredient_basis[0]) or []

    # Ähnliche Rezepte berechnen
    recommended = recommend_similar_recipes(recipe, candidates)

    return render_template(
        "recipe_detail.html",
        recipe=recipe,
        selected_ingredients=selected_ingredients,
        recommended_recipes=recommended,
    )


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    app.run(debug=True, port=5000)
