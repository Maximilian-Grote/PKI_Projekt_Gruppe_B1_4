/**
 * Zutatenwahl-Interface (index.html)
 */

let allIngredients = [];
let selectedIngredients = new Set();

// Beim Laden: Zutaten fetchen
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Loading ingredients...');
    await loadIngredients();
    setupEventListeners();
});

/**
 * Alle Zutaten von der API laden
 */
async function loadIngredients() {
    try {
        const response = await fetch('/api/ingredients');
        const data = await response.json();
        allIngredients = data;
        
        console.log(`Loaded ${allIngredients.length} ingredients`);
        renderIngredients();
    } catch (error) {
        console.error('Error loading ingredients:', error);
        document.getElementById('ingredientGrid').innerHTML = 
            '<p class="error">Fehler beim Laden der Zutaten. Bitte später erneut versuchen.</p>';
    }
}

/**
 * Zutaten-Kacheln rendern
 */
function renderIngredients() {
    const grid = document.getElementById('ingredientGrid');
    
    if (allIngredients.length === 0) {
        grid.innerHTML = '<p class="error">Keine Zutaten verfügbar.</p>';
        return;
    }

    grid.innerHTML = allIngredients.map(ingredient => {
        const name = ingredient.strIngredient;
        const imageUrl = `https://www.themealdb.com/images/ingredients/${name}.png`;
        
        return `
            <div class="ingredient-card" data-ingredient="${name}">
                <img src="${imageUrl}" alt="${name}" onerror="this.src='/static/placeholder.png'">
                <p>${name}</p>
            </div>
        `;
    }).join('');

    // Click-Handler für Kacheln
    grid.querySelectorAll('.ingredient-card').forEach(card => {
        card.addEventListener('click', () => toggleIngredient(card));
    });
}

/**
 * Zutat togglen (hinzufügen/entfernen)
 */
function toggleIngredient(card) {
    const ingredient = card.dataset.ingredient;
    
    if (selectedIngredients.has(ingredient)) {
        selectedIngredients.delete(ingredient);
        card.classList.remove('selected');
    } else {
        selectedIngredients.add(ingredient);
        card.classList.add('selected');
    }
    
    updateUI();
}

/**
 * UI aktualisieren (Tags + Button)
 */
function updateUI() {
    // Tags rendern
    const tagsContainer = document.getElementById('selectedTags');
    if (selectedIngredients.size === 0) {
        tagsContainer.innerHTML = '<p class="empty-state">Noch keine Zutaten gewählt</p>';
    } else {
        tagsContainer.innerHTML = Array.from(selectedIngredients)
            .map(ingredient => `
                <span class="tag">
                    ${ingredient}
                    <button class="tag-remove" onclick="removeIngredient('${ingredient}')">×</button>
                </span>
            `).join('');
    }

    // Such-Button aktualisieren
    const searchBtn = document.getElementById('searchBtn');
    searchBtn.disabled = selectedIngredients.size === 0;
    searchBtn.textContent = `Rezepte suchen (${selectedIngredients.size} Zutaten)`;
}

/**
 * Zutat entfernen
 */
function removeIngredient(ingredient) {
    selectedIngredients.delete(ingredient);
    
    // Karte deselektieren
    document.querySelector(`[data-ingredient="${ingredient}"]`)?.classList.remove('selected');
    
    updateUI();
}

/**
 * Event-Listener registrieren
 */
function setupEventListeners() {
    // Suchfeld
    const searchInput = document.getElementById('ingredientSearch');
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        showSuggestions(query);
    });

    // Such-Button
    document.getElementById('searchBtn').addEventListener('click', () => {
        if (selectedIngredients.size > 0) {
            // Zu Rezepte-Seite navigieren
            const ingredientsList = Array.from(selectedIngredients).join(',');
            window.location.href = `/recipes?ingredients=${encodeURIComponent(ingredientsList)}`;
        }
    });
}

/**
 * Such-Vorschläge anzeigen
 */
function showSuggestions(query) {
    const container = document.getElementById('searchSuggestions');
    
    if (query.length === 0) {
        container.innerHTML = '';
        return;
    }

    const matches = allIngredients
        .filter(ing => ing.strIngredient.toLowerCase().includes(query))
        .slice(0, 5);

    if (matches.length === 0) {
        container.innerHTML = '<p class="no-matches">Keine Treffer gefunden</p>';
        return;
    }

    container.innerHTML = matches.map(ing => `
        <div class="suggestion-item" onclick="selectFromSuggestion('${ing.strIngredient}')">
            ${ing.strIngredient}
        </div>
    `).join('');
}

/**
 * Zutat aus Vorschlag auswählen
 */
function selectFromSuggestion(ingredient) {
    if (!selectedIngredients.has(ingredient)) {
        selectedIngredients.add(ingredient);
        
        // Karte markieren
        const card = document.querySelector(`[data-ingredient="${ingredient}"]`);
        if (card) {
            card.classList.add('selected');
        }
    }
    
    // Suchfeld leeren
    document.getElementById('ingredientSearch').value = '';
    document.getElementById('searchSuggestions').innerHTML = '';
    
    updateUI();
}
