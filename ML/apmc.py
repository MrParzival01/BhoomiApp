import math

APMC_DB = [
    # Karnataka
    {"name":"Raichur APMC","state":"Karnataka","district":"Raichur","lat":16.2120,"lon":77.3566,"commodities":["Rice","Jowar","Cotton","Groundnut","Maize"]},
    {"name":"Kalaburagi APMC","state":"Karnataka","district":"Kalaburagi","lat":17.3297,"lon":76.8343,"commodities":["Tur Dal","Chickpea","Cotton","Jowar"]},
    {"name":"Bellary APMC","state":"Karnataka","district":"Bellary","lat":15.1394,"lon":76.9214,"commodities":["Cotton","Groundnut","Onion","Tomato"]},
    {"name":"Vijayapura APMC","state":"Karnataka","district":"Vijayapura","lat":16.8302,"lon":75.7100,"commodities":["Onion","Jowar","Sunflower","Chickpea"]},
    {"name":"Hubli APMC","state":"Karnataka","district":"Dharwad","lat":15.3647,"lon":75.1240,"commodities":["Groundnut","Cotton","Jowar","Wheat"]},
    {"name":"Yeshwanthpur APMC","state":"Karnataka","district":"Bangalore","lat":13.0250,"lon":77.5420,"commodities":["Vegetables","Fruits","Flowers","Onion"]},
    {"name":"Davangere APMC","state":"Karnataka","district":"Davangere","lat":14.4644,"lon":75.9218,"commodities":["Rice","Maize","Groundnut","Cotton"]},
    {"name":"Mysuru APMC","state":"Karnataka","district":"Mysuru","lat":12.3052,"lon":76.6552,"commodities":["Rice","Ragi","Silk","Vegetables"]},
    {"name":"Bidar APMC","state":"Karnataka","district":"Bidar","lat":17.9104,"lon":77.5199,"commodities":["Tur Dal","Soybean","Jowar","Maize"]},
    {"name":"Haveri APMC","state":"Karnataka","district":"Haveri","lat":14.7939,"lon":75.4005,"commodities":["Cotton","Chilli","Groundnut","Paddy"]},
    {"name":"Shimoga APMC","state":"Karnataka","district":"Shimoga","lat":13.9299,"lon":75.5681,"commodities":["Rice","Arecanut","Coconut"]},
    {"name":"Mandya APMC","state":"Karnataka","district":"Mandya","lat":12.5218,"lon":76.8951,"commodities":["Sugarcane","Rice","Ragi"]},
    {"name":"Koppal APMC","state":"Karnataka","district":"Koppal","lat":15.3508,"lon":76.1547,"commodities":["Rice","Cotton","Groundnut","Jowar"]},
    {"name":"Yadgir APMC","state":"Karnataka","district":"Yadgir","lat":16.7700,"lon":77.1400,"commodities":["Tur Dal","Jowar","Cotton","Groundnut"]},
    # Telangana / Andhra Pradesh
    {"name":"Bowenpally Market","state":"Telangana","district":"Hyderabad","lat":17.4647,"lon":78.4998,"commodities":["Vegetables","Fruits","Onion","Tomato"]},
    {"name":"Guntur APMC","state":"Andhra Pradesh","district":"Guntur","lat":16.3067,"lon":80.4365,"commodities":["Chilli","Cotton","Tobacco","Rice"]},
    {"name":"Kurnool APMC","state":"Andhra Pradesh","district":"Kurnool","lat":15.8281,"lon":78.0373,"commodities":["Cotton","Groundnut","Onion","Jowar"]},
    {"name":"Warangal APMC","state":"Telangana","district":"Warangal","lat":17.9689,"lon":79.5941,"commodities":["Cotton","Maize","Turmeric","Rice"]},
    {"name":"Nizamabad APMC","state":"Telangana","district":"Nizamabad","lat":18.6725,"lon":78.0941,"commodities":["Turmeric","Rice","Maize","Cotton"]},
    {"name":"Nalgonda APMC","state":"Telangana","district":"Nalgonda","lat":17.0575,"lon":79.2671,"commodities":["Cotton","Maize","Groundnut"]},
    {"name":"Mahbubnagar APMC","state":"Telangana","district":"Mahbubnagar","lat":16.7488,"lon":77.9886,"commodities":["Cotton","Jowar","Groundnut"]},
    # Maharashtra
    {"name":"Gultekdi Market","state":"Maharashtra","district":"Pune","lat":18.4862,"lon":73.8503,"commodities":["Onion","Tomato","Vegetables","Fruits"]},
    {"name":"Vashi APMC","state":"Maharashtra","district":"Navi Mumbai","lat":19.0748,"lon":73.0001,"commodities":["Vegetables","Fruits","Onion","Potato"]},
    {"name":"Lasalgaon APMC","state":"Maharashtra","district":"Nashik","lat":20.1244,"lon":74.1764,"commodities":["Onion"]},
    {"name":"Nashik APMC","state":"Maharashtra","district":"Nashik","lat":20.0059,"lon":73.7898,"commodities":["Onion","Grapes","Tomato","Pomegranate"]},
    {"name":"Nagpur APMC","state":"Maharashtra","district":"Nagpur","lat":21.1458,"lon":79.0882,"commodities":["Orange","Cotton","Soybean","Vegetables"]},
    {"name":"Solapur APMC","state":"Maharashtra","district":"Solapur","lat":17.6599,"lon":75.9064,"commodities":["Jowar","Pomegranate","Onion","Pulses"]},
    {"name":"Aurangabad APMC","state":"Maharashtra","district":"Aurangabad","lat":19.8762,"lon":75.3433,"commodities":["Cotton","Soybean","Jowar","Mosambi"]},
    {"name":"Kolhapur APMC","state":"Maharashtra","district":"Kolhapur","lat":16.7050,"lon":74.2433,"commodities":["Sugarcane","Vegetables","Gur"]},
    # Tamil Nadu
    {"name":"Koyambedu Market","state":"Tamil Nadu","district":"Chennai","lat":13.0701,"lon":80.1956,"commodities":["Vegetables","Fruits","Flowers","Onion"]},
    {"name":"Coimbatore APMC","state":"Tamil Nadu","district":"Coimbatore","lat":11.0168,"lon":76.9558,"commodities":["Cotton","Coconut","Turmeric","Vegetables"]},
    {"name":"Madurai APMC","state":"Tamil Nadu","district":"Madurai","lat":9.9252,"lon":78.1198,"commodities":["Vegetables","Banana","Rice","Jasmine"]},
    {"name":"Salem APMC","state":"Tamil Nadu","district":"Salem","lat":11.6643,"lon":78.1460,"commodities":["Mango","Vegetables","Tapioca","Onion"]},
    # Delhi NCR
    {"name":"Azadpur Mandi","state":"Delhi","district":"Delhi","lat":28.7196,"lon":77.1762,"commodities":["Vegetables","Fruits","Onion","Potato"]},
    {"name":"Ghazipur Mandi","state":"Delhi","district":"Delhi","lat":28.6250,"lon":77.3270,"commodities":["Vegetables","Fruits","Flowers"]},
    # Uttar Pradesh
    {"name":"Lucknow APMC","state":"Uttar Pradesh","district":"Lucknow","lat":26.8467,"lon":80.9462,"commodities":["Wheat","Rice","Potato","Vegetables"]},
    {"name":"Kanpur APMC","state":"Uttar Pradesh","district":"Kanpur","lat":26.4499,"lon":80.3319,"commodities":["Wheat","Mustard","Potato","Pulses"]},
    {"name":"Agra APMC","state":"Uttar Pradesh","district":"Agra","lat":27.1767,"lon":78.0081,"commodities":["Wheat","Potato","Vegetables"]},
    # Punjab Haryana
    {"name":"Ludhiana APMC","state":"Punjab","district":"Ludhiana","lat":30.9010,"lon":75.8573,"commodities":["Wheat","Rice","Potato"]},
    {"name":"Amritsar APMC","state":"Punjab","district":"Amritsar","lat":31.6340,"lon":74.8723,"commodities":["Wheat","Rice","Maize"]},
    {"name":"Karnal APMC","state":"Haryana","district":"Karnal","lat":29.6857,"lon":76.9905,"commodities":["Wheat","Rice","Vegetables"]},
    # Rajasthan
    {"name":"Jaipur APMC","state":"Rajasthan","district":"Jaipur","lat":26.9124,"lon":75.7873,"commodities":["Vegetables","Mustard","Wheat"]},
    {"name":"Jodhpur APMC","state":"Rajasthan","district":"Jodhpur","lat":26.2389,"lon":73.0243,"commodities":["Guar","Mustard","Bajra"]},
    {"name":"Unjha APMC","state":"Gujarat","district":"Mehsana","lat":23.8060,"lon":72.3937,"commodities":["Cumin","Fennel","Coriander","Isabgol"]},
    # Gujarat
    {"name":"Ahmedabad APMC","state":"Gujarat","district":"Ahmedabad","lat":23.0225,"lon":72.5714,"commodities":["Cotton","Groundnut","Castor","Vegetables"]},
    {"name":"Rajkot APMC","state":"Gujarat","district":"Rajkot","lat":22.3039,"lon":70.8022,"commodities":["Groundnut","Cotton","Castor","Sesame"]},
    # MP
    {"name":"Indore APMC","state":"Madhya Pradesh","district":"Indore","lat":22.7196,"lon":75.8577,"commodities":["Soybean","Wheat","Garlic","Onion"]},
    {"name":"Bhopal APMC","state":"Madhya Pradesh","district":"Bhopal","lat":23.2599,"lon":77.4126,"commodities":["Wheat","Soybean","Maize"]},
    # West Bengal
    {"name":"Mechua Market","state":"West Bengal","district":"Kolkata","lat":22.5726,"lon":88.3639,"commodities":["Vegetables","Fish","Rice","Potato"]},
    # Odisha
    {"name":"Bhubaneswar APMC","state":"Odisha","district":"Bhubaneswar","lat":20.2961,"lon":85.8245,"commodities":["Rice","Vegetables","Fruits"]},
]

MSP_2024_25 = {
    "rice":2300,"maize":2090,"cotton":7121,"jute":5335,"mungbean":8682,
    "blackgram":7400,"pigeonpeas":7550,"chickpea":5440,"lentil":6425,
    "kidneybeans":6000,"mothbeans":5650,
}

SCHEMES = [
    {"name":"PM-KISAN","benefit":"₹6,000/year direct income support","eligibility":"All landholding farmer families","link":"https://pmkisan.gov.in"},
    {"name":"PMFBY (Crop Insurance)","benefit":"Insurance cover against crop loss","eligibility":"All farmers growing notified crops","link":"https://pmfby.gov.in"},
    {"name":"Soil Health Card","benefit":"Free soil testing + nutrient recommendations","eligibility":"All farmers","link":"https://soilhealth.dac.gov.in"},
    {"name":"PM Kisan Maandhan","benefit":"Pension ₹3,000/month after age 60","eligibility":"Small/marginal farmers aged 18–40","link":"https://maandhan.in"},
    {"name":"Kisan Credit Card (KCC)","benefit":"Crop loans up to ₹3 lakh at 4% interest","eligibility":"All farmers, sharecroppers, SHGs","link":"https://www.nabard.org"},
]

def _haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def get_nearest_apmcs(lat, lon, top_n=3):
    ranked = []
    for m in APMC_DB:
        entry = dict(m)
        entry["distance_km"] = round(_haversine(lat, lon, m["lat"], m["lon"]), 1)
        entry["maps_url"] = f"https://www.google.com/maps?q={m['lat']},{m['lon']}"
        ranked.append(entry)
    ranked.sort(key=lambda x: x["distance_km"])
    return ranked[:top_n]

def get_msp_and_schemes(crop: str) -> dict:
    return {
        "crop":     crop,
        "msp":      MSP_2024_25.get(crop.lower()),
        "msp_unit": "₹/quintal",
        "msp_year": "2024-25",
        "schemes":  SCHEMES,
    }