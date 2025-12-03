"""
Flask-Anwendung - Haupteinstiegspunkt
"""
from flask import Flask, render_template, request, jsonify
from themealdb_client import TheMealDBClient
import logging

# Logging konfigurieren
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
    return render_template("index.html")


@app.route("/api/ingredients")
def get_ingredients():
    """API: Alle verfügbaren Zutaten"""
    return jsonify(ALL_INGREDIENTS)


@app.route("/api/recipes")
def get_recipes():
    """
    API: Rezepte für gewählte Zutaten suchen
    Query-Parameter: ingredients (komma-separiert)
    Beispiel: /api/recipes?ingredients=Chicken,Garlic
    """
    ingredients_param = request.args.get("ingredients", "").strip()
    
    if not ingredients_param:
        return jsonify({"error": "No ingredients provided"}), 400
    
    # Zutaten splitten
    ingredients = [i.strip() for i in ingredients_param.split(",")]
    
    # Rezepte für jede Zutat suchen
    all_recipes = {}
    for ingredient in ingredients:
        if ingredient:
            recipes = client.search_recipes_by_ingredient(ingredient)
            for recipe in recipes:
                meal_id = recipe.get("idMeal")
                if meal_id not in all_recipes:
                    all_recipes[meal_id] = recipe
    
    # In Liste konvertieren und sortieren
    recipes_list = list(all_recipes.values())
    logger.info(f"Found {len(recipes_list)} recipes for ingredients: {ingredients}")
    
    return jsonify(recipes_list)


@app.route("/api/recipe/<meal_id>")
def get_recipe_details(meal_id):
    """API: Details eines Rezepts"""
    recipe = client.get_recipe_details(meal_id)
    
    if not recipe:
        return jsonify({"error": f"Recipe with ID {meal_id} not found"}), 404
    
    return jsonify(recipe)


@app.route("/recipes")
def recipes_page():
    """Rezepte-Ergebnisseite"""
    return render_template("recipes.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
