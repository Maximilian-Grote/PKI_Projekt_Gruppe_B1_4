"""
Flask-Anwendung - Haupteinstiegspunkt
"""
from flask import Flask, render_template, request, abort
from themealdb_client import TheMealDBClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
client = TheMealDBClient()

# Globale Zutaten (beim Start laden)
ALL_INGREDIENTS = []


@app.before_request
def init_ingredients():
    """Zutaten beim ersten Request laden"""
    global ALL_INGREDIENTS
    if not ALL_INGREDIENTS:
        ALL_INGREDIENTS = client.get_all_ingredients()


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


def get_recipes_for_ingredients(ingredients: list) -> list:
    """Suche Rezepte, die alle angegebenen Zutaten enthalten (Schnittmenge)."""
    if not ingredients:
        return []

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
    return render_template("recipe_detail.html", recipe=recipe, selected_ingredients=selected_ingredients)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
