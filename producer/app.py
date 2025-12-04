from kafka import KafkaProducer
import json
import time
import pandas as pd
import os

def create_producer(bootstrap_servers):
    """
    Creates and returns a Kafka producer with JSON serialization.
    Retries until successful connection.
    
    :param bootstrap_servers: List of Kafka bootstrap servers.
    :return: KafkaProducer instance.
    """
    producer = None

    while producer is None:
        try:
            producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            print("Kafka producer created successfully.")
        except Exception as e:
            print(f"Error creating Kafka producer: {e}. Retrying in 5 seconds...")
            time.sleep(5)
    
    return producer

def load_data(filepath):
    """
    Uses pandas to load data from a Parquet file.
    Converts datetime columns to strings and fills NaN values with 0 for Kafka compatibility.
    
    :param filepath: Path to the Parquet file.
    :return: DataFrame with loaded and processed data.
    """
    df = pd.read_parquet(filepath)
    initial_len = len(df)
    
    # Data cleaning:
    critical_columns = ['tpep_pickup_datetime', 'tpep_dropoff_datetime', 'PULocationID', 'DOLocationID']
    df = df.dropna(subset=critical_columns)
    
    df['tpep_pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'])
    df['tpep_dropoff_datetime'] = pd.to_datetime(df['tpep_dropoff_datetime'])
    
    df = df.sort_values(by='tpep_pickup_datetime')
    
    df['passenger_count'] = df['passenger_count'].fillna(1).astype(int) 
    df['RatecodeID'] = df['RatecodeID'].fillna(99).astype(int)
    
    df['fare_amount'] = df['fare_amount'].fillna(0.0)
    df['total_amount'] = df['total_amount'].fillna(df['fare_amount'])
    df = df[(df['fare_amount'] > 0) & (df['total_amount'] > 0)]
    
    df['trip_distance'] = df['trip_distance'].fillna(0.0)
    df['tip_amount'] = df['tip_amount'].fillna(0.0)
    df['tolls_amount'] = df['tolls_amount'].fillna(0.0)
    
    if 'extra' in df.columns:
        df['extra'] = df['extra'].fillna(0.0)
    
    df['PULocationID'] = df['PULocationID'].astype(int)
    df['DOLocationID'] = df['DOLocationID'].astype(int)
    
    df['tpep_pickup_datetime'] = df['tpep_pickup_datetime'].astype(str)
    df['tpep_dropoff_datetime'] = df['tpep_dropoff_datetime'].astype(str)
    
    print(f"Clean data: {len(df)} rows (removed {initial_len - len(df)} dirty rows).")
    
    return df

if __name__ == "__main__":
    bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    data_path = os.getenv('DATA_PATH', '../data/taxi_data.parquet')

    print(f"🔧 Configuration: Server={bootstrap_servers}, File={data_path}")

    print("Creating Kafka producer")
    producer = create_producer([bootstrap_servers])

    print("Loading data")
    df = load_data(data_path)

    print("Initiating data stream to Kafka topic 'taxi-rides'")
    
    records = df.to_dict(orient='records')

    total_records = len(records)
    sent_count = 0
    
    try:
        for record in records:
            future = producer.send('taxi-rides', value=record)
            sent_count += 1

            if sent_count % 1000 == 0:
                try:
                    future.get(timeout=10)
                    print(f"Confirmed delivery of {sent_count}/{total_records} messages.")
                    producer.flush()
                except Exception as e:
                    print(f"Error confirming message delivery at record {sent_count}: {e}")
            
            if sent_count % 100 == 0:
                print(f"🚕 Sending: {sent_count}/{total_records} | Last: {record['tpep_pickup_datetime']}")
            
            # Simulate a delay to mimic real-time data streaming
            time.sleep(0.01)
        
    except KeyboardInterrupt:
        print("Data streaming interrupted.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        producer.flush()
        producer.close()
        print("Producer flushed and closed correctly.")