# Nutrition Label Renderer

A FastAPI service that renders FDA-style nutrition fact labels as PNG images from JSON data.

## Requirements

- Python 3.11+
- System dependencies for CairoSVG (libcairo, libpango — see [CairoSVG docs](https://cairosvg.org/documentation/))

```bash
pip install -r requirements.txt
```

## Running Locally

```bash
export API_KEY=your_secret_key
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Endpoints

### `GET /`
Returns service info and example request keys.

### `GET /healthz`
Health check — returns `{"ok": true}`.

### `POST /render/nutrition`
Renders a nutrition facts label as a PNG.

**Headers:**
```
Authorization: Bearer <API_KEY>
Content-Type: application/json
Accept: image/png          # returns raw PNG bytes
# or omit Accept header   # returns {"mime_type": "image/png", "image_base64": "..."}
```

**Request body:**
```json
{
  "SERVING_SIZE": "1 cup (240ml)",
  "SERVINGS_PER_CONTAINER": "2",
  "nutrients": {
    "CALORIES": 250,
    "TOTAL_FAT_AMT": "12g",
    "TOTAL_FAT_DV": "15%",
    "SAT_FAT_AMT": "3g",
    "SAT_FAT_DV": "15%",
    "TRANS_FAT_AMT": "0g",
    "TRANS_FAT_DV": "0%",
    "CHOLESTEROL_AMT": "30mg",
    "CHOLESTEROL_DV": "10%",
    "SODIUM_AMT": "470mg",
    "SODIUM_DV": "20%",
    "CARBS_AMT": "31g",
    "CARBS_DV": "11%",
    "FIBER_AMT": "0g",
    "FIBER_DV": "0%",
    "SUGARS_AMT": "5g",
    "SUGARS_DV": "0%",
    "ADD_SUG_AMT": "0g",
    "ADD_SUG_DV": "0%",
    "PROTEIN_AMT": "5g",
    "PROTEIN_DV": "0%",
    "VITD_AMT": "2mcg",
    "VITD_DV": "10%",
    "CALCIUM_AMT": "260mg",
    "CALCIUM_DV": "20%",
    "IRON_AMT": "8mg",
    "IRON_DV": "45%",
    "POTASSIUM_AMT": "235mg",
    "POTASSIUM_DV": "6%"
  }
}
```

All `nutrients` fields have sensible zero-value defaults, so you only need to supply the fields relevant to your product. The optional fields `VITC_AMT`, `VITC_DV`, `VITB6_AMT`, and `VITB6_DV` default to empty strings.

**Response (JSON):**
```json
{
  "mime_type": "image/png",
  "image_base64": "<base64-encoded PNG>"
}
```

## Deployment

Configured for [Render.com](https://render.com) via `render.yaml`. Set the `API_KEY` environment variable in your Render service settings.
