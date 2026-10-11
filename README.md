# Smart Plant & Garden Pathologist 🌱🔬

A local visual plant disease and nutrient distress diagnostic lab powered by **Moondream (1.8B VLM)** running on **Apple Silicon Metal**.

Identify plant species, diagnose foliar distress patterns (chlorosis, fungal leaf spots, necrotic lesions, spider mites), and receive immediate, actionable 3-step clinical remediation guides with recovery timelines.

---

## Key Features

- **Species & Health Classification:** Recognizes crops and houseplants (*Monstera*, *Citrus*, *Tomato*, *Rose*, *Ficus*, etc.) and evaluates overall vitality.
- **Foliar Distress Pathology:** Detects interveinal chlorosis, fungal spore lesions (Alternaria/Cercospora), tissue necrosis, and sap-feeding pest stippling.
- **Prioritized 3-Step Remediation:** Clear instructions covering pruning, organic biofungicides / neem oil treatments, and watering/soil pH adjustments.
- **Prognosis & Recovery Timeline:** Estimates healing timeframes and preventive measures.
- **Real Botanical Test Samples:** Includes 4 verified leaf photographs from Wikimedia Commons (Healthy Monstera, Citrus Iron Chlorosis, Fungal Leaf Spot, Tomato Spider Mites).
- **Minimal, Zero-Friction UI:** Drag-and-drop or click a verified sample for instant diagnosis (~800ms).

---

## Tech Stack & Architecture

- **Vision-Language Model:** `moondream` (1.8B VLM, ~1.7 GB on disk, ~2.2 GB unified RAM)
- **Backend:** FastAPI, Pydantic, Pillow, HTTPX
- **Frontend:** Responsive Tailwind CSS UI with live preview and severity indicators
- **Inference Server:** Local Ollama on Apple Silicon Metal GPU

---

## Quick Start

### 1. Prerequisites
Ensure Ollama is running and has the `moondream` model available:
```bash
ollama list
# moondream should be present
```

### 2. Setup Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run Automated Tests
```bash
python sample_test.py
```

### 4. Start Web Application
```bash
uvicorn app:app --reload --port 8800
```
Open **`http://localhost:8800`** in your browser.
