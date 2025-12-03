# Copilot Instructions: Rezept-Empfehlungssystem

## MVP: Zutatenwahl & Rezeptanzeige

### Projektübersicht
Webanwendung zur Rezeptsuche durch Zutatenauswahl. Kern-Feature: Benutzer wählt Zutaten via UI → Rezepte mit Bildern anzeigen.

### Stack
- **Backend**: Python (Flask)
- **Frontend**: HTML/CSS/JavaScript
- **Datenbeschaffung**: TheMealDB-API (kostenlos, keine Auth)
- **Datenverarbeitung**: pandas, requests
- **Lokalisierung**: Deutsch/Englisch

### Kritischer Datenfluss: Zutatenwahl

```
1. Zutaten-Kategorien laden (TheMealDB)
   ↓
2. Mit Bildern als Kacheln anzeigen
   ↓
3. User wählt Zutaten (Checkboxen/Buttons)
   ↓
4. Rezepte suchen (matching ingredients)
   ↓
5. Mit Bildern + Anleitung anzeigen
```

### UI-Komponenten (Priorität)

**Zutaten-Auswahl:**
- Kachel-Layout: Zutatenbilder von TheMealDB (URL: `https://www.themealdb.com/images/ingredients/{name}.png`)
- Suchfeld mit Auto-Komplettierung für Zutaten
- Gewählte Zutaten als Chips/Tags anzeigen
- Button: "Rezepte suchen"

**Rezept-Ergebnisse:**
- Rezept-Karte: Bild + Name + Kurzbeschreibung
- Klick → Detailseite mit Zutaten + Anleitung
- Keine Filterung initial; nur Matching

### Integration TheMealDB-API

**Key Endpoints:**
```
GET /api/ingredient/list.php → alle Zutaten
GET /api/filter.php?i={ingredient} → Rezepte mit Zutat
GET /api/lookup.php?i={meal_id} → Rezept-Details
```

### Backend-Struktur

```
app.py
├── routes.py (Endpoints für UI)
├── themealdb_client.py (API-Wrapper)
└── templates/
    ├── index.html (Zutatenwahl)
    └── recipes.html (Rezepte anzeigen)
```

### Konventionen für diese Phase

- **Einfach halten**: Keine NLP/KI initial—exaktes Matching reicht
- **Fehlertoleranz später**: Erst funktional, dann robust
- **Deutsch standardmäßig**: Sprachen-Toggle auf späteren Sprint
- **API-Caching**: TheMealDB-Antworten cachen, um Rate-Limits zu vermeiden
