import requests

SOILGRIDS_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"

def get_soil_texture(lat: float, lon: float) -> dict:
    try:
        r = requests.get(
            SOILGRIDS_URL,
            params={"lon": lon, "lat": lat, "property": ["clay","sand","silt"], "depth": "0-5cm", "value": "mean"},
            timeout=20
        )
        r.raise_for_status()
        result = {}
        for layer in r.json()["properties"]["layers"]:
            val = layer["depths"][0]["values"]["mean"]
            result[layer["name"] + "_pct"] = round(val / 10, 1) if val is not None else None
        return result
    except Exception as e:
        print(f"[SoilGrids] {e}")
        return {"clay_pct": None, "sand_pct": None, "silt_pct": None}