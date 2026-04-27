# Agriculture AI — ML Projects

A collection of ML modules that fetch real weather and satellite data, predict soil parameters, assess fertility, rank suitable crops, and give fertilizer recommendations for any GPS location — no manual soil testing required.

---

## Project Structure

```
Game/
├── requirements.txt
├── crop_pridiction/
│   ├── model.py            ← crop prediction function
│   ├── classifier.pkl      ← trained GradientBoosting model
│   └── run_test.py
└── ML/
    ├── weather.py          ← NASA POWER weather fetcher
    ├── ndvi.py             ← Google Earth Engine NDVI fetcher
    ├── predict.py          ← soil parameter prediction (LightGBM)
    ├── recommendations.py  ← fertility score, crop ranking, fertilizer advice
    ├── crop_nutrition.py   ← fertilizer doses (Urea/DAP/MOP/SSP) per crop
    ├── map_utils.py        ← feature assembly + dummy fallback
    ├── run_test.py         ← full pipeline test
    └── module/             ← trained LightGBM + RandomForest model files
```

---

## Setup

### 1. Clone the repo

```bash
git clone <repo-url>
cd Game
```

### 2. Extract ML models

The trained model files (`.pkl`) are bundled in `models.zip`. Unzip before running anything:

```bash
unzip models.zip
```

This restores:
```
ML/module/*.pkl          ← LightGBM + RandomForest soil/fertility models
crop_pridiction/classifier.pkl  ← GradientBoosting crop classifier
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** Do not commit the `env/` folder or `.pkl` files — they are excluded by `.gitignore`. Share models via `models.zip`.

---

## Quick Start

```bash
cd ML
python3 run_test.py
```

This runs the full pipeline for **Raichur-Lingasur (16.155, 76.519)** and prints:

```
========================================
WEATHER
========================================
  Temperature : 25.57 °C
  Rainfall    : 943.8 mm

========================================
SOIL PARAMETERS
========================================
  ph               6.8
  n                120.0
  ...

========================================
SOIL FERTILITY
========================================
  Level      : MEDIUM
  Confidence : 89.3%

========================================
TOP 5 SUITABLE CROPS
========================================
  1. rice             86.4%
  2. maize            13.5%
  ...

========================================
FERTILIZER ADVICE — RICE
========================================
  N : Add ~30 kg/ha (current 90, needs 120)
  P : Add ~20 kg/ha (current 40, needs 60)
  K : Sufficient (65 >= 60 kg/ha)
```

---

## Modules

### 1. Weather — `ML/weather.py`

Fetches average temperature (°C) and total rainfall (mm) from the NASA POWER API. No API key required.

```python
from weather import get_weather

temp, rain = get_weather(lat=16.155, lon=76.519)
print(temp, rain)
```

Returns `(None, None)` on failure.

---

### 2. Soil Parameter Prediction — `ML/predict.py`

Predicts 11 soil parameters for any GPS point using trained LightGBM models. Falls back to spatially-varying dummy values if models are unavailable.

```python
from predict import predict

soil = predict(lat=16.155, lon=76.519)
# Returns dict: ph, n, p, k, organic_carbon, s, fe, zn, cu, b, mn
```

| Parameter | Description | Unit |
|---|---|---|
| `ph` | Soil pH | — |
| `n` | Nitrogen | kg/ha |
| `p` | Phosphorous | kg/ha |
| `k` | Potassium | kg/ha |
| `organic_carbon` | Organic Carbon | % |
| `s` | Sulphur | kg/ha |
| `fe` | Iron | mg/kg |
| `zn` | Zinc | mg/kg |
| `cu` | Copper | mg/kg |
| `b` | Boron | mg/kg |
| `mn` | Manganese | mg/kg |

---

### 3. Soil Fertility Score — `ML/recommendations.py`

Classifies soil as **low / medium / high** fertility using a trained Random Forest model with 17 features (soil params + NDVI + weather + texture).

```python
from recommendations import get_fertility

result = get_fertility(soil, rainfall=943.8)
print(result)
# {'fertility': 'medium', 'confidence': 89.3}
```

---

### 4. Crop Suitability Ranking — `ML/recommendations.py`

Ranks all 22 supported crops by suitability for the given soil and environment using the crop classifier's probability scores.

```python
from recommendations import rank_crops

top = rank_crops(soil, temperature=25.5, humidity=70.0, rainfall=943.8, top_n=5)
for entry in top:
    print(entry['rank'], entry['crop'], entry['score'])
```

**Supported crops (22):** apple, banana, blackgram, chickpea, coconut, coffee, cotton, grapes, jute, kidneybeans, lentil, maize, mango, mothbeans, mungbean, muskmelon, orange, papaya, pigeonpeas, pomegranate, rice, watermelon

---

### 5. Fertilizer Recommendation — `ML/recommendations.py`

Compares current soil N, P, K against the selected crop's standard requirements and tells you how much to add.

```python
from recommendations import get_fertilizer_advice

advice = get_fertilizer_advice('rice', soil)
print(advice['n_advice'])  # "Add ~30 kg/ha (current 90, needs 120)"
print(advice['p_advice'])
print(advice['k_advice'])
```

---

### 6. Crop Nutrition Doses — `ML/crop_nutrition.py`

Given soil N/P/K and crop name, returns recommended Urea, DAP, MOP, and SSP doses in both kg/hectare and kg/acre. Adjusts doses up or down 25% based on actual soil levels. Also returns FYM requirement and target yield.

Covers **57 crops** including rice, wheat, maize, cotton, sugarcane, banana varieties, coffee, rubber, vegetables, and spices.

```python
from crop_nutrition import get_crop_urea_dap_mop_dose, get_crop_list

# Get fertilizer doses for rice given soil data
result = get_crop_urea_dap_mop_dose(
    n=120, p=45, k=200,
    ph=6.8, ec=0.5, oc=0.6,
    crop="rice"
)

for line in result["crop_fertilizer"][0]:
    print(line)
# Urea : 54.35 kg/hectare  21.74 kg/acre
# DAP  : 97.83 kg/hectare  39.13 kg/acre
# MOP  : 100.0 kg/hectare  40.0  kg/acre
# SSP  : 375.0 kg/hectare  150.0 kg/acre

for line in result["fym"][0]:
    print(line)
# Soil remedy   : No remedy needed
# Soil fertility: Medium fertile, soil is fertile
# FYM           : 10.0 tons/hectare
# Target yield  : 18-19 Quintals per acre
```

Pass `ph=None, ec=None, oc=None` to skip soil remedy output. Pass `n=0, p=0, k=0` to use the standard table values without adjustment.

```python
# List all supported crops
print(list(get_crop_list(api=True)))
```

---

### 7. Crop Prediction — `crop_pridiction/model.py`

Given exact soil values and environment data, returns the single best crop to grow.

```python
from model import run_model

crop = run_model({
    'N': [90], 'P': [42], 'K': [43],
    'temperature': [20.8], 'humidity': [82.0],
    'ph': [6.5], 'rainfall': [202.9]
})
print(crop)  # e.g. "rice"
```

---

### 7. NDVI — `ML/ndvi.py`

Fetches mean NDVI (vegetation health index) from Sentinel-2 satellite imagery via Google Earth Engine. Requires GEE authentication.

```python
from ndvi import get_ndvi

ndvi = get_ndvi(lat=16.155, lon=76.519, start_date="2024-01-01", end_date="2024-12-31")
# Returns float (0–1) or None
```

**NDVI guide:** `< 0.1` bare soil · `0.1–0.3` sparse · `0.3–0.6` moderate · `0.6–1.0` dense crops

#### GEE Authentication (one-time)

```bash
earthengine authenticate
```

---

## Data Sources

| Source | Data | API Key |
|---|---|---|
| NASA POWER | Temperature, Rainfall | Not required |
| Sentinel-2 (GEE) | NDVI | GEE account required |
| LightGBM models | Soil parameters | — |
| Random Forest model | Fertility class | — |
| Gradient Boosting | Crop suitability | — |