"""
Amazon Athena Query Execution
Executes SQL queries directly against Parquet data in S3
Results stored in results S3 bucket
"""
import json
import time
import boto3
from botocore.exceptions import ClientError

# AWS Athena Configuration
ATHENA_DATABASE = "insightflow_db"  # Same as Glue database
ATHENA_RESULTS_BUCKET = "insightflow-query-results"  # Change to your query results bucket
ATHENA_RESULTS_PATH = f"s3://{ATHENA_RESULTS_BUCKET}/athena-results/"
ATHENA_WORKGROUP = "primary"  # Default workgroup; can create custom one

athena_client = boto3.client('athena')
s3_client = boto3.client('s3')


def execute_query(sql_query, max_retries=30):
    """Execute SQL query on Athena and wait for results"""
    try:
        # Submit query to Athena
        response = athena_client.start_query_execution(
            QueryString=sql_query,
            QueryExecutionContext={'Database': ATHENA_DATABASE},
            ResultConfiguration={'OutputLocation': ATHENA_RESULTS_PATH},
            WorkGroup=ATHENA_WORKGROUP
        )
        
        query_id = response['QueryExecutionId']
        print(f"🔍 Query submitted. Query ID: {query_id}")
        
        # Poll for query completion
        for attempt in range(max_retries):
            query_status = athena_client.get_query_execution(QueryExecutionId=query_id)
            status = query_status['QueryExecution']['Status']['State']
            
            if status == 'SUCCEEDED':
                print(f"✅ Query succeeded in {attempt + 1} attempts")
                return {
                    "status": "success",
                    "query_id": query_id,
                    "message": "Query executed successfully"
                }
            elif status == 'FAILED':
                failure_reason = query_status['QueryExecution']['Status'].get('StateChangeReason', 'Unknown')
                print(f"❌ Query failed: {failure_reason}")
                return {
                    "status": "error",
                    "query_id": query_id,
                    "error": failure_reason
                }
            elif status == 'CANCELLED':
                print(f"⚠️  Query was cancelled")
                return {
                    "status": "cancelled",
                    "query_id": query_id,
                    "message": "Query was cancelled"
                }
            
            # Wait before retrying
            time.sleep(1)
        
        return {
            "status": "timeout",
            "query_id": query_id,
            "message": "Query execution timeout"
        }
    
    except ClientError as e:
        print(f"❌ Athena query failed: {e}")
        return {"status": "error", "message": str(e)}


def get_query_results(query_id, max_rows=100):
    """Fetch results from completed Athena query"""
    try:
        response = athena_client.get_query_results(
            QueryExecutionId=query_id,
            MaxResults=max_rows
        )
        
        rows = response['ResultSet']['Rows']
        
        # Skip header row, extract data
        if len(rows) > 1:
            headers = [col['VarCharValue'] for col in rows[0]['Data']]
            data = []
            
            for row in rows[1:]:
                row_data = {}
                for idx, header in enumerate(headers):
                    value = row['Data'][idx].get('VarCharValue', None)
                    row_data[header] = value
                data.append(row_data)
            
            return {
                "status": "success",
                "query_id": query_id,
                "row_count": len(data),
                "columns": headers,
                "data": data
            }
        else:
            return {
                "status": "success",
                "query_id": query_id,
                "row_count": 0,
                "columns": [],
                "data": []
            }
    
    except ClientError as e:
        return {"status": "error", "message": str(e)}


def run_predefined_query(query_name):
    """Execute one of the predefined Athena queries"""
    
    queries = {
        "top_products": """
            SELECT suggested_product, COUNT(*) AS frequency
            FROM skin_events
            GROUP BY suggested_product
            ORDER BY frequency DESC
            LIMIT 20
        """,
        "avg_metrics_by_state": """
            SELECT skin_state,
                   AVG(CAST(skin_moisture_pct AS DOUBLE)) AS avg_moisture,
                   AVG(CAST(sebum_level_index AS DOUBLE)) AS avg_sebum,
                   AVG(CAST(skin_ph AS DOUBLE)) AS avg_ph
            FROM skin_events
            GROUP BY skin_state
        """,
        "dry_skin_alerts": """
            SELECT device_id, customer_id, skin_moisture_pct, dryness_index
            FROM skin_events
            WHERE skin_moisture_pct < 30
            ORDER BY skin_moisture_pct ASC
            LIMIT 50
        """,
        "concern_distribution": """
            SELECT primary_concern, COUNT(*) AS total
            FROM skin_events
            GROUP BY primary_concern
            ORDER BY total DESC
        """,
        "ambient_by_state": """
            SELECT skin_state,
                   AVG(CAST(ambient_temp_c AS DOUBLE)) AS avg_temp,
                   AVG(CAST(ambient_humidity_pct AS DOUBLE)) AS avg_humidity
            FROM skin_events
            GROUP BY skin_state
        """
    }
    
    if query_name not in queries:
        return {
            "status": "error",
            "message": f"Query not found. Available: {list(queries.keys())}"
        }
    
    sql = queries[query_name]
    print(f"\n🔍 Running predefined query: {query_name}")
    print(f"   SQL: {sql[:100]}...")
    
    result = execute_query(sql)
    
    if result['status'] == 'success':
        # Get results
        query_id = result['query_id']
        data = get_query_results(query_id)
        return data
    
    return result


def run_custom_query(sql_query):
    """Execute custom SQL query on Athena"""
    print(f"\n🔍 Running custom Athena query...")
    print(f"   SQL: {sql_query[:150]}...")
    
    result = execute_query(sql_query)
    
    if result['status'] == 'success':
        query_id = result['query_id']
        data = get_query_results(query_id)
        return data
    
    return result


if __name__ == "__main__":
    # Example: Run a predefined query
    result = run_predefined_query("top_products")
    print(json.dumps(result, indent=2))
