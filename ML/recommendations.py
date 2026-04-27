import os
import pickle
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ── Paths ──────────────────────────────────────────────────────────────────────
_DIR        = os.path.dirname(__file__)
_MODULE_DIR = os.path.join(_DIR, "module")
_CROP_MODEL = os.path.join(_DIR, "..", "crop_pridiction", "classifier.pkl")

# ── Crop labels (matches classifier.pkl class order) ───────────────────────────
CROPS = [
    'apple', 'banana', 'blackgram', 'chickpea', 'coconut', 'coffee',
    'cotton', 'grapes', 'jute', 'kidneybeans', 'lentil', 'maize',
    'mango', 'mothbeans', 'mungbean', 'muskmelon', 'orange', 'papaya',
    'pigeonpeas', 'pomegranate', 'rice', 'watermelon'
]

# ── Typical NPK requirements per crop (kg/ha) ──────────────────────────────────
# Format: {crop: (N_required, P_required, K_required)}
CROP_NPK = {
    'apple':       (70,  35,  70),
    'banana':      (200, 60,  300),
    'blackgram':   (20,  40,  40),
    'chickpea':    (20,  60,  40),
    'coconut':     (100, 40,  200),
    'coffee':      (100, 60,  100),
    'cotton':      (120, 60,  60),
    'grapes':      (100, 50,  150),
    'jute':        (60,  30,  30),
    'kidneybeans': (20,  60,  40),
    'lentil':      (20,  40,  40),
    'maize':       (120, 60,  40),
    'mango':       (100, 50,  100),
    'mothbeans':   (20,  40,  40),
    'mungbean':    (20,  40,  40),
    'muskmelon':   (80,  40,  60),
    'orange':      (100, 50,  100),
    'papaya':      (200, 100, 200),
    'pigeonpeas':  (20,  50,  40),
    'pomegranate': (100, 50,  100),
    'rice':        (120, 60,  60),
    'watermelon':  (100, 50,  80),
}

# ── 1. Soil Fertility Score ────────────────────────────────────────────────────

def get_fertility(soil: dict, ndvi: float = 0.55, rainfall: float = 950.0,
                  elevation: float = 200.0, clay_pct: float = 30.0,
                  sand_pct: float = 40.0, silt_pct: float = 30.0) -> dict:
    """
    Classify soil fertility as low / medium / high using the trained
    Random Forest model.

    Parameters
    ----------
    soil     : dict with keys ph, n, p, k, organic_carbon, s, fe, zn, cu, b, mn
    ndvi, rainfall, elevation, clay_pct, sand_pct, silt_pct : floats (env features)

    Returns
    -------
    dict: { 'fertility': 'low'|'medium'|'high', 'confidence': float (0-100) }
    """
    with open(os.path.join(_MODULE_DIR, "rf_fertility.pkl"), "rb") as f:
        model = pickle.load(f)

    features = [
        soil.get("ph", 6.5),
        soil.get("n", 200),
        soil.get("p", 30),
        soil.get("k", 200),
        soil.get("organic_carbon", 1.5),
        soil.get("s", 15),
        soil.get("fe", 10),
        soil.get("zn", 2),
        soil.get("cu", 1),
        soil.get("b", 1),
        soil.get("mn", 5),
        ndvi, rainfall, elevation, clay_pct, sand_pct, silt_pct
    ]

    proba      = model.predict_proba([features])[0]
    class_idx  = int(np.argmax(proba))
    fertility  = model.classes_[class_idx]
    confidence = round(float(proba[class_idx]) * 100, 1)

    return {"fertility": fertility, "confidence": confidence}


# ── 2. Fertilizer Recommendation ──────────────────────────────────────────────

def get_fertilizer_advice(crop: str, soil: dict) -> dict:
    """
    Compare current soil N, P, K against the crop's requirement and
    suggest how much to add.

    Parameters
    ----------
    crop : str  — crop name (one of CROP_NPK keys)
    soil : dict — must contain 'n', 'p', 'k' keys

    Returns
    -------
    dict: { 'n_advice': str, 'p_advice': str, 'k_advice': str,
            'n_deficit': float, 'p_deficit': float, 'k_deficit': float }
    """
    crop = crop.lower()
    if crop not in CROP_NPK:
        return {"error": f"No requirement data for crop '{crop}'"}

    req_n, req_p, req_k = CROP_NPK[crop]
    curr_n = soil.get("n", 0)
    curr_p = soil.get("p", 0)
    curr_k = soil.get("k", 0)

    def _advice(current, required, nutrient):
        deficit = round(max(0.0, required - current), 1)
        if deficit == 0:
            return f"Sufficient ({current:.1f} >= {required} kg/ha)", 0.0
        return f"Add ~{deficit} kg/ha (current {current:.1f}, needs {required})", deficit

    n_msg, n_def = _advice(curr_n, req_n, "N")
    p_msg, p_def = _advice(curr_p, req_p, "P")
    k_msg, k_def = _advice(curr_k, req_k, "K")

    return {
        "crop":       crop,
        "n_advice":   n_msg,  "n_deficit": n_def,
        "p_advice":   p_msg,  "p_deficit": p_def,
        "k_advice":   k_msg,  "k_deficit": k_def,
    }


# ── 3. Crop Suitability Ranking ────────────────────────────────────────────────

def rank_crops(soil: dict, temperature: float, humidity: float,
               rainfall: float, top_n: int = 5) -> list:
    """
    Rank all 22 crops by suitability for the given soil and environment.

    Parameters
    ----------
    soil        : dict with keys n, p, k, ph
    temperature : float (°C)
    humidity    : float (%) — use 70.0 if unknown
    rainfall    : float (mm)
    top_n       : int — how many top crops to return

    Returns
    -------
    list of dicts: [{ 'rank': 1, 'crop': 'rice', 'score': 94.2 }, ...]
    """
    with open(_CROP_MODEL, "rb") as f:
        model = pickle.load(f)

    features = pd.DataFrame([{
        "N":           soil.get("n", 90),
        "P":           soil.get("p", 42),
        "K":           soil.get("k", 43),
        "temperature": temperature,
        "humidity":    humidity,
        "ph":          soil.get("ph", 6.5),
        "rainfall":    rainfall,
    }])

    proba   = model.predict_proba(features)[0]
    ranked  = sorted(zip(CROPS, proba), key=lambda x: x[1], reverse=True)

    return [
        {"rank": i + 1, "crop": crop, "score": round(prob * 100, 1)}
        for i, (crop, prob) in enumerate(ranked[:top_n])
    ]