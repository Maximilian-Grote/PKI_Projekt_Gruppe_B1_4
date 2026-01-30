"""
Flask-Anwendung - Haupteinstiegspunkt
"""
from flask import Flask, render_template, request, abort, jsonify
from themealdb_client import TheMealDBClient
import logging
import difflib
import unicodedata
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
client = TheMealDBClient()

# Globale Zutaten (beim Start laden)
ALL_INGREDIENTS = []
ALL_SIMILAR_INGREDIENTS = {}


def _normalize(text: str) -> str:
    """Kleinbuchstaben + Akzente entfernen."""
    text = (text or "").strip().lower()
    return "".join(
        ch for ch in unicodedata.normalize("NFD", text) if unicodedata.category(ch) != "Mn"
    )


def score_ingredient(query: str, candidate: str) -> float:
    """Fuzzy-Score zwischen 0 und 1 mit Bonus für Präfix/Substring."""
    q = _normalize(query)
    c = _normalize(candidate)
    if not q or not c:
        return 0.0

    base = difflib.SequenceMatcher(None, q, c).ratio()
    bonus = 0.1 if c.startswith(q) else (0.05 if q in c else 0.0)
    score = max(0.0, min(1.0, base + bonus))
    return score


def _ingredient_text(recipe_detail: dict) -> str:
    """Extrahiert Zutaten + Mengen als Textrepräsentation für TF-IDF."""
    parts = []
    for i in range(1, 21):
        ingredient = recipe_detail.get(f"strIngredient{i}")
        measure = recipe_detail.get(f"strMeasure{i}")
        if ingredient and ingredient.strip():
            token = ingredient.strip()
            if measure and measure.strip():
                token = f"{token} {measure.strip()}"
            parts.append(token)

    instructions = recipe_detail.get("strInstructions", "") or ""
    return " ".join(parts + [instructions])


def recommend_similar_recipes(target_detail: dict, candidate_recipes: list, top_n: int = 4) -> list:
    """Berechnet ähnliche Rezepte zur Detailansicht per TF-IDF."""
    if not target_detail or not candidate_recipes:
        return []

    target_id = target_detail.get("idMeal")
    enriched = []

    target_text = _ingredient_text(target_detail)
    if target_text.strip():
        enriched.append({"recipe": target_detail, "text": target_text})

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

    if len(enriched) < 2:
        return []

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(entry["text"] for entry in enriched)
    similarity = cosine_similarity(matrix)

    anchor_index = 0  # erstes Element ist das aktuelle Rezept
    scored = []
    for idx, score in enumerate(similarity[anchor_index]):
        if idx == anchor_index:
            continue
        scored.append((idx, float(score)))

    scored.sort(key=lambda item: item[1], reverse=True)
    return [enriched[idx]["recipe"] for idx, _ in scored[:top_n]]


@app.before_request
def init_ingredients():
    """Zutaten beim ersten Request laden"""
    global ALL_INGREDIENTS
    global ALL_SIMILAR_INGREDIENTS
    if not ALL_INGREDIENTS:
        ALL_INGREDIENTS = client.get_all_ingredients()
    if not ALL_SIMILAR_INGREDIENTS:
        ALL_SIMILAR_INGREDIENTS = client.load_similarity_cache()


@app.route("/")
def index():
    """Startseite - Zutatenwahl"""
    # Zutaten aus Query-Parametern auslesen (von Rezepte-Seite zurückgekommen)
    selected_ingredients = request.args.getlist("ingredients")
    
    return render_template(
        "index.html", 
        ingredients=ALL_INGREDIENTS,
        selected_ingredients=selected_ingredients
    )


@app.route("/ingredient_suggestions")
def ingredient_suggestions():
    """JSON-Vorschläge für Zutaten (fuzzy, absteigend nach Score)."""
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])

    scored = []
    for item in ALL_INGREDIENTS:
        name = item.get("strIngredient", "")
        score = score_ingredient(query, name)
        if score > 0.5:
            scored.append(
                {
                    "name": name,
                    "image_url": item.get("image_url"),
                    "score": score,
                }
            )

    top = sorted(scored, key=lambda x: x["score"], reverse=True)[:8]
    for entry in top:
        entry.pop("score", None)

    return jsonify(top)


def _deduplicate_similar_ingredients(ingredients: list) -> list:
    """
    Entfernt ähnliche/doppelte Zutaten aus der Liste basierend auf ALL_SIMILAR_INGREDIENTS.
    Die Hauptzutat (erste in der Gruppe) bleibt, ähnliche werden entfernt.
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
                similar_ingredient = similar_entry[0] if isinstance(similar_entry, (list, tuple)) else similar_entry
                if similar_ingredient in deduplicated and similar_ingredient != ingredient:
                    to_remove.add(similar_ingredient)
    
    logger.debug(f"Removed similar ingredients: {to_remove}, from input: {ingredients}")
    return [ing for ing in deduplicated if ing not in to_remove]


def get_recipes_for_ingredients(ingredients: list) -> list:
    """Suche Rezepte, die alle angegebenen Zutaten enthalten (Schnittmenge)."""
    if not ingredients:
        return []

    # Ähnliche Zutaten deduplizieren da sie sonst doppelt in die Suche eingehen und nicht beides in einem Rezept vorkommen kann
    ingredients = _deduplicate_similar_ingredients(ingredients)

    recipes_by_id = {}
    intersect_ids = None  # Wird mit der Schnittmenge der Meal-IDs gefüllt

    for ingredient in ingredients:
        recipes = client.search_recipes_by_ingredient(ingredient) or []
        current_ids = set()

        for recipe in recipes:
            meal_id = recipe.get("idMeal")
            if meal_id:
                current_ids.add(meal_id)
                recipes_by_id.setdefault(meal_id, recipe)

        if intersect_ids is None:
            intersect_ids = current_ids
        else:
            intersect_ids &= current_ids

        if not intersect_ids:
            break

    return [recipes_by_id[mid] for mid in intersect_ids] if intersect_ids else []


@app.route("/recipes")
def recipes_page():
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
    recipe = client.get_recipe_details(meal_id)
    if not recipe:
        abort(404)

    selected_ingredients = request.args.getlist("ingredients")
    ingredient_basis = selected_ingredients
    if not ingredient_basis:
        derived = [recipe.get(f"strIngredient{i}") for i in range(1, 21)]
        ingredient_basis = [ing for ing in derived if ing and ing.strip()]
        ingredient_basis = ingredient_basis[:3]  # begrenze auf erste Zutaten für Suche

    candidates = []
    if ingredient_basis:
        candidates = get_recipes_for_ingredients(ingredient_basis) or []
        if not candidates and ingredient_basis:
            candidates = client.search_recipes_by_ingredient(ingredient_basis[0]) or []

    recommended = recommend_similar_recipes(recipe, candidates)

    return render_template(
        "recipe_detail.html",
        recipe=recipe,
        selected_ingredients=selected_ingredients,
        recommended_recipes=recommended,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
