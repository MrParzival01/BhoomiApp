"""
Bhoomi-AI: Hybrid Dataset Generator
====================================
Generates a semi-real training dataset combining:
- Real soil parameter ranges from Punjab Soil Health Card data
- Real NDVI ranges from Sentinel-2 satellite observations
- Yield models calibrated to PAU (Punjab Agricultural University) field trials

Sources:
- Soil Health Cards: soilhealth.dac.gov.in (Punjab district averages)
- NDVI ranges: Sentinel-2 observations for Punjab wheat/paddy belts
- Yield calibration: PAU Ludhiana Nano Urea trial reports (2022-2024)
"""

import pandas as pd
import numpy as np

np.random.seed(42)

# ============================================================
# REAL DATA RANGES (from Punjab Soil Health Card portal & PAU)
# ============================================================

# District-wise soil data from Punjab Soil Health Cards
# Format: (nitrogen_low, nitrogen_high, ph_low, ph_high, oc_low, oc_high)
PUNJAB_DISTRICTS = {
    "Ludhiana":   (180, 320, 7.0, 8.2, 0.30, 0.65),
    "Amritsar":   (150, 290, 7.2, 8.4, 0.25, 0.55),
    "Patiala":    (170, 310, 6.8, 8.0, 0.35, 0.70),
    "Jalandhar":  (160, 300, 7.1, 8.3, 0.28, 0.60),
    "Bathinda":   (120, 260, 7.5, 8.8, 0.20, 0.45),
    "Sangrur":    (165, 305, 7.0, 8.1, 0.30, 0.62),
    "Moga":       (155, 295, 7.2, 8.3, 0.27, 0.58),
    "Firozpur":   (130, 270, 7.4, 8.6, 0.22, 0.50),
    "Gurdaspur":  (175, 315, 6.9, 8.0, 0.32, 0.65),
    "Kapurthala": (160, 300, 7.0, 8.2, 0.29, 0.60),
}

# Real NDVI ranges observed in Punjab (Sentinel-2)
# Varies by crop and growth stage
NDVI_RANGES = {
    "wheat": {
        "germination":    (0.15, 0.30),
        "tillering":      (0.35, 0.55),
        "jointing":       (0.50, 0.72),
        "heading":        (0.60, 0.80),
        "grain_filling":  (0.45, 0.65),
    },
    "paddy": {
        "seedling":           (0.15, 0.28),
        "tillering":          (0.35, 0.58),
        "panicle_initiation": (0.55, 0.75),
        "flowering":          (0.60, 0.80),
        "grain_filling":      (0.45, 0.62),
    }
}

# Growth stage day ranges
GROWTH_STAGES = {
    "wheat": {
        "germination":   (0, 20),
        "tillering":     (21, 50),
        "jointing":      (51, 80),
        "heading":       (81, 100),
        "grain_filling": (101, 130),
    },
    "paddy": {
        "seedling":           (0, 15),
        "tillering":          (16, 45),
        "panicle_initiation": (46, 65),
        "flowering":          (66, 90),
        "grain_filling":      (91, 120),
    }
}

# PAU yield benchmarks (quintal/acre)
# From PAU field trials comparing different urea strategies
YIELD_BENCHMARKS = {
    "wheat": {"min": 14.0, "max": 22.0, "traditional_avg": 18.5},
    "paddy": {"min": 22.0, "max": 32.0, "traditional_avg": 27.0},
}

# Phosphorus and Potassium ranges from Soil Health Cards (kg/ha)
P_RANGE = (10, 45)   # Available Phosphorus
K_RANGE = (120, 320)  # Available Potassium


def calculate_optimal_solid_pct(soil_n, soil_ph, organic_carbon, ndvi,
                                 growth_stage, crop_type):
    """
    Calculate optimal solid urea percentage based on agronomic rules
    derived from PAU research findings.
    
    Key rules from PAU trials:
    1. Low soil N + low OC → soil is starving → more solid urea needed
    2. High pH (>8.0) → Nano absorption drops → more solid needed
    3. Early growth stages → roots establishing → more solid needed
    4. High NDVI → crop is healthy → can shift more to Nano
    5. 100% Nano = 21% yield drop (PAU 2024) → never go below 30% solid
    """
    base_solid = 50.0  # Start at 50:50 — the core hybrid promise

    # --- Soil Nitrogen Effect ---
    # Low N soil needs more direct solid feeding, but moderate soil is fine at 50:50
    if soil_n < 150:
        base_solid += 8   # Very low → favor solid
    elif soil_n < 200:
        base_solid += 3   # Slightly low
    elif soil_n > 280:
        base_solid -= 6   # Rich soil → lean into Nano
    elif soil_n > 320:
        base_solid -= 10  # Very rich → Nano-heavy

    # --- Organic Carbon Effect ---
    # Low OC = dead microbiome, but most Punjab soil is moderate
    if organic_carbon < 0.25:
        base_solid += 7   # Very depleted
    elif organic_carbon < 0.35:
        base_solid += 3   # Below average
    elif organic_carbon > 0.55:
        base_solid -= 5   # Healthy soil
    elif organic_carbon > 0.65:
        base_solid -= 8   # Very healthy, go Nano-heavy

    # --- pH Effect ---
    # High pH reduces Nano efficacy, but effect is moderate
    if soil_ph > 8.5:
        base_solid += 5
    elif soil_ph > 8.0:
        base_solid += 2
    elif soil_ph < 6.8:
        base_solid -= 3   # Slightly acidic = better Nano absorption

    # --- Growth Stage Effect ---
    # Only germination/seedling needs heavy solid (roots not established)
    # Tillering onwards, leaves are developed enough for Nano
    if crop_type == "wheat":
        if growth_stage == "germination":
            base_solid += 6  # Roots just forming, need solid
        elif growth_stage == "tillering":
            base_solid += 2  # Transitioning, slight solid preference
        elif growth_stage in ["heading", "grain_filling"]:
            base_solid -= 6  # Leaves fully developed, Nano works great
    else:  # paddy
        if growth_stage == "seedling":
            base_solid += 6
        elif growth_stage == "tillering":
            base_solid += 2
        elif growth_stage in ["flowering", "grain_filling"]:
            base_solid -= 6

    # --- NDVI Effect ---
    # High NDVI = crop is thriving, shift toward Nano
    if ndvi > 0.70:
        base_solid -= 5
    elif ndvi > 0.55:
        base_solid -= 2
    elif ndvi < 0.25:
        base_solid += 5   # Crop struggling badly

    # --- Crop Type Base Adjustment ---
    if crop_type == "paddy":
        base_solid -= 2  # Paddy responds slightly better to foliar

    # Clamp: minimum 30% solid (PAU: 100% Nano = 21% yield drop)
    # maximum 70% solid (otherwise what's the point of hybrid?)
    base_solid = np.clip(base_solid, 30, 70)

    return base_solid


def calculate_yield(solid_pct, soil_n, organic_carbon, ndvi, crop_type):
    """
    Estimate yield based on PAU trial findings.
    
    Key finding: 100% Nano = ~21% yield drop
    Optimal hybrid (around 50:50 adjusted) = matches or slightly
    exceeds traditional yield.
    """
    benchmark = YIELD_BENCHMARKS[crop_type]
    base_yield = benchmark["traditional_avg"]

    # Yield penalty for being too far from optimal
    # Too much Nano (low solid%) = soil starvation
    if solid_pct < 35:
        penalty = (35 - solid_pct) * 0.15  # ~21% drop at 0% solid
        base_yield -= penalty
    # Too much solid (high solid%) = missing Nano efficiency gains
    elif solid_pct > 65:
        penalty = (solid_pct - 65) * 0.05  # Small penalty
        base_yield -= penalty

    # Boost from good soil conditions
    if organic_carbon > 0.5:
        base_yield += 1.0
    if ndvi > 0.6:
        base_yield += 0.8
    if soil_n > 280:
        base_yield += 0.5

    # Clamp
    base_yield = np.clip(base_yield, benchmark["min"], benchmark["max"])
    return base_yield


def generate_dataset(n_samples=1000):
    """Generate the full hybrid dataset."""
    rows = []

    for i in range(n_samples):
        # --- Pick random district (real soil ranges) ---
        district = np.random.choice(list(PUNJAB_DISTRICTS.keys()))
        n_lo, n_hi, ph_lo, ph_hi, oc_lo, oc_hi = PUNJAB_DISTRICTS[district]

        # --- Pick crop type ---
        crop_type = np.random.choice(["wheat", "paddy"], p=[0.55, 0.45])

        # --- Generate soil parameters (from real ranges + noise) ---
        soil_nitrogen = np.random.uniform(n_lo, n_hi)
        soil_ph = np.random.uniform(ph_lo, ph_hi)
        organic_carbon = np.random.uniform(oc_lo, oc_hi)
        phosphorus = np.random.uniform(*P_RANGE)
        potassium = np.random.uniform(*K_RANGE)

        # --- Pick growth stage and calculate days since sowing ---
        stages = list(GROWTH_STAGES[crop_type].keys())
        growth_stage = np.random.choice(stages)
        day_lo, day_hi = GROWTH_STAGES[crop_type][growth_stage]
        days_since_sowing = np.random.randint(day_lo, day_hi + 1)

        # --- Generate NDVI (from real Sentinel-2 ranges) ---
        ndvi_lo, ndvi_hi = NDVI_RANGES[crop_type][growth_stage]
        ndvi = np.random.uniform(ndvi_lo, ndvi_hi)

        # --- Plot size (typical Punjab farm) ---
        plot_acres = np.random.choice(
            [1, 2, 3, 4, 5, 7, 10, 12, 15],
            p=[0.10, 0.20, 0.20, 0.15, 0.15, 0.08, 0.06, 0.04, 0.02]
        )

        # --- Calculate optimal solid urea % ---
        optimal_solid_pct = calculate_optimal_solid_pct(
            soil_nitrogen, soil_ph, organic_carbon,
            ndvi, growth_stage, crop_type
        )

        # Add realistic noise (±3-5%) to simulate real-world variance
        noise = np.random.normal(0, 3)
        optimal_solid_pct = np.clip(optimal_solid_pct + noise, 30, 75)
        nano_pct = 100 - optimal_solid_pct

        # --- Calculate expected yield ---
        expected_yield = calculate_yield(
            optimal_solid_pct, soil_nitrogen, organic_carbon, ndvi, crop_type
        )
        yield_noise = np.random.normal(0, 0.8)
        expected_yield = max(expected_yield + yield_noise, 10)

        # --- Calculate actual bags/bottles needed ---
        # Standard: wheat needs ~120 kg N/ha, paddy ~110 kg N/ha
        # 1 acre = 0.4047 hectares
        n_requirement = 120 if crop_type == "wheat" else 110  # kg N/ha
        n_total_kg = n_requirement * plot_acres * 0.4047
        # Solid urea is 46% nitrogen, 1 bag = 45 kg
        solid_urea_kg = (optimal_solid_pct / 100) * n_total_kg / 0.46
        solid_bags = solid_urea_kg / 45
        # 1 bottle Nano Urea (500ml) ≈ replaces 1 bag (45kg) solid urea
        nano_bottles = (nano_pct / 100) * n_total_kg / (0.46 * 45)
        water_liters = plot_acres * 125  # Standard spray volume

        rows.append({
            "district": district,
            "crop_type": crop_type,
            "plot_acres": plot_acres,
            "soil_nitrogen_kg_ha": round(soil_nitrogen, 1),
            "soil_ph": round(soil_ph, 2),
            "organic_carbon_pct": round(organic_carbon, 3),
            "phosphorus_kg_ha": round(phosphorus, 1),
            "potassium_kg_ha": round(potassium, 1),
            "growth_stage": growth_stage,
            "days_since_sowing": days_since_sowing,
            "ndvi": round(ndvi, 3),
            "optimal_solid_urea_pct": round(optimal_solid_pct, 1),
            "optimal_nano_urea_pct": round(nano_pct, 1),
            "solid_urea_bags": round(solid_bags, 2),
            "nano_urea_bottles": round(nano_bottles, 2),
            "water_liters": water_liters,
            "expected_yield_quintal_acre": round(expected_yield, 2),
        })

    df = pd.DataFrame(rows)
    return df


if __name__ == "__main__":
    print("Generating Bhoomi-AI training dataset...")
    print("=" * 50)

    df = generate_dataset(1000)
    df.to_csv("bhoomi_training_data.csv", index=False)

    print(f"Dataset shape: {df.shape}")
    print(f"\nCrop distribution:\n{df['crop_type'].value_counts()}")
    print(f"\nDistrict distribution:\n{df['district'].value_counts()}")
    print(f"\nTarget variable (optimal_solid_urea_pct) stats:")
    print(df['optimal_solid_urea_pct'].describe())
    print(f"\nSample rows:")
    print(df.head(10).to_string())
    print(f"\nDataset saved to: bhoomi_training_data.csv")
