"""
AWS Glue Crawler - Catalogs Parquet files in S3
Automatically creates/updates table schema in Glue Catalog for Athena queries
"""
import json
import boto3
from botocore.exceptions import ClientError

# AWS Glue Configuration
GLUE_DATABASE = "insightflow_db"  # Change to your database name
GLUE_CRAWLER_NAME = "skin_events_crawler"
S3_BUCKET_PROCESSED = "insightflow-processed-lake"  # Change to your bucket name
S3_TARGET_PATH = f"s3://{S3_BUCKET_PROCESSED}/processed/"
GLUE_ROLE_ARN = "arn:aws:iam::YOUR_ACCOUNT_ID:role/GlueServiceRole"  # Update with your role ARN
GLUE_TABLE_NAME = "skin_events"

glue_client = boto3.client('glue')


def create_glue_database():
    """Create Glue database if it doesn't exist"""
    try:
        glue_client.create_database(
            DatabaseInput={
                'Name': GLUE_DATABASE,
                'Description': 'InsightFlow IoT Skin Analytics Data Lake'
            }
        )
        print(f"✅ Created Glue database: {GLUE_DATABASE}")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'AlreadyExistsException':
            print(f"ℹ️  Database already exists: {GLUE_DATABASE}")
            return True
        else:
            print(f"❌ Failed to create database: {e}")
            return False


def create_glue_crawler():
    """Create Glue Crawler if it doesn't exist"""
    try:
        glue_client.create_crawler(
            Name=GLUE_CRAWLER_NAME,
            Role=GLUE_ROLE_ARN,
            DatabaseName=GLUE_DATABASE,
            Targets={
                'S3Targets': [
                    {
                        'Path': S3_TARGET_PATH,
                        'Exclusions': []
                    }
                ]
            },
            SchemaChangePolicy={
                'UpdateBehavior': 'UPDATE_IN_DATABASE',
                'DeleteBehavior': 'LOG'
            },
            TablePrefix='',
            Description='Crawls Parquet files in processed layer and creates/updates Glue Catalog'
        )
        print(f"✅ Created Glue Crawler: {GLUE_CRAWLER_NAME}")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'CrawlerAlreadyExistsException':
            print(f"ℹ️  Crawler already exists: {GLUE_CRAWLER_NAME}")
            return True
        else:
            print(f"❌ Failed to create crawler: {e}")
            return False


def run_glue_crawler():
    """Trigger Glue Crawler to scan S3 and catalog Parquet files"""
    try:
        response = glue_client.start_crawler(Name=GLUE_CRAWLER_NAME)
        print(f"✅ Started Glue Crawler: {GLUE_CRAWLER_NAME}")
        print(f"   Crawler will scan: {S3_TARGET_PATH}")
        return {
            "status": "success",
            "message": f"Crawler {GLUE_CRAWLER_NAME} started",
            "crawler_name": GLUE_CRAWLER_NAME,
            "s3_path": S3_TARGET_PATH,
            "database": GLUE_DATABASE,
            "note": "Crawler typically completes in 2-5 minutes"
        }
    except ClientError as e:
        if 'CrawlerRunningException' in str(e):
            print(f"⚠️  Crawler is already running")
            return {"status": "info", "message": "Crawler is already running"}
        else:
            print(f"❌ Failed to run crawler: {e}")
            return {"status": "error", "message": str(e)}


def get_crawler_status():
    """Check current crawler status"""
    try:
        response = glue_client.get_crawler(Name=GLUE_CRAWLER_NAME)
        crawler = response['Crawler']
        
        return {
            "status": "success",
            "crawler_name": crawler['Name'],
            "state": crawler['State'],
            "last_crawl": crawler.get('LastCrawl', {}).get('Status', 'N/A'),
            "database": crawler.get('DatabaseName', 'N/A'),
            "s3_target": S3_TARGET_PATH
        }
    except ClientError as e:
        return {"status": "error", "message": f"Failed to get crawler status: {e}"}


def list_cataloged_tables():
    """List all tables in Glue database (after crawler runs)"""
    try:
        response = glue_client.get_tables(DatabaseName=GLUE_DATABASE)
        tables = response.get('TableList', [])
        
        table_list = [
            {
                "name": t['Name'],
                "location": t['StorageDescriptor']['Location'],
                "columns": len(t['StorageDescriptor']['Columns']),
                "format": t['StorageDescriptor']['SerdeInfo'].get('SerializationLibrary', 'N/A')
            }
            for t in tables
        ]
        
        return {
            "status": "success",
            "database": GLUE_DATABASE,
            "table_count": len(table_list),
            "tables": table_list
        }
    except ClientError as e:
        return {"status": "error", "message": str(e)}


def setup_and_run_crawler():
    """Full setup: Create database → Create crawler → Run crawler"""
    print("\n🔍 Setting up Glue Crawler for Data Cataloging...")
    
    # Step 1: Create database
    if not create_glue_database():
        return {"status": "error", "message": "Failed to create database"}
    
    # Step 2: Create crawler
    if not create_glue_crawler():
        return {"status": "error", "message": "Failed to create crawler"}
    
    # Step 3: Run crawler
    result = run_glue_crawler()
    return result


if __name__ == "__main__":
    result = setup_and_run_crawler()
    print(json.dumps(result, indent=2))
