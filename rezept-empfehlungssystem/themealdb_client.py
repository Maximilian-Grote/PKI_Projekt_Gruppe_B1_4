"""
TheMealDB API Client - Wrapper für API-Aufrufe
Dokumentation: https://www.themealdb.com/api.php
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://www.themealdb.com/api/json/v1/1"
SIMILARITY_CACHE_PATH = "ingredient_similarity_cache_30-01-2026-15-48_max.json"


class TheMealDBClient:
    """Client für TheMealDB API mit Caching-Support"""

    def __init__(self):
        self.session = requests.Session()
        self._ingredients_cache = None
        self._recipe_details_cache = {}
        self._similarity_cache = None

    def load_similarity_cache(self) -> Dict:
        """Lädt die global definierte JSON-Datei und gibt ein Dict zurück."""
        if self._similarity_cache is not None:
            return self._similarity_cache

        try:
            file_path = Path(__file__).resolve().parent / SIMILARITY_CACHE_PATH
            with file_path.open("r", encoding="utf-8") as file:
                self._similarity_cache = json.load(file)
            logger.info("Loaded similarity cache from %s", file_path)
            return self._similarity_cache
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Error loading similarity cache: %s", exc)
            return {}

    def get_all_ingredients(self) -> List[Dict]:
        """Alle verfügbaren Zutaten laden, angereichert mit Bild-URLs"""
        if self._ingredients_cache:
            return self._ingredients_cache

        try:
            response = self.session.get(f"{BASE_URL}/list.php?i=list")
            response.raise_for_status()
            data = response.json()
            ingredients = data.get("meals", [])

            for item in ingredients:
                name = item.get("strIngredient", "")
                item["image_url"] = item.get("strThumb", "")

            self._ingredients_cache = ingredients
            logger.info(f"Loaded {len(self._ingredients_cache)} ingredients from TheMealDB")
            return self._ingredients_cache
        except requests.RequestException as e:
            logger.error(f"Error loading ingredients: {e}")
            return []

    def get_ingredient_image_url(self, ingredient_name: str) -> str:
        """Bild-URL für eine Zutat"""
        safe_name = (ingredient_name or "").strip()
        return f"https://www.themealdb.com/images/ingredients/{safe_name}.png"

    def search_recipes_by_ingredient(self, ingredient: str) -> List[Dict]:
        """
        Rezepte nach Zutat suchen
        
        Args:
            ingredient: Zutatenname (z.B. "Chicken")
            
        Returns:
            Liste mit Rezepten: [{"idMeal": "52806", "strMeal": "...", "strMealThumb": "..."}]
        """
        try:
            recipes = []
            logger.info(f"1. Search input ingrident: {ingredient}")
            similar_ingredients = self._similarity_cache.get(ingredient, []) if self._similarity_cache else [ingredient]
            logger.info(f"2.Liste der ingredients: {similar_ingredients}")
            for ing,score in similar_ingredients:
                logger.info(f"Searching recipes for ingredient: {ing}")
                response = self.session.get(f"{BASE_URL}/filter.php?i={ing}")
                response.raise_for_status()
                data = response.json()
                recipes.extend(data.get("meals", []) or []) #fängt None ab
                logger.info(f"Found {len(recipes)} recipes for ingredient: {ing}")
            return recipes
        except requests.RequestException as e:
            logger.error(f"Error searching recipes for {ingredient}: {e}")
            return []

    def get_recipe_details(self, meal_id: str) -> Optional[Dict]:
        """
        Details eines Rezepts laden (Zutaten, Anleitung, etc.)
        
        Args:
            meal_id: ID des Rezepts
            
        Returns:
            Rezept-Details oder None bei Fehler
        """
        if meal_id in self._recipe_details_cache:
            return self._recipe_details_cache.get(meal_id)

        try:
            response = self.session.get(f"{BASE_URL}/lookup.php?i={meal_id}")
            response.raise_for_status()
            data = response.json()
            meals = data.get("meals", [])
            if meals:
                self._recipe_details_cache[meal_id] = meals[0]
                return meals[0]
            return None
        except requests.RequestException as e:
            logger.error(f"Error loading recipe details for {meal_id}: {e}")
            return None

