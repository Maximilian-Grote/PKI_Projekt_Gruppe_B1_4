# Rezept-Empfehlungssystem - MVP

Ein webbasiertes Rezeptempfehlungssystem mit Zutatenwahl über eine benutzerfreundliche Oberfläche.

## Features

✅ **Zutatenwahl-Interface**
- Alle Zutaten von TheMealDB laden
- Kachel-Layout mit Zutatenbildern
- Suchfeld mit Auto-Komplettierung
- Gewählte Zutaten als Tags anzeigen

✅ **Rezept-Suche**
- Rezepte nach gewählten Zutaten suchen
- Rezeptkarten mit Bildern anzeigen
- Detailansicht mit Zutaten + Anleitung (Modal)

✅ **TheMealDB-Integration**
- Kostenlose API ohne Authentifizierung
- Caching zur Rate-Limit-Vermeidung
- RESTful API-Wrapper

## Setup

### 1. Installation

Um die benötigten Pakete in einer virtuellen Umgebung zu installieren, führe die folgenden Schritte aus:

1. Erstelle eine virtuelle Umgebung:
   ```bash
   python -m venv venv
   ```
2. Aktiviere die virtuelle Umgebung:
   - Für Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Für macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
3. Installiere die Abhängigkeiten:
   ```bash
   pip install -r requirements.txt
   ```

### 2. Starten

```bash
python app.py
```

Die Anwendung läuft unter: `http://localhost:5000`

## Projektstruktur

```
rezept-empfehlungssystem/
├── app.py                    # Flask-Anwendung (Haupteinstiegspunkt)
├── themealdb_client.py       # TheMealDB-API-Wrapper
├── requirements.txt          # Python-Dependencies
├── templates/
│   ├── index.html           # Zutatenwahl-Seite
│   └── recipes.html         # Rezept-Ergebnisseite
└── static/
    ├── app.js               # Zutatenwahl-Logik
    ├── recipes.js           # Rezept-Logik
    └── style.css            # Styling
```

## API-Endpoints

### Backend-API

| Endpoint | Methode | Beschreibung |
|----------|---------|-------------|
| `/` | GET | Startseite (Zutatenwahl) |
| `/api/ingredients` | GET | Alle verfügbaren Zutaten |
| `/api/recipes` | GET | Rezepte für Zutaten (Query: `?ingredients=Chicken,Garlic`) |
| `/api/recipe/<meal_id>` | GET | Details eines Rezepts |
| `/recipes` | GET | Rezepte-Ergebnisseite |

## TheMealDB-API-Integration

- **Quelle**: https://www.themealdb.com/api.php
- **Endpoints genutzt**:
  - `GET /list.php?i=list` – alle Zutaten
  - `GET /filter.php?i={ingredient}` – Rezepte nach Zutat
  - `GET /lookup.php?i={meal_id}` – Rezept-Details
- **Zutatenbilder**: `https://www.themealdb.com/images/ingredients/{name}.png`

## Workflow

1. **Benutzer startet Anwendung**
   - Frontend lädt alle Zutaten von `/api/ingredients`
   - Zutaten als Kacheln mit Bildern rendern

2. **Benutzer wählt Zutaten**
   - Klick auf Zutat togglet Auswahl
   - Ausgewählte Zutaten als Tags oben anzeigen
   - Such-Button aktiviert sich

3. **Benutzer klickt "Rezepte suchen"**
   - Navigation zu `/recipes?ingredients=Chicken,Garlic`
   - Frontend fetcht `/api/recipes?ingredients=Chicken,Garlic`

4. **Rezepte anzeigen**
   - Rezept-Karten mit Bildern rendern
   - Klick auf Rezept → Modal mit Details
   - Modal zeigt: Bild, Zutaten, Anleitungstext

## Entwickler-Hinweise

- **Einfach halten**: Kein NLP/KI in dieser Phase—exaktes Matching reicht
- **Caching**: TheMealDB-Antworten werden gecacht, um Rate-Limits zu vermeiden
- **Fehlerbehandlung**: Fehlerhafte Zutatenbilder zeigen Placeholder
- **Responsive Design**: Mobile & Desktop-kompatibel

## Nächste Schritte (Zukunft)

- [ ] NLP-Zutatenerkennung (spaCy/NLTK)
- [ ] Flexible Suche (1-2 fehlende Zutaten)
- [ ] Kategorien/Küchen-Filter
- [ ] Lokalisierung (Deutsch/Englisch)
- [ ] Content-based Empfehlungen (Scikit-learn)
- [ ] Maßeinheiten-Konvertierung

## Alte virtuelle Umgebung löschen

Um eine alte virtuelle Umgebung zu löschen, führe die folgenden Schritte aus:

1. Deaktiviere die virtuelle Umgebung, falls sie aktiv ist:
   ```bash
   deactivate
   ```
2. Lösche den Ordner der virtuellen Umgebung:
   ```bash
   rm -rf venv
   ```
   (Für Windows:
   ```bash
   rmdir /s /q venv
   ```
   )
3. Erstelle eine neue virtuelle Umgebung:
   ```bash
   python -m venv venv
   ```
