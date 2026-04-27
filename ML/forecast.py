import requests
from datetime import datetime

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

WMO = {
    0: ("Clear Sky","☀️"), 1: ("Mainly Clear","🌤️"), 2: ("Partly Cloudy","⛅"),
    3: ("Overcast","☁️"), 45: ("Foggy","🌫️"), 48: ("Icy Fog","🌫️"),
    51: ("Light Drizzle","🌦️"), 53: ("Drizzle","🌦️"), 55: ("Heavy Drizzle","🌦️"),
    61: ("Slight Rain","🌧️"), 63: ("Rain","🌧️"), 65: ("Heavy Rain","🌧️"),
    71: ("Slight Snow","❄️"), 73: ("Snow","❄️"), 75: ("Heavy Snow","❄️"),
    80: ("Rain Showers","🌧️"), 81: ("Showers","🌧️"), 82: ("Heavy Showers","🌧️"),
    95: ("Thunderstorm","⛈️"), 96: ("Thunderstorm+Hail","⛈️"), 99: ("Thunderstorm+Hail","⛈️"),
}

def get_forecast(lat: float, lon: float) -> list:
    try:
        r = requests.get(OPEN_METEO_URL, params={
            "latitude": lat, "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
            "timezone": "Asia/Kolkata", "forecast_days": 7,
        }, timeout=15)
        r.raise_for_status()
        d = r.json()["daily"]
        days = []
        for i in range(7):
            code = d["weathercode"][i]
            desc, icon = WMO.get(code, ("Unknown","🌡️"))
            days.append({
                "date":  d["time"][i],
                "day":   datetime.strptime(d["time"][i], "%Y-%m-%d").strftime("%a"),
                "icon":  icon,
                "desc":  desc,
                "max":   round(d["temperature_2m_max"][i], 1),
                "min":   round(d["temperature_2m_min"][i], 1),
                "rain":  round(d["precipitation_sum"][i], 1),
            })
        return days
    except Exception as e:
        print(f"[Forecast] {e}")
        return []