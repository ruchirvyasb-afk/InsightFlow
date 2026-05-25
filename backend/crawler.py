"""
AWS Glue Crawler
Catalogs Parquet files in S3
Automatically updates Athena schema
"""

import json
import os
import boto3
from botocore.exceptions import ClientError

# ==========================================
# AWS CONFIGURATION
# ==========================================

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

# Glue Database
GLUE_DATABASE = os.getenv("ATHENA_DATABASE", "insightflow_db")

# Your crawler name
GLUE_CRAWLER_NAME = os.getenv(
    "GLUE_CRAWLER_NAME",
    "skin_events_data"
)

# Processed S3 bucket
PROCESSED_BUCKET = os.getenv("PROCESSED_BUCKET")

# S3 parquet path
S3_TARGET_PATH = f"s3://{PROCESSED_BUCKET}/"

# Glue IAM Role ARN
GLUE_ROLE_ARN = os.getenv("GLUE_ROLE_ARN")

# Athena table name
GLUE_TABLE_NAME = "skin_events"

# ==========================================
# BOTO3 CLIENT
# ==========================================

glue_client = boto3.client(
    "glue",
    region_name=AWS_REGION
)

# ==========================================
# CREATE GLUE DATABASE
# ==========================================

def create_glue_database():

    try:

        glue_client.create_database(
            DatabaseInput={
                "Name": GLUE_DATABASE,
                "Description": "InsightFlow IoT Analytics Data Lake"
            }
        )

        print(f"✅ Created database: {GLUE_DATABASE}")

        return True

    except ClientError as e:

        if e.response["Error"]["Code"] == "AlreadyExistsException":

            print(f"ℹ️ Database already exists: {GLUE_DATABASE}")

            return True

        else:

            print(f"❌ Failed to create database: {e}")

            return False

# ==========================================
# CREATE GLUE CRAWLER
# ==========================================

def create_glue_crawler():

    try:

        if not PROCESSED_BUCKET:

            return {
                "status": "error",
                "message": "PROCESSED_BUCKET environment variable not set"
            }

        if not GLUE_ROLE_ARN:

            return {
                "status": "error",
                "message": "GLUE_ROLE_ARN environment variable not set"
            }

        print(f"🔍 Scanning path: {S3_TARGET_PATH}")

        glue_client.create_crawler(

            Name=GLUE_CRAWLER_NAME,

            Role=GLUE_ROLE_ARN,

            DatabaseName=GLUE_DATABASE,

            Targets={
                "S3Targets": [
                    {
                        "Path": S3_TARGET_PATH,
                        "Exclusions": []
                    }
                ]
            },

            SchemaChangePolicy={
                "UpdateBehavior": "UPDATE_IN_DATABASE",
                "DeleteBehavior": "LOG"
            },

            TablePrefix="",

            Description="InsightFlow Parquet Data Crawler"
        )

        print(f"✅ Created crawler: {GLUE_CRAWLER_NAME}")

        return {
            "status": "success",
            "message": f"Crawler {GLUE_CRAWLER_NAME} created successfully"
        }

    except ClientError as e:

        if e.response["Error"]["Code"] == "CrawlerAlreadyExistsException":

            print(f"ℹ️ Crawler already exists: {GLUE_CRAWLER_NAME}")

            return {
                "status": "success",
                "message": "Crawler already exists"
            }

        else:

            print(f"❌ Failed to create crawler: {e}")

            return {
                "status": "error",
                "message": str(e)
            }

# ==========================================
# RUN GLUE CRAWLER
# ==========================================

def run_glue_crawler():

    try:

        glue_client.start_crawler(
            Name=GLUE_CRAWLER_NAME
        )

        print(f"✅ Started crawler: {GLUE_CRAWLER_NAME}")

        return {
            "status": "success",
            "message": f"Crawler {GLUE_CRAWLER_NAME} started successfully",
            "crawler_name": GLUE_CRAWLER_NAME,
            "database": GLUE_DATABASE,
            "s3_path": S3_TARGET_PATH,
            "note": "Crawler usually finishes in 2-5 minutes"
        }

    except ClientError as e:

        if "CrawlerRunningException" in str(e):

            return {
                "status": "info",
                "message": "Crawler already running"
            }

        return {
            "status": "error",
            "message": str(e)
        }

# ==========================================
# GET CRAWLER STATUS
# ==========================================

def get_crawler_status():

    try:

        response = glue_client.get_crawler(
            Name=GLUE_CRAWLER_NAME
        )

        crawler = response["Crawler"]

        return {
            "status": "success",
            "crawler_name": crawler["Name"],
            "state": crawler["State"],
            "database": crawler["DatabaseName"],
            "targets": crawler["Targets"]
        }

    except ClientError as e:

        return {
            "status": "error",
            "message": str(e)
        }

# ==========================================
# MAIN TEST
# ==========================================

if __name__ == "__main__":

    print("\n========== GLUE CRAWLER TEST ==========\n")

    create_glue_database()

    create_glue_crawler()

    result = run_glue_crawler()

    print(json.dumps(result, indent=2))
