import warnings
warnings.filterwarnings("ignore")

from weather import get_weather
from predict import predict
from recommendations import get_fertility, get_fertilizer_advice, rank_crops
from crop_nutrition import get_crop_urea_dap_mop_dose

# Raichur-Lingasur coordinates
lat = 16.1550
lon = 76.5199

# ── 1. Weather ─────────────────────────────────────────────────────────────────
temp, rain = get_weather(lat, lon)
print("=" * 40)
print("WEATHER")
print("=" * 40)
print(f"  Temperature : {temp} °C")
print(f"  Rainfall    : {rain} mm")

# ── 2. Soil Parameters ─────────────────────────────────────────────────────────
soil = predict(lat, lon)
print("\n" + "=" * 40)
print("SOIL PARAMETERS")
print("=" * 40)
for param, value in soil.items():
    print(f"  {param:<16} {value}")

# ── 3. Soil Fertility ──────────────────────────────────────────────────────────
fertility = get_fertility(soil, rainfall=rain or 950.0)
print("\n" + "=" * 40)
print("SOIL FERTILITY")
print("=" * 40)
print(f"  Level      : {fertility['fertility'].upper()}")
print(f"  Confidence : {fertility['confidence']}%")

# ── 4. Crop Suitability Ranking ────────────────────────────────────────────────
top_crops = rank_crops(soil, temperature=temp or 28.0, humidity=70.0, rainfall=rain or 950.0)
print("\n" + "=" * 40)
print("TOP 5 SUITABLE CROPS")
print("=" * 40)
for entry in top_crops:
    print(f"  {entry['rank']}. {entry['crop']:<16} {entry['score']}%")

# ── 5. Fertilizer Advice (for top crop) ───────────────────────────────────────
best_crop = top_crops[0]["crop"]
advice    = get_fertilizer_advice(best_crop, soil)
print(f"\n" + "=" * 40)
print(f"FERTILIZER ADVICE — {best_crop.upper()}")
print("=" * 40)
print(f"  N : {advice['n_advice']}")
print(f"  P : {advice['p_advice']}")
print(f"  K : {advice['k_advice']}")

# ── 6. Crop Nutrition Doses ────────────────────────────────────────────────────
nutrition = get_crop_urea_dap_mop_dose(
    n   = soil.get("n"),
    p   = soil.get("p"),
    k   = soil.get("k"),
    ph  = soil.get("ph"),
    ec  = soil.get("ec"),
    oc  = soil.get("organic_carbon"),
    crop= best_crop,
)
print(f"\n" + "=" * 40)
print(f"CROP NUTRITION DOSES — {best_crop.upper()}")
print("=" * 40)
if "error" in nutrition:
    print(f"  {nutrition['error']}")
else:
    for stage in nutrition["crop_fertilizer"]:
        for line in stage:
            print(f"  {line}")
    print()
    for row in nutrition["fym"]:
        for line in row:
            print(f"  {line}")