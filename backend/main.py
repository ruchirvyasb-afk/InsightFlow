"""
FastAPI backend for InsightFlow IoT Skin Analytics Pipeline
Complete pipeline:
Ingest → Validate → Transform → S3 → Glue → Athena
"""

import json
import statistics
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ==========================================
# LOCAL MODULES
# ==========================================

from config import (
    RAW_DATA_FILE,
    VALIDATION_LOG_FILE,
    TRANSFORMED_DATA_FILE,
    AWS_REGION,
    RAW_BUCKET,
    PROCESSED_BUCKET,
    QUERY_RESULTS_BUCKET,
    GLUE_CRAWLER_NAME,
    ATHENA_DATABASE
)

from generate import generate_data
from ingestion import ingest_data
from validation import validate_records, save_validation_log
from transform import transform_records, save_transformed_data

# ==========================================
# AWS MODULES
# ==========================================

from storage import save_to_data_lake

from athena import (
    execute_query,
    get_query_results,
    run_predefined_query
)

from crawler import (
    run_glue_crawler,
    get_crawler_status
)

# ==========================================
# FASTAPI APP
# ==========================================

app = FastAPI(
    title="InsightFlow API",
    version="1.0.0"
)

# ==========================================
# CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# RESPONSE MODELS
# ==========================================

class PipelineResponse(BaseModel):

    status: str
    message: str

    raw_count: int
    valid_count: int
    invalid_count: int
    transformed_count: int

    raw_records: List[Dict[str, Any]]

    validation_summary: Dict[str, Any]

    transformed_records: List[Dict[str, Any]]

class QueryResponse(BaseModel):

    status: str

    query_id: Optional[str]

    results: Optional[List[Dict[str, Any]]]

    message: str

# ==========================================
# KPI CALCULATOR
# ==========================================

def calculate_dashboard_kpis(transformed_records: List[Dict]) -> Dict:

    if not transformed_records:

        return {
            "valid_records": 0,
            "avg_moisture": 0,
            "avg_sebum": 0,
            "avg_ph": 0,
            "treatment_rate": 0,
            "unique_devices": 0,
            "skin_state_breakdown": {},
            "primary_concern_breakdown": {},
            "top_products": []
        }

    moisture_vals = [
        r.get("skin_moisture_pct", 0)
        for r in transformed_records
        if r.get("skin_moisture_pct") is not None
    ]

    sebum_vals = [
        r.get("sebum_level_index", 0)
        for r in transformed_records
        if r.get("sebum_level_index") is not None
    ]

    ph_vals = [
        r.get("skin_ph", 0)
        for r in transformed_records
        if r.get("skin_ph") is not None
    ]

    skin_state_breakdown = {}
    concern_breakdown = {}
    product_count = {}

    for record in transformed_records:

        state = record.get("skin_state", "Unknown")
        concern = record.get("primary_concern", "Unknown")
        product = record.get("suggested_product", "Unknown")

        skin_state_breakdown[state] = (
            skin_state_breakdown.get(state, 0) + 1
        )

        concern_breakdown[concern] = (
            concern_breakdown.get(concern, 0) + 1
        )

        product_count[product] = (
            product_count.get(product, 0) + 1
        )

    top_products = sorted(
        product_count.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

    treatment_count = sum(
        1 for r in transformed_records
        if r.get("routine_step") == "Treatment"
    )

    treatment_rate = (
        treatment_count / len(transformed_records) * 100
    )

    unique_devices = len(
        set(r.get("device_id") for r in transformed_records)
    )

    return {
        "valid_records": len(transformed_records),

        "avg_moisture": round(
            statistics.mean(moisture_vals), 2
        ) if moisture_vals else 0,

        "avg_sebum": round(
            statistics.mean(sebum_vals), 2
        ) if sebum_vals else 0,

        "avg_ph": round(
            statistics.mean(ph_vals), 2
        ) if ph_vals else 0,

        "treatment_rate": round(
            treatment_rate, 2
        ),

        "unique_devices": unique_devices,

        "skin_state_breakdown": skin_state_breakdown,

        "primary_concern_breakdown": concern_breakdown,

        "top_products": top_products
    }

# ==========================================
# ROOT
# ==========================================

@app.get("/")
async def root():

    return {
        "status": "ok",
        "message": "InsightFlow API is running",
        "version": "1.0.0"
    }

# ==========================================
# HEALTH CHECK
# ==========================================

@app.get("/health")
async def health():

    return {
        "status": "ok",
        "message": "InsightFlow API is running",

        "aws_region": AWS_REGION,

        "raw_bucket": RAW_BUCKET,

        "processed_bucket": PROCESSED_BUCKET,

        "query_results_bucket": QUERY_RESULTS_BUCKET,

        "glue_crawler": GLUE_CRAWLER_NAME,

        "athena_database": ATHENA_DATABASE
    }

# ==========================================
# PIPELINE
# ==========================================

@app.post("/api/generate-data")
async def generate_and_process():

    try:

        fault_summary, records = generate_data()

        raw_records = ingest_data()

        valid_records, invalid_records = validate_records(raw_records)

        save_validation_log(
            valid_records,
            invalid_records
        )

        transformed_records = transform_records(valid_records)

        save_transformed_data(transformed_records)

        try:

            with open(VALIDATION_LOG_FILE, "r") as f:

                validation_summary = json.load(f)

        except Exception:

            validation_summary = {
                "valid_count": len(valid_records),
                "invalid_count": len(invalid_records),
                "total": len(valid_records) + len(invalid_records)
            }

        return PipelineResponse(
            status="success",

            message="Pipeline completed successfully",

            raw_count=len(raw_records),

            valid_count=len(valid_records),

            invalid_count=len(invalid_records),

            transformed_count=len(transformed_records),

            raw_records=raw_records[:10],

            validation_summary=validation_summary,

            transformed_records=transformed_records[:10]
        )

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }

# ==========================================
# DASHBOARD KPI
# ==========================================

@app.get("/api/dashboard/kpis")
async def get_dashboard_kpis():

    try:

        if not TRANSFORMED_DATA_FILE.exists():

            return {
                "status": "no_data",
                "kpis": {}
            }

        with open(TRANSFORMED_DATA_FILE, "r") as f:

            transformed_records = json.load(f)

        kpis = calculate_dashboard_kpis(transformed_records)

        return {
            "status": "success",
            "kpis": kpis
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }

# ==========================================
# S3 UPLOAD
# ==========================================

@app.post("/api/s3/upload")
async def upload_to_s3():

    try:

        with open(TRANSFORMED_DATA_FILE, "r") as f:

            records = json.load(f)

        result = save_to_data_lake(records)

        return result

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }

# ==========================================
# GLUE CRAWLER
# ==========================================

@app.post("/api/crawler/run")
async def run_crawler():

    try:

        return run_glue_crawler()

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/api/crawler/status")
async def crawler_status():

    try:

        return get_crawler_status()

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }

# ==========================================
# ATHENA QUERY
# ==========================================

@app.post("/api/query")
async def run_query(sql: str = Query(...)):

    try:

        exec_result = execute_query(sql)

        if exec_result.get("status") != "success":

            return exec_result

        query_id = exec_result.get("query_id")

        results = get_query_results(query_id)

        return {
            "status": "success",
            "query_id": query_id,
            "results": results.get("data", [])
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }

# ==========================================
# PREDEFINED ATHENA QUERIES
# ==========================================

@app.get("/api/query/predefined")
async def predefined_query(query_name: str):

    try:

        return run_predefined_query(query_name)

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }

# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )