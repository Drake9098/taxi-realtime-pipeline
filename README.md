# 🚕 Taxi Real-Time Pipeline (MLOps)

This is an **end-to-end MLOps project** implementing a real-time streaming pipeline for ML predictions on taxi data.

## 📋 Project Status

🚧 **Current Status:** Phase 1 Complete (Data Ingestion & Infrastructure)

- [x] Kafka Infrastructure Setup
- [x] Data Ingestion Producer (Python + Docker)
- [x] Model Training Service (In Progress)
- [ ] Inference API (Planned)

## 🏗️ Repository Structure

```
taxi-realtime-pipeline/
│
├── producer/                  # 📡 Kafka Producer Service
│   ├── app.py                # Script to send data to Kafka
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile            # Producer container
│
├── training/                  # 🎓 ML Training Service (🚧 Work in Progress)
│   ├── train.py              # Model training script
│   ├── feature_engineering.py # Feature engineering pipeline
│   ├── requirements.txt      # Training dependencies
│   └── Dockerfile            # Training container
│
├── inference/                 # 🚀 API Service (🚧 Work in Progress)
│   ├── main.py               # FastAPI app for model serving
│   ├── requirements.txt      # Inference dependencies
│   └── Dockerfile            # API container
│
├── data/                      # 💾 Local data (Excluded from Git)
│   └── .gitkeep              # Keeps folder in repo
│
├── docker-compose.yml         # 🐳 Complete orchestration
├── .gitignore                 # 🛡️ Protection from unwanted commits
└── README.md                  # 📖 Documentation
```

## 🎯 Architecture Rationale

**Separation of Concerns:**
Each service (producer, training, inference) is completely isolated with separate dependencies, Dockerfile, and runtime. This enables independent deployments, horizontal scalability, and isolated testing.

**Reproducibility:**
Docker ensures consistent environments across different machines and stages (dev, staging, production).

## 🚀 Quick Start

### 1. Prerequisites

- **Docker** installed
- **Dataset**: Download one of the "Yellow Taxi Trip Records" (Parquet format) from the [official NYC TLC website](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)
  - Rename the file to `taxi_data.parquet`
  - Place it in the `data/` folder

### 2. Launch

```bash
# Start the entire infrastructure
docker-compose up -d --build
```

### 3. Access Services

- **Kafka UI**: [http://localhost:8080](http://localhost:8080) (Monitor data streaming)
- **MLflow UI**: [http://localhost:5000](http://localhost:5000) (Track experiments - Coming Soon)
- **Inference API**: [http://localhost:8000/docs](http://localhost:8000/docs) (Model predictions - Planned)

## 🛠️ Tech Stack

- **Streaming:** Apache Kafka + Zookeeper
- **Infrastructure:** Docker + Docker Compose
- **Language:** Python 3.9
- **Libraries:** kafka-python, pandas, (Planned: scikit-learn, MLflow, FastAPI)

---
