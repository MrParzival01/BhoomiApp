from model import run_model

# Example soil + environment values
soil_nutrients = {
    'N'          : [90],     # Nitrogen (kg/ha)
    'P'          : [42],     # Phosphorous (kg/ha)
    'K'          : [43],     # Potassium (kg/ha)
    'temperature': [20.8],   # °C
    'humidity'   : [82.0],   # %
    'ph'         : [6.5],    # pH level
    'rainfall'   : [202.9]   # mm
}

result = run_model(soil_nutrients)
print(f"Predicted crop: {result}")