"""
S3 Data Lake Storage
Converts cleaned JSON to Parquet and uploads to S3 bucket
"""
import json
import pandas as pd
import boto3
from config import TRANSFORMED_DATA_FILE, BASE_DIR
from datetime import datetime

# AWS S3 Configuration
S3_BUCKET_RAW = "insightflow-raw-ruchir"  # Change to your bucket name
S3_BUCKET_PROCESSED = "insightflow-processed-ruchir"  # Change to your bucket name
S3_PREFIX_RAW = "raw/"
S3_PREFIX_PROCESSED = "processed/"

s3_client = boto3.client('s3')


def load_transformed_data():
    """Load transformed JSON data from file"""
    try:
        with open(TRANSFORMED_DATA_FILE, 'r') as f:
            records = json.load(f)
        return records
    except FileNotFoundError:
        print(f"❌ Transformed data file not found: {TRANSFORMED_DATA_FILE}")
        return []


def convert_to_parquet(records):
    """Convert JSON records to Parquet format"""
    if not records:
        print("⚠️  No records to convert")
        return None
    
    df = pd.DataFrame(records)
    
    # Add partition columns for Athena
    df['load_date'] = datetime.now().strftime('%Y-%m-%d')
    df['load_hour'] = datetime.now().strftime('%H')
    
    return df


def upload_to_s3(df, bucket_name, s3_prefix, filename):
    """Upload Parquet file to S3"""
    try:
        # Convert DataFrame to Parquet in memory
        parquet_key = f"{s3_prefix}{filename}"
        
        # Write to S3
        df.to_parquet(
            f"s3://{bucket_name}/{parquet_key}",
            engine='pyarrow',
            compression='snappy',
            index=False
        )
        
        print(f"✅ Uploaded to S3: s3://{bucket_name}/{parquet_key}")
        return parquet_key
    except Exception as e:
        print(f"❌ S3 upload failed: {e}")
        return None


def save_to_data_lake(records):
    """Main: Convert transformed data to Parquet and upload to S3"""
    print("\n📦 Starting S3 Data Lake Upload...")
    
    # Convert to Parquet
    df = convert_to_parquet(records)
    if df is None:
        return {"status": "error", "message": "Failed to convert data to Parquet"}
    
    print(f"📊 DataFrame shape: {df.shape[0]} rows × {df.shape[1]} columns")
    
    # Upload processed Parquet
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    processed_filename = f"skin_events_{timestamp}.parquet"
    
    try:
        upload_to_s3(df, S3_BUCKET_PROCESSED, S3_PREFIX_PROCESSED, processed_filename)
        
        return {
            "status": "success",
            "message": "Data uploaded to S3 successfully",
            "bucket": S3_BUCKET_PROCESSED,
            "key": f"{S3_PREFIX_PROCESSED}{processed_filename}",
            "rows": len(df),
            "columns": list(df.columns)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    records = load_transformed_data()
    result = save_to_data_lake(records)
    print(json.dumps(result, indent=2))
