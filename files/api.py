"""
Bhoomi-AI: FastAPI Prediction Server
======================================
Single endpoint that loads the pre-trained Random Forest model
and returns fertilizer recommendations.

Run with: uvicorn api:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import joblib
import json
import numpy as np

# =====================
# LOAD MODEL & CONFIG
# =====================
model = joblib.load("bhoomi_model.joblib")

with open("model_config.json", "r") as f:
    config = json.load(f)

CROP_MAP = config["crop_classes"]
STAGE_MAP = config["stage_classes"]
DISTRICT_MAP = config["district_classes"]
N_REQUIREMENT = config["n_requirement_kg_ha"]

# Growth stage lookup from days since sowing
GROWTH_STAGE_DAYS = {
    "wheat": [
        (0, 20, "germination"),
        (21, 50, "tillering"),
        (51, 80, "jointing"),
        (81, 100, "heading"),
        (101, 999, "grain_filling"),
    ],
    "paddy": [
        (0, 15, "seedling"),
        (16, 45, "tillering"),
        (46, 65, "panicle_initiation"),
        (66, 90, "flowering"),
        (91, 999, "grain_filling"),
    ],
}

# Fertilizer schedule templates
SCHEDULE_TEMPLATES = {
    "wheat": {
        "germination": {
            "action": "Apply basal solid urea + DAP + MOP at sowing",
            "solid_split": 0.50,
            "nano_spray": False,
        },
        "tillering": {
            "action": "Apply 2nd split of solid urea at first irrigation",
            "solid_split": 0.25,
            "nano_spray": True,
            "spray_note": "1st Nano Urea spray (2-4 ml per liter of water)",
        },
        "jointing": {
            "action": "Apply 3rd split of solid urea at second irrigation",
            "solid_split": 0.25,
            "nano_spray": True,
            "spray_note": "2nd Nano Urea spray (2-4 ml per liter of water)",
        },
        "heading": {
            "action": "No more solid urea. Foliar spray only if needed.",
            "solid_split": 0.0,
            "nano_spray": True,
            "spray_note": "Optional 3rd Nano spray for grain filling support",
        },
        "grain_filling": {
            "action": "No fertilizer application. Crop is maturing.",
            "solid_split": 0.0,
            "nano_spray": False,
        },
    },
    "paddy": {
        "seedling": {
            "action": "Apply basal solid urea + DAP + MOP at transplanting",
            "solid_split": 0.50,
            "nano_spray": False,
        },
        "tillering": {
            "action": "Apply 2nd split of solid urea",
            "solid_split": 0.25,
            "nano_spray": True,
            "spray_note": "1st Nano Urea spray (2-4 ml per liter of water)",
        },
        "panicle_initiation": {
            "action": "Apply 3rd split of solid urea",
            "solid_split": 0.25,
            "nano_spray": True,
            "spray_note": "2nd Nano Urea spray (2-4 ml per liter of water)",
        },
        "flowering": {
            "action": "Foliar Nano spray only",
            "solid_split": 0.0,
            "nano_spray": True,
            "spray_note": "Optional Nano spray for grain support",
        },
        "grain_filling": {
            "action": "No fertilizer. Crop is maturing.",
            "solid_split": 0.0,
            "nano_spray": False,
        },
    },
}


# =====================
# API SETUP
# =====================
app = FastAPI(
    title="Bhoomi-AI Prediction API",
    description="Hybrid fertilizer recommendation engine for Punjab farmers",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your Nuxt app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================
# REQUEST/RESPONSE MODELS
# =====================
class PredictionRequest(BaseModel):
    crop_type: str = Field(..., description="'wheat' or 'paddy'")
    plot_acres: float = Field(..., gt=0, description="Farm size in acres")
    soil_nitrogen_kg_ha: float = Field(..., description="Soil nitrogen (kg/ha)")
    soil_ph: float = Field(..., description="Soil pH value")
    organic_carbon_pct: float = Field(..., description="Organic carbon %")
    phosphorus_kg_ha: float = Field(25.0, description="Phosphorus (kg/ha)")
    potassium_kg_ha: float = Field(200.0, description="Potassium (kg/ha)")
    days_since_sowing: int = Field(..., ge=0, description="Days since sowing")
    ndvi: float = Field(..., ge=0, le=1, description="NDVI value (0-1)")
    district: str = Field("Ludhiana", description="Punjab district name")


class FertilizerScheduleItem(BaseModel):
    stage: str
    day_range: str
    action: str
    solid_urea_bags: float
    nano_spray: bool
    spray_note: str = ""


class PredictionResponse(BaseModel):
    # Core prediction
    optimal_solid_urea_pct: float
    optimal_nano_urea_pct: float

    # Actual quantities
    total_solid_urea_bags: float
    total_nano_urea_bottles: float
    total_water_liters: float

    # NPK recommendation
    dap_bags: float
    mop_bags: float

    # Current stage info
    current_growth_stage: str
    current_action: str

    # Full season schedule
    schedule: list[FertilizerScheduleItem]

    # Cost comparison
    traditional_cost_inr: float
    hybrid_cost_inr: float
    savings_inr: float
    savings_pct: float

    # Environmental impact (the real value)
    urea_reduced_kg: float
    chemical_reduction_pct: float
    nitrogen_waste_prevented_kg: float


# =====================
# HELPER FUNCTIONS
# =====================
def get_growth_stage(crop_type: str, days: int) -> str:
    for lo, hi, stage in GROWTH_STAGE_DAYS[crop_type]:
        if lo <= days <= hi:
            return stage
    return GROWTH_STAGE_DAYS[crop_type][-1][2]  # Default to last stage


def calculate_costs(plot_acres, crop_type, solid_bags, nano_bottles, dap_bags, mop_bags):
    """
    Calculate costs using average Punjab market prices (2024).
    Includes: product cost + labor (carrying/spreading) + transport.
    """
    # Traditional: ALL nitrogen comes from solid urea
    n_req = 120 if crop_type == "wheat" else 110
    n_total_kg = n_req * plot_acres * 0.4047
    traditional_urea_kg = n_total_kg / 0.46
    traditional_urea_bags = traditional_urea_kg / 45

    # Prices
    urea_price = 267      # ₹/bag (subsidized)
    nano_price = 240      # ₹/bottle
    dap_price = 1350      # ₹/bag
    mop_price = 870       # ₹/bag
    labor_per_bag = 50    # ₹/bag for carrying + spreading
    transport_per_bag = 30 # ₹/bag for transport from dealer

    # Traditional total
    trad_urea_cost = traditional_urea_bags * (urea_price + labor_per_bag + transport_per_bag)
    traditional_cost = trad_urea_cost + dap_bags * dap_price + mop_bags * mop_price

    # Hybrid total
    hybrid_urea_cost = solid_bags * (urea_price + labor_per_bag + transport_per_bag)
    hybrid_nano_cost = nano_bottles * nano_price  # Nano is sprayed, less labor
    hybrid_cost = hybrid_urea_cost + hybrid_nano_cost + dap_bags * dap_price + mop_bags * mop_price

    return traditional_cost, hybrid_cost


# =====================
# PREDICTION ENDPOINT
# =====================
@app.post("/predict", response_model=PredictionResponse)
def predict(req: PredictionRequest):
    # Validate inputs
    if req.crop_type not in CROP_MAP:
        raise HTTPException(400, f"crop_type must be 'wheat' or 'paddy'")

    # Determine growth stage from days
    growth_stage = get_growth_stage(req.crop_type, req.days_since_sowing)

    if growth_stage not in STAGE_MAP:
        raise HTTPException(400, f"Unknown growth stage: {growth_stage}")

    district = req.district if req.district in DISTRICT_MAP else "Ludhiana"

    # Build feature vector (must match training order)
    features = np.array([[
        CROP_MAP[req.crop_type],
        req.plot_acres,
        req.soil_nitrogen_kg_ha,
        req.soil_ph,
        req.organic_carbon_pct,
        req.phosphorus_kg_ha,
        req.potassium_kg_ha,
        req.days_since_sowing,
        STAGE_MAP[growth_stage],
        req.ndvi,
        DISTRICT_MAP[district],
    ]])

    # Predict
    solid_pct = float(model.predict(features)[0])
    solid_pct = round(np.clip(solid_pct, 30, 75), 1)
    nano_pct = round(100 - solid_pct, 1)

    # Calculate actual quantities
    n_req = N_REQUIREMENT[req.crop_type]  # kg N per hectare
    n_total_kg = n_req * req.plot_acres * 0.4047  # acres to hectares

    solid_urea_kg = (solid_pct / 100) * n_total_kg / 0.46
    solid_bags = round(solid_urea_kg / 45, 1)

    nano_bottles = round((nano_pct / 100) * n_total_kg / (0.46 * 45), 1)
    water_liters = round(req.plot_acres * 125)

    # NPK: DAP and MOP (standard Punjab recommendation)
    # DAP bags are 50kg, DAP contains 46% P2O5 and 18% N
    # Wheat: 60 kg P2O5/ha, Paddy: 50 kg P2O5/ha
    hectares = req.plot_acres * 0.4047
    p_req = 60 if req.crop_type == "wheat" else 50
    dap_kg = (p_req * hectares) / 0.46  # kg of DAP needed
    dap_bags = round(dap_kg / 50, 1)    # 50 kg per bag

    # MOP: 40 kg K2O/ha → MOP is 60% K2O, bags are 50kg
    k_req = 40
    mop_kg = (k_req * hectares) / 0.60
    mop_bags = round(mop_kg / 50, 1)

    # Build full season schedule
    schedule = []
    stages_config = SCHEDULE_TEMPLATES[req.crop_type]
    stage_days = GROWTH_STAGE_DAYS[req.crop_type]

    for lo, hi, stage_name in stage_days:
        stage_info = stages_config[stage_name]
        stage_solid_bags = round(solid_bags * stage_info["solid_split"], 1)

        schedule.append(FertilizerScheduleItem(
            stage=stage_name,
            day_range=f"Day {lo}-{hi}",
            action=stage_info["action"],
            solid_urea_bags=stage_solid_bags,
            nano_spray=stage_info["nano_spray"],
            spray_note=stage_info.get("spray_note", ""),
        ))

    # Cost comparison
    trad_cost, hybrid_cost = calculate_costs(
        req.plot_acres, req.crop_type, solid_bags, nano_bottles, dap_bags, mop_bags
    )
    savings = trad_cost - hybrid_cost
    savings_pct = round((savings / trad_cost) * 100, 1) if trad_cost > 0 else 0

    # Environmental impact
    traditional_urea_kg = (n_total_kg / 0.46)  # total urea if 100% solid
    hybrid_urea_kg = solid_bags * 45
    urea_reduced_kg = round(traditional_urea_kg - hybrid_urea_kg, 1)
    chemical_reduction_pct = round((urea_reduced_kg / traditional_urea_kg) * 100, 1)
    # Traditional NUE is ~33%, Nano NUE is ~80%+
    # Wasted N in traditional = 67% of total N applied
    # Wasted N in hybrid = 67% of solid portion + 20% of Nano portion
    trad_waste = n_total_kg * 0.67
    hybrid_waste = (solid_pct / 100) * n_total_kg * 0.67 + (nano_pct / 100) * n_total_kg * 0.20
    nitrogen_waste_prevented = round(trad_waste - hybrid_waste, 1)

    # Current stage action
    current_info = stages_config[growth_stage]

    return PredictionResponse(
        optimal_solid_urea_pct=solid_pct,
        optimal_nano_urea_pct=nano_pct,
        total_solid_urea_bags=solid_bags,
        total_nano_urea_bottles=nano_bottles,
        total_water_liters=water_liters,
        dap_bags=dap_bags,
        mop_bags=mop_bags,
        current_growth_stage=growth_stage,
        current_action=current_info["action"],
        schedule=schedule,
        traditional_cost_inr=round(trad_cost),
        hybrid_cost_inr=round(hybrid_cost),
        savings_inr=round(savings),
        savings_pct=savings_pct,
        urea_reduced_kg=urea_reduced_kg,
        chemical_reduction_pct=chemical_reduction_pct,
        nitrogen_waste_prevented_kg=nitrogen_waste_prevented,
    )


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "metrics": config["model_metrics"],
    }
