# main.py
from fastapi import FastAPI, Header, HTTPException, Response, Request
from pydantic import BaseModel
from typing import Optional
import base64, os, re
import cairosvg

app = FastAPI(title="Nutrition Label Renderer", version="3.0.0")

API_KEY = os.environ.get("API_KEY")

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class Nutrients(BaseModel):
    CALORIES: float
    TOTAL_FAT_AMT: str
    TOTAL_FAT_DV: str
    SAT_FAT_AMT: str
    SAT_FAT_DV: str
    TRANS_FAT_AMT: str
    TRANS_FAT_DV: str
    CHOLESTEROL_AMT: str
    CHOLESTEROL_DV: str
    SODIUM_AMT: str
    SODIUM_DV: str
    CARBS_AMT: str
    CARBS_DV: str
    FIBER_AMT: str
    FIBER_DV: str
    SUGARS_AMT: str
    SUGARS_DV: str
    ADD_SUG_AMT: str
    ADD_SUG_DV: str
    PROTEIN_AMT: str
    PROTEIN_DV: str
    VITD_AMT: str
    VITD_DV: str
    CALCIUM_AMT: str
    CALCIUM_DV: str
    IRON_AMT: str
    IRON_DV: str
    POTASSIUM_AMT: str
    POTASSIUM_DV: str
    VITC_AMT: Optional[str] = ""
    VITC_DV: Optional[str] = ""
    VITB6_AMT: Optional[str] = ""
    VITB6_DV: Optional[str] = ""

class LabelData(BaseModel):
    SERVING_SIZE: str
    SERVINGS_PER_CONTAINER: str
    nutrients: Nutrients

# ---------------------------------------------------------------------------
# Utils
# ---------------------------------------------------------------------------
def load_template() -> str:
    """Load the SVG template file."""
    path = os.path.join(os.path.dirname(__file__), "NutritionFacts Template.svg")
    if not os.path.exists(path):
        raise FileNotFoundError("NutritionFacts Template.svg not found in app directory")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def fill_template(svg_template: str, payload: LabelData) -> str:
    """Replace placeholders like {{CALORIES}} with real data."""
    svg_filled = svg_template
    # Replace simple top-level placeholders
    svg_filled = svg_filled.replace("{{SERVING_SIZE}}", payload.SERVING_SIZE)
    svg_filled = svg_filled.replace("{{SERVINGS_PER_CONTAINER}}", payload.SERVINGS_PER_CONTAINER)

    # Replace all nutrient placeholders
    for key, value in payload.nutrients.dict().items():
        svg_filled = re.sub(rf"{{{{{key}}}}}", str(value), svg_filled)
    return svg_filled

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "POST JSON to /render/nutrition with Authorization: Bearer <API_KEY>.",
        "example_keys": [
            "SERVING_SIZE",
            "SERVINGS_PER_CONTAINER",
            "Nutrients section includes keys like CALORIES, TOTAL_FAT_AMT, TOTAL_FAT_DV, etc."
        ]
    }

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/render/nutrition")
def render_nutrition(payload: LabelData, request: Request, authorization: str = Header(None)):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="Server not configured: API_KEY missing.")
    if authorization != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        template_svg = load_template()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template error: {e}")

    svg_filled = fill_template(template_svg, payload)

    # Render PNG with CairoSVG
    try:
        png_bytes = cairosvg.svg2png(bytestring=svg_filled.encode("utf-8"), dpi=300)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Render error: {e}")

    # Return bytes or JSON
    accept = (request.headers.get("accept") or "").lower()
    if "image/png" in accept:
        return Response(content=png_bytes, media_type="image/png")

    b64 = base64.b64encode(png_bytes).decode("utf-8")
    return {"mime_type": "image/png", "image_base64": b64}
