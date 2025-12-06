from kafka import KafkaConsumer
import json
import os
import time
import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from mlflow.models import infer_signature


def create_consumer(bootstrap_servers, topic, group_id):
    """Creates and returns a Kafka consumer"""
    consumer = None

    while consumer is None:
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=bootstrap_servers,
                group_id=group_id,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            print("Kafka consumer created successfully.")
        except Exception as e:
            print(f"Error creating Kafka consumer: {e}. Retrying in 5 seconds...")
            time.sleep(5)

    return consumer


def process_data(batch_data):
    """Turns batch data (a list of dicts) into features and labels for training"""

    df = pd.DataFrame(batch_data)

    df['tpep_pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'])
    df['tpep_dropoff_datetime'] = pd.to_datetime(df['tpep_dropoff_datetime'])
    
    df['actual_duration'] = (df['tpep_dropoff_datetime'] - df['tpep_pickup_datetime']).dt.total_seconds() / 60
    
    df = df[(df['actual_duration'] > 1) & (df['actual_duration'] < 120)]
    
    features = ['PULocationID', 'DOLocationID', 'trip_distance']
    
    X = df[features].copy()
    
    # Float64 conversion for compatibility with MLflow
    X['PULocationID'] = X['PULocationID'].astype('float64')
    X['DOLocationID'] = X['DOLocationID'].astype('float64')
    X['trip_distance'] = X['trip_distance'].astype('float64')
    
    # Remove rows with missing PULocationID or DOLocationID and fill missing trip_distance with 0
    X = X.dropna(subset=['PULocationID', 'DOLocationID'])
    X['trip_distance'] = X['trip_distance'].fillna(0.0)
    
    target = 'actual_duration'
    
    # Align y with the cleaned X (necessary after dropping rows)
    y = df.loc[X.index, target]
    
    return X, y


def train_and_log(X, y):
    """
    Trains a Random Forest model and logs it to MLflow
    along with parameters and metrics.
    """
    print("🧠 Training model...")
    
    # MLflow setup
    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("taxi-demand-prediction")
    
    with mlflow.start_run():
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        
        # Model training using a Random Forest Regressor
        params = {"n_estimators": 10, "max_depth": 10}
        model = RandomForestRegressor(**params)
        
        model.fit(X_train, y_train)
        
        predictions = model.predict(X_test)
        mae = mean_absolute_error(y_test, predictions)
        print(f"📉 Model MAE: {mae:.2f} minutes")

        signature = infer_signature(X_train, predictions)

        input_example = X_train.iloc[:5]
        
        # Log parameters, metrics, and model to MLflow
        mlflow.log_params(params)
        mlflow.log_metric("mae", mae)
        mlflow.sklearn.log_model(sk_model=model, artifact_path="model", signature=signature, input_example=input_example)
        
        print("✅ Model saved to MLflow!")


if __name__ == "__main__":
    KAFKA_BROKER = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    TOPIC = 'taxi-rides'
    GROUP_ID = 'taxi-training-group'

    print("Configuration: Broker:", KAFKA_BROKER)
    
    print(f"🔧 Creating consumer for topic '{TOPIC}'...")
    consumer = create_consumer([KAFKA_BROKER], TOPIC, GROUP_ID)

    BATCH_SIZE = 1000
    batch_data = []
    
    print(f"🎧 Awaiting data for group {GROUP_ID} (Batch size: {BATCH_SIZE})...")
    
    try:
        for message in consumer:
            record = message.value

            batch_data.append(record)

            if len(batch_data) % 1000 == 0:
                print(f"📥 Received {len(batch_data)} records so far")
            
            if len(batch_data) >= BATCH_SIZE:
                print(f"🚀 Processing batch of {len(batch_data)} records")
                
                X, y = process_data(batch_data)
                
                if not X.empty:
                    train_and_log(X, y)
                else:
                    print("⚠️ No valid data to train on in this batch. Skipping.")

                print("✅ Batch processed. Clearing batch data.")
                batch_data = []  # Reset the batch after processing
            
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted")
    finally:
        consumer.close()
        print("✅ Consumer closed")