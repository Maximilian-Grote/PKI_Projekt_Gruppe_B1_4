"""
TheMealDB API Client - Wrapper für API-Aufrufe
Dokumentation: https://www.themealdb.com/api.php
"""
import requests
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

BASE_URL = "https://www.themealdb.com/api/json/v1/1"


class TheMealDBClient:
    """Client für TheMealDB API mit Caching-Support"""

    def __init__(self):
        self.session = requests.Session()
        self._ingredients_cache = None

    def get_all_ingredients(self) -> List[Dict]:
        """
        Alle verfügbaren Zutaten laden
        Cached nach erstem Aufruf
        
        Returns:
            Liste mit Zutaten: [{"idIngredient": "1", "strIngredient": "Chicken", ...}]
        """
        if self._ingredients_cache:
            return self._ingredients_cache

        try:
            response = self.session.get(f"{BASE_URL}/list.php?i=list")
            response.raise_for_status()
            data = response.json()
            self._ingredients_cache = data.get("meals", [])
            logger.info(f"Loaded {len(self._ingredients_cache)} ingredients from TheMealDB")
            return self._ingredients_cache
        except requests.RequestException as e:
            logger.error(f"Error loading ingredients: {e}")
            return []

    def search_recipes_by_ingredient(self, ingredient: str) -> List[Dict]:
        """
        Rezepte nach Zutat suchen
        
        Args:
            ingredient: Zutatenname (z.B. "Chicken")
            
        Returns:
            Liste mit Rezepten: [{"idMeal": "52806", "strMeal": "...", "strMealThumb": "..."}]
        """
        try:
            response = self.session.get(f"{BASE_URL}/filter.php?i={ingredient}")
            response.raise_for_status()
            data = response.json()
            recipes = data.get("meals", [])
            logger.info(f"Found {len(recipes)} recipes for ingredient: {ingredient}")
            return recipes
        except requests.RequestException as e:
            logger.error(f"Error searching recipes for {ingredient}: {e}")
            return []
        
    def search_recipes_by_ingredients(self, ingredients: List) -> List[Dict]:
        """
        Rezepte nach Zutaten suchen
        
        Args:
            ingredients: Zutatenname (z.B. ["chicken","Basmati Rice", ...])
            
        Returns:
            Liste mit Rezepten: [{"idMeal": "52806", "strMeal": "...", "strMealThumb": "..."}]
        """
        try:
            response = self.session.get(f"{BASE_URL}/filter.php?i={ingredients.join(',')}")
            response.raise_for_status()
            data = response.json()
            recipes = data.get("meals", [])
            logger.info(f"Found {len(recipes)} recipes for ingredients: {ingredients}")
            return recipes
        except requests.RequestException as e:
            logger.error(f"Error searching recipes for {ingredients}: {e}")
            return []

    def get_recipe_details(self, meal_id: str) -> Optional[Dict]:
        """
        Details eines Rezepts laden (Zutaten, Anleitung, etc.)
        
        Args:
            meal_id: ID des Rezepts
            
        Returns:
            Rezept-Details oder None bei Fehler
        """
        try:
            response = self.session.get(f"{BASE_URL}/lookup.php?i={meal_id}")
            response.raise_for_status()
            data = response.json()
            meals = data.get("meals", [])
            if meals:
                return meals[0]
            return None
        except requests.RequestException as e:
            logger.error(f"Error loading recipe details for {meal_id}: {e}")
            return None

    def get_ingredient_image_url(self, ingredient_name: str) -> str:
        """
        Bild-URL für eine Zutat
        
        Args:
            ingredient_name: Name der Zutat
            
        Returns:
            URL zum Zutatenbild
        """
        return f"https://www.themealdb.com/images/ingredients/{ingredient_name}.png"
