import os
from time import sleep
import mlflow.sklearn
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import asyncio

MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
mlflow.set_tracking_uri(MLFLOW_URI)

model_cache = {}


def attempt_load_model():
    """
    Helper function to attempt loading the model from MLflow.
    Returns True if successful, False otherwise.
    """
    print(f"🔄 Trying to load model from: {MLFLOW_URI}")
    mlflow.set_tracking_uri(MLFLOW_URI)

    try:
        experiment = mlflow.get_experiment_by_name("taxi-demand-prediction")
        if experiment is None:
            print("⚠️ Experiment not found (Has training started yet?).")
            return False

        print("🔎 Looking for the latest finished run...")
        runs = mlflow.search_runs(
            experiment_ids=[experiment.experiment_id],
            filter_string="status = 'FINISHED'",
            order_by=["start_time DESC"],
            max_results=1
        )
        
        if not runs.empty:
            run_id = runs.iloc[0].run_id

            if 'model_run_id' in model_cache and model_cache['model_run_id'] == run_id:
                print(f"ℹ️ Model already loaded (Run ID: {run_id})")
                return True

            model_uri = f"runs:/{run_id}/model"
            print(f"📥 Found model (Run ID: {run_id}). Loading...")
            model_cache['model'] = mlflow.sklearn.load_model(model_uri)
            print("✅ Model loaded into memory!")
            return True
        else:
            print("⚠️ No finished runs found.")
            return False
            
    except Exception as e:
        print(f"❌ MLflow connection error: {e}")
        return False


async def periodic_model_reload(interval = 300):
    """
    Periodically checks and reloads the model if not present in cache.
    
    :param interval: Time interval between checks in seconds. Default is 300 seconds (5 minutes).
    """
    while True:
        await asyncio.sleep(interval)
        print("🔄 Periodic model check...")
        attempt_load_model()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Loads ML model at startup and clears it at shutdown.
    """
    # --- STARTUP ---
    # Call helper function to try and load the model
    success = attempt_load_model()
    if not success:
        print("⚠️ Starting without model. The model will be loaded on the first request (Lazy Loading).")
    
    # Start periodic model reload task
    reload_task = asyncio.create_task(periodic_model_reload())

    yield

    # --- SHUTDOWN ---
    reload_task.cancel()
    model_cache.clear()
    print("👋 Model unloaded from memory.")

app = FastAPI(title="🚖 Taxi Demand Prediction API", lifespan=lifespan)

# CORS Middleware for local testing with frontend apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Input Schema (same as training)
class TaxiRide(BaseModel):
    PULocationID: int
    DOLocationID: int
    trip_distance: float

@app.get("/")
def home():
    return {
        "status": "online", 
        "model_loaded": 'model' in model_cache
    }

@app.post("/predict")
def predict_duration(ride: TaxiRide):
    """
    Riceve i dati della corsa e restituisce la durata stimata in minuti.
    """
    if 'model' not in model_cache:
        print("⚠️ Model not in cache. Attempting lazy load...")
        success = False

        for i in range(3):
            print(f"🔄 Attempt {i+1}/3...")
            success = attempt_load_model()
            if success:
                break
            sleep(2)  # Wait before retrying
        if not success:
            raise HTTPException(
                status_code=503, 
                detail="Model not available yet. Training might still be in progress. Check MLflow UI at http://localhost:5000"
            )
    
    
    try:
        # Create DataFrame (with explicit float casting as in training to avoid mismatches)
        input_data = {
            "PULocationID": [float(ride.PULocationID)],
            "DOLocationID": [float(ride.DOLocationID)],
            "trip_distance": [float(ride.trip_distance)]
        }
        df = pd.DataFrame(input_data)
        
        # Prediction happens here
        model = model_cache['model']
        prediction = model.predict(df)
        
        # Result
        return {
            "predicted_duration_minutes": round(prediction[0], 2),
            "ride_details": ride
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore predizione: {str(e)}")