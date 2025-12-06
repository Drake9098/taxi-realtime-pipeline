# 🚖 Real-Time Taxi Demand Prediction (End-to-End MLOps)

A complete **End-to-End MLOps system** that simulates a real-time streaming pipeline to predict the duration of NYC taxi trips. The system continuously learns from new incoming data (**Continuous Training**) and exposes an API for real-time predictions.

## 📋 Project Status

🟢 **Status:** Completed

- [x] **Data Ingestion:** Scalable Kafka Producer (Python + Docker).
- [x] **Streaming Infrastructure:** Apache Kafka & Zookeeper.
- [x] **Continuous Training:** Consumer that trains Random Forest models on-the-fly.
- [x] **Model Registry:** Experiment tracking and artifact versioning with MLflow.
- [x] **Inference API:** FastAPI microservice with "Lazy Loading" pattern to serve the latest available model.

## 🏗️ Monorepo Architecture

The project follows a **Microservices** architecture, orchestrated via Docker Compose.

```
taxi-realtime-pipeline/
│
├── producer/ # 📡 Service: Sends streaming data to Kafka
│ ├── app.py
│ └── Dockerfile
│
├── training/ # 🎓 Service: Consumes data & trains models
│ ├── train.py # Training logic & MLflow logging
│ └── Dockerfile
│
├── inference/ # 🚀 Service: Exposes REST API for predictions
│ ├── main.py # FastAPI app with auto-reload model logic
│ └── Dockerfile
│
├── data/ # 💾 Local data (Excluded from Git)
├── mlruns/ # 📂 Shared volume for MLflow artifacts
├── docker-compose.yml # 🐳 Orchestration
└── README.md
```

## 🎯 Technical Choices & Best Practices

Microservices Isolation: Each component runs in its own isolated Python environment (venv/Dockerfile) to avoid dependency conflicts.

Event-Driven: Decoupling between data production and model training via Kafka.

Data Robustness: Explicit type handling (Float64) and Schema Enforcement via MLflow Signatures.

API Resilience: Implementation of the Lazy Loading pattern in the Inference API to handle cold starts or temporary model unavailability gracefully.

## 🚀 Quick Start

### Prerequisites

Docker and Docker Compose installed.

Dataset: Download one of the "Yellow Taxi Trip Records" files (Parquet format) from the official NYC TLC website, rename it to taxi_data.parquet, and place it in the data/ folder.

### Launch

Start the entire infrastructure with a single command:

```
docker-compose up -d --build
```

This command will build and start the following services:

- Zookeeper
- Kafka Broker
- Kafka UI (for monitoring streams)
- Data Producer (sends taxi trip data to Kafka)
- Training Service (consumes data, trains models, logs to MLflow)
- Inference API (serves predictions via FastAPI)
- MLflow Tracking Server (for experiment tracking and model registry)
- MLflow UI (for visualizing experiments and models)

Wait approximately 60-90 seconds for the Training Service to collect the first batch of data (default: 10,000 records) and generate the initial model.

### Dashboards & Monitoring

Kafka UI: http://localhost:8080 (Stream monitoring)

MLflow UI: http://localhost:5000 (MAE metrics & Models visualization)

API Documentation: http://localhost:8000/docs (Swagger UI)

### Test Prediction (Inference)

You can test the API directly via Swagger UI or using curl in your terminal:

JSON Request Example (JFK Airport -> Times Square):

```
{
"PULocationID": 132,
"DOLocationID": 230,
"trip_distance": 18.5
}
```

Expected Response:

```
{
"predicted_duration_minutes": 51.64, (approximate value)
"ride_details": { ... }
}
```

## 🛠️ Tech Stack

**Streaming**: Apache Kafka, Zookeeper

**ML & Data**: Scikit-Learn, Pandas, MLflow

**Backend**: FastAPI, Uvicorn, Pydantic

**Containerization**: Docker, Docker Compose

**Language**: Python 3.11
