import os
import pickle
import glob
from weather import get_weather
from map_utils import predict_for_point, dummy_predictions

# Path to trained LightGBM models from ml_pipeline
MODELS_DIR = os.path.join(os.path.dirname(__file__), "module")


def _load_models():
    models = {}
    pattern = os.path.join(MODELS_DIR, "lgbm_*.pkl")
    for path in glob.glob(pattern):
        param = os.path.basename(path).replace("lgbm_", "").replace(".pkl", "")
        with open(path, "rb") as f:
            models[param] = pickle.load(f)
    return models


def predict(lat: float, lon: float) -> dict:
    """
    Return predicted soil parameters for a GPS location.

    Parameters
    ----------
    lat : float  Latitude
    lon : float  Longitude

    Returns
    -------
    dict with keys: ph, n, p, k, organic_carbon, s, fe, zn, cu, b, mn
    """
    models = _load_models()

    if models:
        # Real predictions using trained LightGBM models + NASA POWER weather
        # NDVI / elevation / texture fall back to India-typical defaults if GEE unavailable
        def _ndvi(lat, lon, *_): return None
        def _elev(lat, lon):     return None
        def _texture(lat, lon):  return {}

        return predict_for_point(
            lat, lon,
            lgbm_models=models,
            weather_fn=get_weather,
            ndvi_fn=_ndvi,
            elev_fn=_elev,
            texture_fn=_texture,
        )
    else:
        print("[predict] No trained models found — returning dummy predictions.")
        print(f"[predict] Train models first: cd {MODELS_DIR.replace('/models','')} && python3 train_model.py\n")
        return dummy_predictions(lat, lon)


if __name__ == "__main__":
    lat, lon = 16.1550, 76.5199  # Raichur-Lingasur
    print(f"Predicting soil parameters for ({lat}, {lon})...\n")
    result = predict(lat, lon)
    print(f"{'Parameter':<16} {'Value':>10}")
    print("-" * 28)
    for param, value in result.items():
        print(f"{param:<16} {str(value):>10}")