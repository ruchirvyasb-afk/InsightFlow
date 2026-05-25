"""
AWS Glue Crawler - Catalogs Parquet files in S3
Automatically creates/updates table schema in Glue Catalog for Athena queries
"""

import json
import boto3
from botocore.exceptions import ClientError

# =========================================================
# AWS CONFIGURATION
# =========================================================

# Change to ap-south-2 if using Hyderabad region
AWS_REGION = "ap-south-1"

# Glue Database
GLUE_DATABASE = "insightflow_db"

# Glue Crawler Name
GLUE_CRAWLER_NAME = "skin_events_data"

# Your processed S3 bucket
S3_BUCKET_PROCESSED = "insightflow-processed-ruchir"

# S3 parquet path
S3_TARGET_PATH = f"s3://{S3_BUCKET_PROCESSED}/"

# IMPORTANT:
# Replace with your actual Glue Role ARN
GLUE_ROLE_ARN = "arn:aws:iam::459640517326:role/InsightFlowGlueRole"

# Table name expected in Athena
GLUE_TABLE_NAME = "skin_events"

# =========================================================
# BOTO3 CLIENT
# =========================================================

glue_client = boto3.client(
    "glue",
    region_name=AWS_REGION
)

# =========================================================
# CREATE GLUE DATABASE
# =========================================================

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


# =========================================================
# CREATE GLUE CRAWLER
# =========================================================

def create_glue_crawler():

    try:

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

        return True

    except ClientError as e:

        if e.response["Error"]["Code"] == "CrawlerAlreadyExistsException":

            print(f"ℹ️ Crawler already exists: {GLUE_CRAWLER_NAME}")

            return True

        else:

            print(f"❌ Failed to create crawler: {e}")

            return False


# =========================================================
# RUN GLUE CRAWLER
# =========================================================

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

        else:

            return {
                "status": "error",
                "message": str(e)
            }


# =========================================================
# GET CRAWLER STATUS
# =========================================================

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
            "database": crawler["DatabaseName"]
        }

    except ClientError as e:

        return {
            "status": "error",
            "message": str(e)
        }


# =========================================================
# LIST GLUE TABLES
# =========================================================

def list_cataloged_tables():

    try:

        response = glue_client.get_tables(
            DatabaseName=GLUE_DATABASE
        )

        tables = response.get("TableList", [])

        table_list = []

        for table in tables:

            table_info = {
                "name": table["Name"],
                "location": table["StorageDescriptor"]["Location"],
                "columns": len(table["StorageDescriptor"]["Columns"])
            }

            table_list.append(table_info)

        return {
            "status": "success",
            "database": GLUE_DATABASE,
            "table_count": len(table_list),
            "tables": table_list
        }

    except ClientError as e:

        return {
            "status": "error",
            "message": str(e)
        }


# =========================================================
# COMPLETE SETUP FLOW
# =========================================================

def setup_and_run_crawler():

    print("\n🚀 Setting up Glue crawler...\n")

    # Step 1 → Create Database
    if not create_glue_database():

        return {
            "status": "error",
            "message": "Failed to create Glue database"
        }

    # Step 2 → Create Crawler
    if not create_glue_crawler():

        return {
            "status": "error",
            "message": "Failed to create crawler"
        }

    # Step 3 → Run Crawler
    result = run_glue_crawler()

    return result


# =========================================================
# MAIN EXECUTION
# =========================================================

if __name__ == "__main__":

    result = setup_and_run_crawler()

    print("\n📊 RESULT:\n")

    print(json.dumps(result, indent=2))
