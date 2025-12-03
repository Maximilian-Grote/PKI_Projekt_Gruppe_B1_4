/**
 * Rezepte-Ansicht (recipes.html)
 */

let selectedIngredientsForRecipes = [];
let allRecipes = [];

document.addEventListener('DOMContentLoaded', async () => {
    // Zutaten aus URL auslesen
    const params = new URLSearchParams(window.location.search);
    const ingredientsParam = params.get('ingredients');
    
    if (ingredientsParam) {
        selectedIngredientsForRecipes = ingredientsParam.split(',').map(i => i.trim());
        await loadRecipes();
    } else {
        document.getElementById('recipeGrid').innerHTML = 
            '<p class="error">Keine Zutaten gewählt.</p>';
    }
});

/**
 * Rezepte für gewählte Zutaten laden
 */
async function loadRecipes() {
    try {
        const ingredientsList = selectedIngredientsForRecipes.join(',');
        const response = await fetch(`/api/recipes?ingredients=${encodeURIComponent(ingredientsList)}`);
        
        if (!response.ok) throw new Error('API error');
        
        allRecipes = await response.json();
        console.log(`Found ${allRecipes.length} recipes`);
        
        renderRecipes();
        renderSelectedIngredients();
    } catch (error) {
        console.error('Error loading recipes:', error);
        document.getElementById('recipeGrid').innerHTML = 
            '<p class="error">Fehler beim Laden der Rezepte.</p>';
    }
}

/**
 * Rezept-Karten rendern
 */
function renderRecipes() {
    const grid = document.getElementById('recipeGrid');
    
    if (allRecipes.length === 0) {
        grid.innerHTML = '<p class="empty-state">Keine Rezepte gefunden. Versuche andere Zutaten.</p>';
        return;
    }

    grid.innerHTML = allRecipes.map(recipe => `
        <div class="recipe-card" onclick="showRecipeDetails('${recipe.idMeal}')">
            <img src="${recipe.strMealThumb}" alt="${recipe.strMeal}" class="recipe-image">
            <div class="recipe-info">
                <h3>${recipe.strMeal}</h3>
                <p class="recipe-id">ID: ${recipe.idMeal}</p>
            </div>
        </div>
    `).join('');
}

/**
 * Gewählte Zutaten anzeigen
 */
function renderSelectedIngredients() {
    const container = document.getElementById('selectedIngredientsInfo');
    container.innerHTML = selectedIngredientsForRecipes
        .map(ing => `<span class="tag">${ing}</span>`)
        .join('');
}

/**
 * Rezept-Details anzeigen (Modal)
 */
async function showRecipeDetails(mealId) {
    try {
        const response = await fetch(`/api/recipe/${mealId}`);
        if (!response.ok) throw new Error('Recipe not found');
        
        const recipe = await response.json();
        displayRecipeModal(recipe);
    } catch (error) {
        console.error('Error loading recipe details:', error);
        alert('Fehler beim Laden des Rezepts.');
    }
}

/**
 * Rezept-Details im Modal anzeigen
 */
function displayRecipeModal(recipe) {
    const modal = document.getElementById('detailsModal');
    const modalBody = document.getElementById('modalBody');

    // Zutaten und Maße zusammensammeln
    let ingredientsList = '<ul>';
    for (let i = 1; i <= 20; i++) {
        const ingredient = recipe[`strIngredient${i}`];
        const measure = recipe[`strMeasure${i}`];
        
        if (ingredient && ingredient.trim()) {
            ingredientsList += `<li>${ingredient} - ${measure}</li>`;
        }
    }
    ingredientsList += '</ul>';

    modalBody.innerHTML = `
        <div class="recipe-details">
            <img src="${recipe.strMealThumb}" alt="${recipe.strMeal}" class="recipe-detail-image">
            <h2>${recipe.strMeal}</h2>
            
            <h3>Zutaten:</h3>
            ${ingredientsList}
            
            <h3>Anleitung:</h3>
            <p>${recipe.strInstructions}</p>
            
            ${recipe.strSource ? `<p><a href="${recipe.strSource}" target="_blank">Weitere Informationen</a></p>` : ''}
        </div>
    `;

    modal.style.display = 'block';

    // Close-Button
    const closeBtn = document.querySelector('.close');
    closeBtn.onclick = () => {
        modal.style.display = 'none';
    };

    // Außerhalb klicken = schließen
    window.onclick = (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    };
}
