from fastapi import FastAPI
import random

app = FastAPI()

def generate_country_stress():
    countries = {
        # Core EM
        "EGP": random.uniform(0.6, 0.9),
        "TRY": random.uniform(0.5, 0.8),
        "ARS": random.uniform(0.7, 0.95),
        "NGN": random.uniform(0.6, 0.85),
        "PKR": random.uniform(0.6, 0.85),
        "LKR": random.uniform(0.5, 0.8),
        "GHS": random.uniform(0.6, 0.85),
        "KES": random.uniform(0.5, 0.75),

        # Secondary EM
        "ZAR": random.uniform(0.3, 0.7),
        "BRL": random.uniform(0.3, 0.6),
        "MXN": random.uniform(0.3, 0.6),
        "IDR": random.uniform(0.3, 0.6),
        "INR": random.uniform(0.2, 0.5),
        "CLP": random.uniform(0.3, 0.6),
        "COP": random.uniform(0.3, 0.6),

        # G10 / Systemic
        "USD": random.uniform(0.1, 0.3),
        "EUR": random.uniform(0.1, 0.3),
        "JPY": random.uniform(0.1, 0.3),
        "CNY": random.uniform(0.2, 0.4),
        "GBP": random.uniform(0.1, 0.3),
    }
    return countries

@app.get("/")
def home():
    return {"status": "running"}

@app.get("/global-state")
def global_state():
    countries = generate_country_stress()
    gci = sum(countries.values()) / len(countries)

    if gci > 0.75:
        regime = "CRISIS"
    elif gci > 0.6:
        regime = "CONTAGION STRESS"
    elif gci > 0.4:
        regime = "REGIONAL STRESS"
    else:
        regime = "STABLE"

    return {
        "countries": countries,
        "GCI": round(gci, 2),
        "regime": regime
    }
