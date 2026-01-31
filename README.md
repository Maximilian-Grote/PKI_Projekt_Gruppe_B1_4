[1. Features](#1-features)  
 [2. Ablauf (Kurzfassung)](#2-ablauf-kurzfassung)  
 [3. Ablaufdiagramm (Mermaid)](#3-ablaufdiagramm-mermaid)  
 [4. NLP/Ähnlichkeitslogik (Probleme \& Lösungen)](#4-nlpähnlichkeitslogik-probleme--lösungen)  
 [5. Rezeptempfehlungslogik (kurz)](#5-rezeptempfehlungslogik-kurz)  
 [6. Setup (kurz)](#6-setup-kurz)  
   - [6.1. Zusätzliche Requirements für Cache-Generierung](#61-zusätzliche-requirements-für-cache-generierung)  
 [7. Ausführen (Bash)](#7-ausführen-bash)  
 [8. Projektstruktur](#8-projektstruktur)  
 [9. API-Endpoints (Backend)](#9-api-endpoints-backend)  
 [10. TheMealDB-API-Integration](#10-themealdb-api-integration)  
 [11. Beiträge](#11-beiträge)  
 [12. KI-Einsatz](#12-ki-einsatz)


# 1. Rezept-Empfehlungssystem

Ein webbasiertes Rezeptempfehlungssystem mit Zutatenwahl über eine benutzerfreundliche Oberfläche.


## 3. Features

✅ **Zutatenwahl-Interface**
- Alle Zutaten von TheMealDB laden
- Kachel-Layout mit Zutatenbildern
- Suchfeld mit Auto-Completion
- Gewählte Zutaten als Tags anzeigen

✅ **Rezept-Suche**
- Rezepte nach gewählten Zutaten suchen
- Rezeptkarten mit Bildern anzeigen
- Detailansicht mit Zutaten + Anleitung

✅ **TheMealDB-Integration**
- Kostenlose API ohne Authentifizierung
- Caching zur Rate-Limit-Vermeidung
- RESTful API-Wrapper

✅ **Ähnliche Rezepte empfehlen**
- Auf der Rezeptdetailseite werden ähnliche Rezepte vorgeschlagen
- Basierend auf Zutatenprofilen und TF-IDF-Ähnlichkeit
- Verbesserte Entdeckung neuer Rezepte

## 4. Ablauf (Kurzfassung)

1. **Start**: App lädt Zutatenliste aus TheMealDB.
2. **Zutatenwahl**: Nutzer wählt Zutaten über UI oder Suche.
3. **Dedup**: Ähnliche Zutaten werden zusammengeführt.
4. **Rezeptsuche**: Rezepte werden per Schnittmenge ermittelt.
5. **Detailansicht**: Zutaten + Anleitung; ähnliche Rezepte werden empfohlen.

## 2. NLP-basierte Ähnlichkeitsmatrix (Vorverarbeitung)

**Wichtig**: Die Zutaten-Ähnlichkeitslogik ist **keine Produktivlogik** im Flask-Server. Stattdessen wird sie als Vorverarbeitungsschritt ausgeführt:

**Problem:**
- Unterschiedliche Schreibweisen (z. B. "Basil", "Basil Leaves")
- Synonyme/Varianten verhindern Treffer in der Schnittmenge
- API liefert teils ähnliche Zutaten als separate Einträge

**Lösung:**
1. **Im Notebook** ([`createIndexForSimilarIngredients.ipynb`](rezept-empfehlungssystem/createIndexForSimilarIngredients.ipynb)): Eine Ähnlichkeitsmatrix wird separat berechnet
2. **NLP-Verfahren**: 
   - Semantische Ähnlichkeit (SentenceTransformer-Embeddings)
   - String-Ähnlichkeit (Levenshtein-Distanz)
   - Grammatikalische Analyse (spaCy Head-Noun-Extraction)
   - Normalisierung von Strings (Kleinschreibung + Akzente entfernen)
3. **Resultat**: JSON-Cache `ingredient_similarity_cache_*.json` mit Zuordnungen ähnlicher Zutaten
4. **Anwendung**: Die JSON-Datei wird vom Server geladen und zur Deduplication während der Rezeptsuche verwendet

Dieses Vorgehen ermöglicht schnelle Lookups ohne rechenintensive NLP-Operationen zur Laufzeit.

## 5. Ablaufdiagramm (Mermaid)

```mermaid
flowchart TD
  A[Startseite öffnen] --> B[Zutatenliste laden]
  B --> C[Zutaten wählen]
  C --> D[Ähnliche Zutaten deduplizieren]
  D --> E[Rezepte per Schnittmenge suchen]
  E --> F[Rezepte anzeigen]
  F --> G[Rezept-Detail öffnen]
  G --> H[Ähnliche Rezepte berechnen]
```

## 4. NLP/Ähnlichkeitslogik (Probleme & Lösungen)

**Probleme:**
- Unterschiedliche Schreibweisen (z. B. "Basil", "Basil Leaves")
- Synonyme/Varianten verhindern Treffer in der Schnittmenge
- API liefert teils ähnliche Zutaten als separate Einträge

**Lösungen im Projekt:**
- Ähnlichkeits-Cache für Zutaten (vorberechnet)
- Dedup-Logik, die ähnliche Zutaten in der Auswahl zusammenführt
- Normalisierung von Strings (klein + Akzente entfernen)

**Notebook:**
- Der Ähnlichkeitsindex wird im Notebook erstellt: [rezept-empfehlungssystem/createIndexForSimilarIngredients.ipynb](rezept-empfehlungssystem/createIndexForSimilarIngredients.ipynb)



## 5. Rezeptempfehlungslogik

**Ablauf:**
- Ausgangspunkt ist das aktuell geöffnete Rezept.
- Aus der Zutatenliste wird ein TF‑IDF‑Vektor gebildet.
- Alle anderen Rezepte werden ebenfalls als TF‑IDF‑Vektoren dargestellt.
- Vergleich per Ähnlichkeitsmaß (Kosinus‑Ähnlichkeit) mit dem Ausgangsrezept.
- Die Top‑Treffer mit der höchsten Ähnlichkeit werden als „ähnliche Rezepte“ angezeigt.

**Ergebnis:**
- Empfehlungen mit möglichst vielen gemeinsamen Zutaten bzw. ähnlichen Zutatenkombinationen, ohne zu strikte Filterung.

## 6. Setup (kurz)

```bash
python3.9 -m venv .venvRezept
source .venvRezept/Scripts/activate
pip install -r requirements.txt
```

**Hinweis zu Abhängigkeiten:**

- Für den normalen Produktivbetrieb (Web-App, Rezepte suchen, Zutatenwahl etc.) reicht die Installation von `requirements.txt`.
- **Für die Erstellung oder Aktualisierung des Zutaten-Ähnlichkeits-Cache (JSON) via Notebook `createIndexForSimilarIngredients.ipynb` gibt es eine separate requirements-Datei:**
  - `requirements-nlp-cache.txt` (enthält alle nötigen NLP-Bibliotheken)

Diese Pakete sind **nicht** in der Standard-`requirements.txt` enthalten, da sie nur für die einmalige Generierung des Caches gebraucht werden.

### 6.1. Zusätzliche Requirements für Cache-Generierung

Falls der Zutaten-Ähnlichkeits-Cache (`ingredient_similarity_cache_*.json`) neu erstellt werden soll:

```bash
# (Im aktivierten venv)
pip install -r requirements-nlp-cache.txt
```

Danach kann das Notebook `createIndexForSimilarIngredients.ipynb` ausgeführt werden, um die JSON-Datei zu erzeugen.

Hinweis: Die spaCy-Modelle (`en_core_web_md`, `en_core_web_trf`) sind in `requirements-nlp-cache.txt` als direkte Wheels enthalten. Falls die Installation der Modelle fehlschlägt, kann man sie manuell nachinstallieren:

```bash
python -m spacy download en_core_web_md
python -m spacy download en_core_web_trf
```

Wenn nach der Installation die Meldung erscheint „You can now load the package via spacy.load('en_core_web_md')“, ist das **korrekt** – das Modell ist erfolgreich installiert und kann direkt in `spacy.load(...)` verwendet werden.

**Im Produktivbetrieb werden diese Pakete nicht benötigt!**

## 7. Ausführen (Bash)
## 7. Ausführen (Bash)

```bash
cd rezept-empfehlungssystem
python app.py
```
Die Anwendung läuft unter: `http://localhost:5000`


## 8. Projektstruktur
## 8. Projektstruktur

```
rezept-empfehlungssystem/
├── app.py                              # Flask-Anwendung
├── themealdb_client.py                 # TheMealDB-API-Wrapper
├── createIndexForSimilarIngredients.ipynb
├── ingredient_similarity_cache_*.json  # Ähnlichkeits-Cache
├── templates/
│   ├── index.html
│   ├── recipes.html
│   └── recipe_detail.html
└── static/
    ├── ingredients-search.js
    └── style.css
```

## 9. API-Endpoints (Backend)
## 9. API-Endpoints (Backend)

| Endpoint | Methode | Beschreibung |
|----------|---------|-------------|
| `/` | GET | Startseite (Zutatenwahl) |
| `/recipes` | GET | Rezepte-Ergebnisseite |
| `/recipe/<meal_id>` | GET | Detailseite für ein Rezept |

## 10. TheMealDB-API-Integration
## 10. TheMealDB-API-Integration

- **Quelle**: https://www.themealdb.com/api.php
- **Endpoints genutzt**:
  - `GET /list.php?i=list` – alle Zutaten
  - `GET /filter.php?i={ingredient}` – Rezepte nach Zutat
  - `GET /lookup.php?i={meal_id}` – Rezept-Details
- **Zutatenbilder**: `https://www.themealdb.com/images/ingredients/{name}.png`

## 11. Beiträge
## 11. Beiträge

**Grundgerüst:**
- Gemeinsam mit KI-Unterstützung erstellt

**Maximilian Grote:**
- Zutaten-Normalisierung mit NLP
- Erweiterung `TheMealDBClient` (z. B. `search_recipes_by_ingredient`)
- Ähnlichkeits-Cache-Integration

**Julien Maximilian Wache:**
- Rezept-Detail-Funktion (`get_recipe_details`)
  - Rezept-Anzeige (Frontend + Backend)(`score_ingredient`)
- Empfehlungslogik basierend auf ausgewähltem Rezept (TF-IDF) (`recommend_similar_recipes`)


## 12. KI-Einsatz
## 12. KI-Einsatz

Für Teile der Ideenfindung, Code-Überarbeitung und Dokumentation wurde KI-Unterstützung verwendet (z. B. Textentwürfe, Strukturvorschläge, Refactoring-Ideen, README-Erstellung).
