"""
S3 Data Lake Storage
Converts cleaned JSON to Parquet and uploads to S3 bucket
"""

import json
import os
import pandas as pd
import boto3
from config import TRANSFORMED_DATA_FILE, BASE_DIR
from datetime import datetime

# ==============================
# AWS CONFIGURATION
# ==============================

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

RAW_BUCKET = os.getenv("RAW_BUCKET")
PROCESSED_BUCKET = os.getenv("PROCESSED_BUCKET")
ATHENA_BUCKET = os.getenv("ATHENA_BUCKET")
QUERY_RESULTS_BUCKET = os.getenv("QUERY_RESULTS_BUCKET")

S3_PREFIX_RAW = "raw/"
S3_PREFIX_PROCESSED = "processed/"

# ==============================
# AWS CLIENT
# ==============================

s3_client = boto3.client(
    's3',
    region_name=AWS_REGION
)

# ==============================
# LOAD TRANSFORMED DATA
# ==============================

def load_transformed_data():
    """Load transformed JSON data from file"""
    
    try:
        with open(TRANSFORMED_DATA_FILE, 'r') as f:
            records = json.load(f)

        print(f"✅ Loaded {len(records)} transformed records")
        return records

    except FileNotFoundError:
        print(f"❌ Transformed data file not found: {TRANSFORMED_DATA_FILE}")
        return []

    except Exception as e:
        print(f"❌ Failed to load transformed data: {e}")
        return []

# ==============================
# CONVERT TO PARQUET
# ==============================

def convert_to_parquet(records):
    """Convert JSON records to Parquet format"""

    if not records:
        print("⚠️ No records to convert")
        return None

    try:
        df = pd.DataFrame(records)

        # Add partition columns
        df['load_date'] = datetime.now().strftime('%Y-%m-%d')
        df['load_hour'] = datetime.now().strftime('%H')

        print(f"✅ DataFrame created: {df.shape}")

        return df

    except Exception as e:
        print(f"❌ Failed to create DataFrame: {e}")
        return None

# ==============================
# UPLOAD TO S3
# ==============================

def upload_to_s3(df, bucket_name, s3_prefix, filename):
    """Upload Parquet file to S3"""

    try:
        parquet_key = f"{s3_prefix}{filename}"

        # Save locally first
        local_file = f"/tmp/{filename}"

        df.to_parquet(
            local_file,
            engine='pyarrow',
            compression='snappy',
            index=False
        )

        # Upload file to S3
        s3_client.upload_file(
            local_file,
            bucket_name,
            parquet_key
        )

        print(f"✅ Uploaded to S3: s3://{bucket_name}/{parquet_key}")

        return parquet_key

    except Exception as e:
        print(f"❌ S3 upload failed: {e}")
        return None

# ==============================
# MAIN DATA LAKE FUNCTION
# ==============================

def save_to_data_lake(records):
    """Convert transformed data to Parquet and upload to S3"""

    print("\n📦 Starting S3 Data Lake Upload...")

    # Validate env vars
    if not PROCESSED_BUCKET:
        return {
            "status": "error",
            "message": "PROCESSED_BUCKET environment variable not set"
        }

    # Convert records
    df = convert_to_parquet(records)

    if df is None:
        return {
            "status": "error",
            "message": "Failed to convert data to Parquet"
        }

    print(f"📊 DataFrame shape: {df.shape[0]} rows × {df.shape[1]} columns")

    # Create filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    processed_filename = f"skin_events_{timestamp}.parquet"

    # Upload to processed bucket
    parquet_key = upload_to_s3(
        df,
        PROCESSED_BUCKET,
        S3_PREFIX_PROCESSED,
        processed_filename
    )

    if parquet_key is None:
        return {
            "status": "error",
            "message": "Failed to upload parquet file"
        }

    return {
        "status": "success",
        "message": "Data uploaded to S3 successfully",
        "bucket": PROCESSED_BUCKET,
        "key": parquet_key,
        "rows": len(df),
        "columns": list(df.columns)
    }

# ==============================
# TEST RUN
# ==============================

if __name__ == "__main__":

    records = load_transformed_data()

    result = save_to_data_lake(records)

    print(json.dumps(result, indent=2))