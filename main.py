from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"status": "running"}

@app.get("/global-state")
def global_state():
    return {
        "countries": {
            "EGP": 0.72,
            "TRY": 0.65
        },
        "GCI": 0.68,
        "regime": "REGIONAL STRESS"
    }
