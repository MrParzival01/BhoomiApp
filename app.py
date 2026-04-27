import sys
import os
import warnings
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "ML"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "crop_pridiction"))

from flask import Flask, request, jsonify, render_template
from concurrent.futures import ThreadPoolExecutor

from weather      import get_weather
from predict      import predict
from recommendations import get_fertility, get_fertilizer_advice, rank_crops
from soilgrids    import get_soil_texture
from forecast     import get_forecast
from crop_calendar import get_calendar
from apmc         import get_nearest_apmcs, get_msp_and_schemes
from model        import run_model

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def run_predict():
    data = request.get_json()
    lat  = float(data["lat"])
    lon  = float(data["lon"])

    # Fire slow API calls in parallel
    with ThreadPoolExecutor(max_workers=3) as ex:
        f_weather  = ex.submit(get_weather,      lat, lon)
        f_texture  = ex.submit(get_soil_texture,  lat, lon)
        f_forecast = ex.submit(get_forecast,      lat, lon)

    temp, rain = f_weather.result()
    temp = temp or 28.0
    rain = rain or 950.0

    texture  = f_texture.result()
    forecast = f_forecast.result()

    soil      = predict(lat, lon)
    fertility = get_fertility(soil, rainfall=rain)
    top_crops = rank_crops(soil, temperature=temp, humidity=70.0, rainfall=rain, top_n=5)
    best_crop = top_crops[0]["crop"]
    advice    = get_fertilizer_advice(best_crop, soil)
    calendar  = get_calendar(best_crop)
    msp       = get_msp_and_schemes(best_crop)
    apmcs     = get_nearest_apmcs(lat, lon, top_n=3)

    # Direct crop recommendation from run_model (uses soil + weather features)
    try:
        direct_crop = run_model({
            'N':           [soil.get("n", 90)],
            'P':           [soil.get("p", 42)],
            'K':           [soil.get("k", 43)],
            'temperature': [temp],
            'humidity':    [70.0],
            'ph':          [soil.get("ph", 6.5)],
            'rainfall':    [rain],
        })
    except Exception:
        direct_crop = None

    return jsonify({
        "direct_crop": direct_crop,
        "weather":    {"temperature": temp, "rainfall": rain},
        "forecast":   forecast,
        "soil":       soil,
        "texture":    texture,
        "fertility":  fertility,
        "crops":      top_crops,
        "fertilizer": advice,
        "calendar":   calendar,
        "msp":        msp,
        "apmcs":      apmcs,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)