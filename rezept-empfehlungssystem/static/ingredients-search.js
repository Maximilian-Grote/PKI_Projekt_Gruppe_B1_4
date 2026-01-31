/**
 * Ingredient search with suggestions, checkbox handling, and tags
 */

document.addEventListener('DOMContentLoaded', function () {
    const checkboxes = Array.from(document.querySelectorAll('input[name="ingredients"]'));
    const tagsContainer = document.getElementById('selectedTags');
    const searchBtn = document.getElementById('searchBtn');
    const searchInput = document.getElementById('ingredientSearch');
    const suggestions = document.getElementById('searchSuggestions');

    const checkboxByName = new Map();
    checkboxes.forEach(cb => checkboxByName.set(cb.value.toLowerCase(), cb));

    let suggestionAborter = null;

    function renderSelection() {
        const selected = checkboxes.filter(cb => cb.checked).map(cb => cb.value);

        if (selected.length === 0) {
            tagsContainer.innerHTML = '<p class="empty-state">No ingredients selected yet</p>';
            searchBtn.disabled = true;
            searchBtn.textContent = 'Search recipes';
            return;
        }

        tagsContainer.innerHTML = selected
            .map(name => {
                const ingredient = ingredientNames.find(i => i.strIngredient === name);
                const imageUrl = ingredient?.image_url || 'https://www.themealdb.com/images/ingredients/' + name + '.png';
                return '<span class="tag">' +
                    '<img src="' + imageUrl + '" alt="' + name + '" class="tag-image" onerror="this.src=' + "'" + "{{ url_for('static', filename='placeholder.svg') }}" + "'" + '">' +
                    '<span class="tag-text">' + name + '</span>' +
                    '<button type="button" class="tag-remove" data-ingredient="' + name + '" aria-label="Remove ' + name + '">×</button>' +
                    '</span>';
            })
            .join('');

        searchBtn.disabled = false;
        searchBtn.textContent = 'Search recipes (' + selected.length + ')';

        // Event-Listener für Remove-Buttons hinzufügen
        tagsContainer.querySelectorAll('.tag-remove').forEach(btn => {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                const ingredient = this.dataset.ingredient;
                const cb = checkboxByName.get(ingredient.toLowerCase());
                if (cb) {
                    cb.checked = false;
                    renderSelection();
                }
            });
        });
    }

    function clearSuggestions() {
        suggestions.innerHTML = '';
        suggestions.style.display = 'none';
    }

    async function renderSuggestions(query) {
        const q = query.trim();
        if (!q) {
            clearSuggestions();
            return;
        }

        if (suggestionAborter) {
            suggestionAborter.abort();
        }
        suggestionAborter = new AbortController();

        let matches = [];
        try {
            const res = await fetch('/ingredient_suggestions?q=' + encodeURIComponent(q), {
                signal: suggestionAborter.signal
            });
            if (res.ok) {
                matches = await res.json();
            }
        } catch (err) {
            if (err.name === 'AbortError') return;
        }

        if (!matches || matches.length === 0) {
            suggestions.innerHTML = '<div class="suggestion-item no-matches">No matches</div>';
            suggestions.style.display = 'block';
            return;
        }

        suggestions.innerHTML = matches
            .map(item => {
                const name = item.name;
                const imageUrl = item.image_url || 'https://www.themealdb.com/images/ingredients/' + name + '.png';
                return '<div class="suggestion-item" data-name="' + name + '">' +
                    '<img src="' + imageUrl + '" alt="' + name + '" class="suggestion-image" onerror="this.src=' + "'" + "{{ url_for('static', filename='placeholder.svg') }}" + "'" + '">' +
                    '<span>' + name + '</span>' +
                    '</div>';
            })
            .join('');
        suggestions.style.display = 'block';
    }

    suggestions.addEventListener('click', function (e) {
        const item = e.target.closest('.suggestion-item');
        if (!item || item.classList.contains('no-matches')) return;

        const name = item.dataset.name;
        const cb = checkboxByName.get(name.toLowerCase());
        if (cb) {
            cb.checked = true;
            renderSelection();
        }

        searchInput.value = '';
        clearSuggestions();
    });

    document.addEventListener('click', function (e) {
        if (!suggestions.contains(e.target) && e.target !== searchInput) {
            clearSuggestions();
        }
    });

    // Clear all button
    const clearAllBtn = document.getElementById('clearAllBtn');
    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', function (e) {
            e.preventDefault();
            checkboxes.forEach(cb => cb.checked = false);
            renderSelection();
        });
    }

    searchInput.addEventListener('input', function (e) {
        renderSuggestions(e.target.value);
    });

    checkboxes.forEach(cb => cb.addEventListener('change', renderSelection));
    renderSelection();
});
