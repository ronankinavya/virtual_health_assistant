
# Virtual Health Assistant (Educational Starter)

> **Important:** This project is for **education/demo only**. It does **not** provide medical advice and must not be used for diagnosis or treatment. Always consult a qualified clinician.

## What you get

- **Toy dataset** of symptoms → condition labels
- **Training script** to build a simple Logistic Regression model (scikit‑learn)
- **FastAPI backend** with:
  - Lightweight NLP (gazetteer) for symptom extraction
  - Triage rules for EMERGENCY / URGENT / ROUTINE\_SELF\_CARE
  - `/analyze` endpoint returning normalized symptoms, triage, and top condition probabilities
- **Minimal website** (HTML + JS) with optional **voice input** (Web Speech API)

## 1) Setup

```bash
# Create and activate a virtualenv (recommended)
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

## 2) Train the model (on the toy dataset)

```bash
python train_model.py
# This saves model.joblib and prints a small accuracy report
```

## 3) Run the API

```bash
uvicorn api:app --reload --port 8000
```

## 4) Open the website

Serve the `static/` folder so it can call your local API:

```bash
# Option A: use Python's built‑in static server (serves on http://localhost:8001)
python -m http.server 8001 --directory static

# Then open http://localhost:8001 in your browser.
# The page will POST to your API at http://localhost:8000/analyze
```

> If hosting behind one server, you can also serve `static/` from FastAPI or proxy the API under the same origin.

## Design notes

- **NLP**: We use a small ontology of symptoms with synonyms and exact word‑boundary matching. In production, you’d replace this with a proper NER model (e.g., spaCy or a transformer) and a clinical terminology (e.g., SNOMED CT/HPO) with licensing.
- **Triage**: Simple rule engine based on red flags. Expand with clinician‑reviewed protocols and age/pregnancy/comorbidity modifiers.
- **Model**: Multinomial Logistic Regression over binary symptom features. Real systems use larger datasets, uncertainty handling, and safety‑first thresholds.
- **Safety**: App surfaces strong **EMERGENCY**/ **URGENT** messaging, never gives definitive diagnoses, and repeats the disclaimer.

## Folder structure

```
virtual_health_assistant_starter/
├─ api.py
├─ train_model.py
├─ requirements.txt
├─ data/
│  ├─ toy_symptom_dataset.csv
│  ├─ feature_order.json
│  ├─ symptom_ontology.json
│  └─ triage_rules.yaml
└─ static/
   ├─ index.html
   ├─ app.js
   └─ styles.css
```

## Next steps (suggested)

1. Replace toy dataset with a larger, clinically curated dataset; enforce data governance and bias checks.
2. Add a proper dialogue manager that asks targeted follow‑ups.
3. Internationalization (languages, local care numbers).
4. Add analytics, consent, and privacy controls; do **not** store PHI without compliance.
5. Security hardening (rate‑limit, auth if exposed publicly).

---

**License**: MIT — see `LICENSE`.
