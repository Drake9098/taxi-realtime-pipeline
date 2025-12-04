# Inference Service - FastAPI Model Serving
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/predict")
def predict():
    return {"prediction": 0}
