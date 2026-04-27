CALENDAR = {
    "rice":        {"sow":[6,7],  "harvest":[10,11], "duration":"4-5 months",  "season":"Kharif"},
    "maize":       {"sow":[6,7],  "harvest":[9,10],  "duration":"3-4 months",  "season":"Kharif"},
    "cotton":      {"sow":[5,6],  "harvest":[10,12], "duration":"5-6 months",  "season":"Kharif"},
    "jute":        {"sow":[3,4],  "harvest":[7,8],   "duration":"4-5 months",  "season":"Kharif"},
    "mungbean":    {"sow":[6,7],  "harvest":[9,10],  "duration":"3 months",    "season":"Kharif"},
    "blackgram":   {"sow":[6,7],  "harvest":[9,10],  "duration":"3 months",    "season":"Kharif"},
    "mothbeans":   {"sow":[6,7],  "harvest":[9,10],  "duration":"3 months",    "season":"Kharif"},
    "pigeonpeas":  {"sow":[6,7],  "harvest":[12,1],  "duration":"6-9 months",  "season":"Kharif"},
    "kidneybeans": {"sow":[11,12],"harvest":[3,4],   "duration":"4 months",    "season":"Rabi"},
    "chickpea":    {"sow":[10,11],"harvest":[2,3],   "duration":"4-5 months",  "season":"Rabi"},
    "lentil":      {"sow":[10,11],"harvest":[3,4],   "duration":"4-5 months",  "season":"Rabi"},
    "banana":      {"sow":[1,2],  "harvest":[10,12], "duration":"10-12 months","season":"Annual"},
    "mango":       {"sow":[7,8],  "harvest":[4,6],   "duration":"Perennial",   "season":"Perennial"},
    "apple":       {"sow":[1,2],  "harvest":[8,10],  "duration":"Perennial",   "season":"Perennial"},
    "grapes":      {"sow":[1,2],  "harvest":[3,5],   "duration":"Perennial",   "season":"Perennial"},
    "orange":      {"sow":[6,7],  "harvest":[11,1],  "duration":"Perennial",   "season":"Perennial"},
    "coconut":     {"sow":[5,6],  "harvest":[1,12],  "duration":"Perennial",   "season":"Perennial"},
    "coffee":      {"sow":[5,6],  "harvest":[11,2],  "duration":"Perennial",   "season":"Perennial"},
    "papaya":      {"sow":[6,7],  "harvest":[10,12], "duration":"9-12 months", "season":"Annual"},
    "watermelon":  {"sow":[1,2],  "harvest":[4,5],   "duration":"3-4 months",  "season":"Zaid"},
    "muskmelon":   {"sow":[1,2],  "harvest":[4,5],   "duration":"3-4 months",  "season":"Zaid"},
    "pomegranate": {"sow":[6,7],  "harvest":[2,3],   "duration":"Perennial",   "season":"Perennial"},
}
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def get_calendar(crop: str) -> dict:
    cal = CALENDAR.get(crop.lower())
    if not cal:
        return {}
    return {
        "crop":            crop,
        "sow_months":      [MONTHS[m-1] for m in cal["sow"]],
        "harvest_months":  [MONTHS[m-1] for m in cal["harvest"]],
        "sow_indices":     [m-1 for m in cal["sow"]],
        "harvest_indices": [m-1 for m in cal["harvest"]],
        "duration":        cal["duration"],
        "season":          cal["season"],
    }