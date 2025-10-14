from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
import base64, io, textwrap
from PIL import ImageFont, ImageDraw, Image
import cairosvg
import os

app = FastAPI(title="Nutrition Label Renderer", version="2.0.0")
API_KEY = os.environ.get("API_KEY", "CHANGE_ME")

class Nutrients(BaseModel):
    calories: float
    fat_g: float
    satfat_g: float
    transfat_g: float
    chol_mg: float
    sodium_mg: float
    carb_g: float
    fiber_g: float
    sugars_g: float
    added_sugars_g: float
    protein_g: float
    vitd_mcg: float
    calcium_mg: float
    iron_mg: float
    potassium_mg: float

class Options(BaseModel):
    dpi: int = 300
    min_width_px: int = 750
    max_width_px: int = 1400
    padding_px: int = 36
    rounded: bool = True

class NutritionRenderRequest(BaseModel):
    serving_display: str
    servings_per_container: int
    nutrients: Nutrients
    options: Optional[Options] = Options()

def load_font(size: int, bold: bool = False):
    names = ["Arial Bold.ttf" if bold else "Arial.ttf",
             "Helvetica-Bold.ttf" if bold else "Helvetica.ttf",
             "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"]
    for n in names:
        try:
            return ImageFont.truetype(n, size=size)
        except Exception:
            continue
    return ImageFont.load_default()

def text_width(s: str, font) -> int:
    img = Image.new("L", (10, 10))
    draw = ImageDraw.Draw(img)
    try:
        return int(draw.textlength(s, font=font))
    except Exception:
        return draw.textbbox((0,0), s, font=font)[2]

def build_svg(payload: NutritionRenderRequest) -> str:
    o = payload.options or Options()
    DPI = max(300, min(600, o.dpi))
    PAD = o.padding_px

    f_title = load_font(int(80*DPI/300), True)
    f_bold  = load_font(int(30*DPI/300), True)
    f_norm  = load_font(int(30*DPI/300), False)
    f_cal   = load_font(int(64*DPI/300), True)
    f_small = load_font(int(24*DPI/300), False)

    left_labels = [
        "Serving size","Amount per serving",
        "Total fat","Saturated fat","Trans fat",
        "Cholesterol","Sodium","Total carbohydrate","Dietary fiber",
        "Total sugars","Includes Added Sugars","Protein",
        "Vitamin D","Calcium","Iron","Potassium"
    ]
    max_left = max(text_width(s, f_bold if s in ["Total fat","Total carbohydrate","Protein"] else f_norm) for s in left_labels)

    amounts = [
        f"{payload.nutrients.fat_g} g", f"{payload.nutrients.satfat_g} g",
        f"{payload.nutrients.transfat_g} g", f"{payload.nutrients.chol_mg} mg",
        f"{payload.nutrients.sodium_mg} mg", f"{payload.nutrients.carb_g} g",
        f"{payload.nutrients.fiber_g} g", f"{payload.nutrients.sugars_g} g",
        f"{payload.nutrients.added_sugars_g} g", f"{payload.nutrients.protein_g} g",
        f"{payload.nutrients.vitd_mcg} mcg", f"{payload.nutrients.calcium_mg} mg",
        f"{payload.nutrients.iron_mg} mg", f"{payload.nutrients.potassium_mg} mg"
    ]
    max_amt = max(text_width(a, f_norm) for a in amounts)
    max_dv  = text_width("100%", f_norm)

    gap = int(18*DPI/300)
    left_margin = PAD + 24
    right_margin = PAD + 24
    content_w = left_margin + max_left + gap + max_amt + gap + max_dv + right_margin
    W = max(o.min_width_px, min(o.max_width_px, content_w))

    line_h  = int(36*DPI/300)
    thick_h = int(12*DPI/300)
    thin_h  = int(4*DPI/300)

    y = PAD
    rows_svg = []

    def rule(thick=False):
        nonlocal y
        rows_svg.append(f'<rect x="{PAD}" y="{y}" width="{W-2*PAD}" height="{thick_h if thick else thin_h}" fill="#000"/>' )
        y += (thick_h if thick else thin_h)

    outer_tpl = '<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#fff" stroke="#000" stroke-width="6" rx="{r}" ry="{r}"/>'

    rows_svg.append(f'<text x="{left_margin}" y="{y+int(0.9*line_h)}" font-family="DejaVu Sans" font-weight="700" font-size="{f_title.size}">NUTRITION FACTS</text>')
    y += int(f_title.size*1.25)
    rule(False); y += line_h//2

    rows_svg.append(f'<text x="{left_margin}" y="{y}" font-family="DejaVu Sans" font-weight="700" font-size="{f_bold.size}">Serving size</text>')
    rows_svg.append(f'<text x="{W-right_margin}" y="{y}" text-anchor="end" font-family="DejaVu Sans" font-size="{f_norm.size}">{payload.serving_display}</text>')
    y += line_h
    rows_svg.append(f'<text x="{left_margin}" y="{y}" font-family="DejaVu Sans" font-size="{f_norm.size}">Servings per container</text>')
    rows_svg.append(f'<text x="{W-right_margin}" y="{y}" text-anchor="end" font-family="DejaVu Sans" font-size="{f_norm.size}">{payload.servings_per_container}</text>')
    y += line_h
    rule(False); y += line_h//3

    rows_svg.append(f'<text x="{left_margin}" y="{y}" font-family="DejaVu Sans" font-size="{f_norm.size}">Amount per serving</text>')
    y += line_h
    rows_svg.append(f'<text x="{left_margin}" y="{y+int(0.2*line_h)}" font-family="DejaVu Sans" font-weight="700" font-size="{f_cal.size}">Calories</text>')
    rows_svg.append(f'<text x="{W-right_margin}" y="{y+int(0.2*line_h)}" text-anchor="end" font-family="DejaVu Sans" font-weight="700" font-size="{f_cal.size}">{int(round(payload.nutrients.calories))}</text>')
    y += int(f_cal.size*0.9)
    rule(True); y += line_h//3

    rows_svg.append(f'<text x="{W-right_margin}" y="{y}" text-anchor="end" font-family="DejaVu Sans" font-weight="700" font-size="{f_bold.size}">% Daily Value*</text>')
    y += line_h

    amt_x = W - right_margin - max_dv - gap

    def row(label, amount, dv_text=None, bold=False):
        nonlocal y
        weight = "700" if bold else "400"
        rows_svg.append(f'<text x="{left_margin}" y="{y}" font-family="DejaVu Sans" font-weight="{weight}" font-size="{f_norm.size}">{label}</text>')
        rows_svg.append(f'<text x="{amt_x}" y="{y}" text-anchor="end" font-family="DejaVu Sans" font-size="{f_norm.size}">{amount}</text>')
        if dv_text is not None:
            rows_svg.append(f'<text x="{W-right_margin}" y="{y}" text-anchor="end" font-family="DejaVu Sans" font-size="{f_norm.size}">{dv_text}</text>')
        y += line_h

    row("Total fat", f"{payload.nutrients.fat_g} g", "—", True)
    row("Saturated fat", f"{payload.nutrients.satfat_g} g")
    row("Trans fat", f"{payload.nutrients.transfat_g} g")
    rule(False)

    row("Cholesterol", f"{payload.nutrients.chol_mg} mg", "—", True)
    rule(False)

    row("Sodium", f"{payload.nutrients.sodium_mg} mg", "—", True)
    rule(False)

    row("Total carbohydrate", f"{payload.nutrients.carb_g} g", "—", True)
    row("Dietary fiber", f"{payload.nutrients.fiber_g} g")
    row("Total sugars", f"{payload.nutrients.sugars_g} g")
    row("Includes Added Sugars", f"{payload.nutrients.added_sugars_g} g")
    rule(False)

    row("Protein", f"{payload.nutrients.protein_g} g", "—", True)
    rule(False)

    for name, amt in [
        ("Vitamin D", f"{payload.nutrients.vitd_mcg} mcg"),
        ("Calcium", f"{payload.nutrients.calcium_mg} mg"),
        ("Iron", f"{payload.nutrients.iron_mg} mg"),
        ("Potassium", f"{payload.nutrients.potassium_mg} mg"),
    ]:
        row(name, amt)

    rule(False)

    foot = ("*Percent Daily Values are based on a 2,000 calorie diet. "
            "Your daily values may be higher or lower depending on your calorie needs.")
    wrap_w = W - left_margin - right_margin
    avg_char = max(1, int(wrap_w / max(8, text_width('M', f_small))))
    for line in textwrap.wrap(foot, width=avg_char):
        rows_svg.append(f'<text x="{left_margin}" y="{y}" font-family="DejaVu Sans" font-size="{f_small.size}">{line}</text>')
        y += int(0.9 * line_h)

    H = y + PAD
    outer = f'<rect x="{int(PAD/2)}" y="{int(PAD/2)}" width="{int(W-PAD)}" height="{int(H-PAD)}" fill="#fff" stroke="#000" stroke-width="6" rx="{20 if o.rounded else 0}" ry="{20 if o.rounded else 0}"/>'

    svg = ['<svg xmlns="http://www.w3.org/2000/svg" '
           f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" shape-rendering="crispEdges">',
           outer,
           *rows_svg,
           '</svg>']
    return "\n".join(svg)

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/render/nutrition")
def render_nutrition(payload: NutritionRenderRequest, authorization: str = Header(None)):
    if not API_KEY or authorization != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    svg = build_svg(payload)
    png_bytes = cairosvg.svg2png(bytestring=svg.encode("utf-8"), dpi=payload.options.dpi)
    b64 = base64.b64encode(png_bytes).decode("utf-8")
    return {"mime_type": "image/png", "image_base64": b64}