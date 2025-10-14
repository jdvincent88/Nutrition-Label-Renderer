# Nutrition-Label-Renderer
Renders a label for a Nutrition label to FDA standards
# Nutrition Label Renderer (Ready-to-Deploy)

Deterministic renderer for FDA-style Nutrition Facts labels. Produces print-ready PNGs at 300–600 DPI.

## Local
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export API_KEY=$(openssl rand -hex 32)
uvicorn main:app --reload
# http://127.0.0.1:8000/docs

## Deploy on Render
Push to GitHub → New+ → Blueprint → select repo (uses render.yaml) → set API_KEY → Deploy.

## Endpoint
POST /render/nutrition  → returns { mime_type, image_base64 }
