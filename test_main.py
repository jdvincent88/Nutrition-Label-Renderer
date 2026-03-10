"""Tests for the Nutrition Label Renderer."""
import os
import sys
import types
import unittest.mock as mock
import pytest


def _import_main():
    """Import main, stubbing out cairosvg which may not be installed."""
    if "main" in sys.modules:
        del sys.modules["main"]

    cairosvg_stub = types.ModuleType("cairosvg")
    cairosvg_stub.svg2png = mock.MagicMock(return_value=b"FAKEPNG")

    with mock.patch.dict(sys.modules, {"cairosvg": cairosvg_stub}):
        import main as m
    return m


@pytest.fixture(scope="module")
def main():
    return _import_main()


def _make_payload(main, **overrides):
    nutrients_data = {
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
        "PROTEIN_DV": "10%",
        "VITD_AMT": "2mcg",
        "VITD_DV": "10%",
        "CALCIUM_AMT": "260mg",
        "CALCIUM_DV": "20%",
        "IRON_AMT": "8mg",
        "IRON_DV": "45%",
        "POTASSIUM_AMT": "235mg",
        "POTASSIUM_DV": "6%",
    }
    nutrients_data.update(overrides)
    return main.LabelData(
        SERVING_SIZE="1 cup (240ml)",
        SERVINGS_PER_CONTAINER="2",
        nutrients=main.Nutrients(**nutrients_data),
    )


# ---------------------------------------------------------------------------
# fill_template tests
# ---------------------------------------------------------------------------

def test_fill_template_replaces_serving_size(main):
    payload = _make_payload(main)
    result = main.fill_template("Serving size {{SERVING_SIZE}}", payload)
    assert "1 cup (240ml)" in result
    assert "{{SERVING_SIZE}}" not in result


def test_fill_template_replaces_servings_per_container(main):
    payload = _make_payload(main)
    result = main.fill_template("{{SERVINGS_PER_CONTAINER}} servings", payload)
    assert "2 servings" in result
    assert "{{SERVINGS_PER_CONTAINER}}" not in result


def test_fill_template_replaces_calories(main):
    payload = _make_payload(main)
    result = main.fill_template("Calories {{CALORIES}}", payload)
    assert "250" in result
    assert "{{CALORIES}}" not in result


def test_fill_template_replaces_all_nutrients(main):
    payload = _make_payload(main)
    all_keys = list(payload.nutrients.model_dump().keys()) + ["SERVING_SIZE", "SERVINGS_PER_CONTAINER"]
    template = " ".join(f"{{{{{k}}}}}" for k in all_keys)
    result = main.fill_template(template, payload)
    assert "{{" not in result
    assert "}}" not in result


def test_fill_template_no_placeholders_unchanged(main):
    payload = _make_payload(main)
    template = "<svg><rect/></svg>"
    assert main.fill_template(template, payload) == template


# ---------------------------------------------------------------------------
# SVG template file tests
# ---------------------------------------------------------------------------

def test_svg_template_has_text_elements():
    template_path = os.path.join(os.path.dirname(__file__), "NutritionFacts Template.svg")
    with open(template_path, "r", encoding="utf-8") as f:
        svg = f.read()
    assert "<text" in svg, "SVG template must contain <text> elements for dynamic data"


def test_svg_template_has_all_required_placeholders():
    template_path = os.path.join(os.path.dirname(__file__), "NutritionFacts Template.svg")
    with open(template_path, "r", encoding="utf-8") as f:
        svg = f.read()

    required = [
        "SERVING_SIZE", "SERVINGS_PER_CONTAINER", "CALORIES",
        "TOTAL_FAT_AMT", "TOTAL_FAT_DV",
        "SAT_FAT_AMT", "SAT_FAT_DV",
        "TRANS_FAT_AMT",
        "CHOLESTEROL_AMT", "CHOLESTEROL_DV",
        "SODIUM_AMT", "SODIUM_DV",
        "CARBS_AMT", "CARBS_DV",
        "FIBER_AMT", "FIBER_DV",
        "SUGARS_AMT",
        "ADD_SUG_AMT", "ADD_SUG_DV",
        "PROTEIN_AMT",
        "VITD_AMT", "VITD_DV",
        "CALCIUM_AMT", "CALCIUM_DV",
        "IRON_AMT", "IRON_DV",
        "POTASSIUM_AMT", "POTASSIUM_DV",
    ]
    missing = [k for k in required if f"{{{{{k}}}}}" not in svg]
    assert not missing, f"SVG template missing placeholders: {missing}"


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

def test_nutrients_defaults(main):
    n = main.Nutrients(CALORIES=100)
    assert n.TOTAL_FAT_AMT == "0g"
    assert n.SODIUM_AMT == "0mg"
    assert n.VITC_AMT == ""


def test_nutrients_all_defaults_work(main):
    n = main.Nutrients()
    assert n.CALORIES == 0


def test_label_data_requires_serving_size(main):
    with pytest.raises(Exception):
        main.LabelData(SERVINGS_PER_CONTAINER="2", nutrients=main.Nutrients())


def test_label_data_requires_servings_per_container(main):
    with pytest.raises(Exception):
        main.LabelData(SERVING_SIZE="1 cup", nutrients=main.Nutrients())
