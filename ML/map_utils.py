import math
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

FEATURE_COLS = ["lat", "lon", "ndvi", "temperature", "rainfall", "elevation", "clay_pct", "sand_pct", "silt_pct"]

def predict_for_point(lat, lon, lgbm_models, weather_fn, ndvi_fn, elev_fn, texture_fn):
    """
    Fetch environmental features and run all LightGBM models for one point.
    Falls back to realistic India-typical defaults if any API fails.
    Returns dict {param: value}.
    """
    try:
        t, r = weather_fn(lat, lon)
        temperature = t if t is not None else 28.0
        rainfall    = r if r is not None else 950.0
    except Exception:
        temperature, rainfall = 28.0, 950.0

    try:
        end_dt   = datetime.now() - timedelta(days=7)
        start_dt = end_dt - timedelta(days=365)
        nv       = ndvi_fn(lat, lon, start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d"))
        ndvi_val = nv if nv is not None else 0.55
    except Exception:
        ndvi_val = 0.55

    try:
        e         = elev_fn(lat, lon)
        elevation = e if e is not None else 200.0
    except Exception:
        elevation = 200.0

    try:
        tex      = texture_fn(lat, lon)
        clay_pct = tex.get("clay_pct") or 30.0
        sand_pct = tex.get("sand_pct") or 40.0
        silt_pct = tex.get("silt_pct") or 30.0
    except Exception:
        clay_pct, sand_pct, silt_pct = 30.0, 40.0, 30.0

    input_df = pd.DataFrame(
        [[lat, lon, ndvi_val, temperature, rainfall, elevation, clay_pct, sand_pct, silt_pct]],
        columns=FEATURE_COLS
    )
    preds = {}
    for param, model in lgbm_models.items():
        try:
            raw          = model.predict(input_df)[0]
            preds[param] = round(float(np.expm1(raw)), 3)
        except Exception:
            preds[param] = None

    return preds


def dummy_predictions(lat, lon, seed_offset=0):
    """
    Generate spatially-varying realistic dummy predictions when models unavailable.
    Uses sine/cosine spatial variation to mimic a real raster surface.
    """
    rng   = np.random.default_rng(int(abs(lat * 1000 + lon * 1000)) + seed_offset)
    noise = rng.uniform(-0.08, 0.08)
    def wave(low, high, freq=3.5):
        base   = (math.sin(lat * freq + lon * freq * 1.3) + 1) / 2
        jitter = rng.uniform(-0.06, 0.06)
        return round(low + (high - low) * max(0, min(1, base + jitter + noise)), 3)

    return {
        "ph"            : wave(5.5, 8.2),
        "n"             : wave(80,  480),
        "p"             : wave(5,   55),
        "k"             : wave(80,  700),
        "organic_carbon": wave(0.4, 3.8),
        "s"             : wave(4,   45),
        "fe"            : wave(2,   35),
        "zn"            : wave(0.2, 8),
        "cu"            : wave(0.1, 7),
        "b"             : wave(0.2, 4),
        "mn"            : wave(1,   18),
    }
