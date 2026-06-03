# InsightFlow – Cloud-Native IoT Skin Analytics Pipeline

## Overview

InsightFlow is a cloud-native IoT analytics platform that simulates, processes, stores, and analyzes skincare sensor data using modern cloud technologies. The project demonstrates a complete end-to-end data engineering workflow, including data generation, validation, transformation, cloud storage, metadata cataloging, serverless analytics, and interactive dashboard visualization.

The platform is designed to showcase how organizations can manage large volumes of IoT-generated data efficiently using AWS services and modern deployment platforms.

---

## Features

### Data Generation

* Simulates IoT skincare sensor data.
* Generates realistic records containing:

  * Moisture Level
  * Sebum Level
  * Skin pH
  * Temperature
  * Humidity
  * Primary Skin Concern

### Data Validation

* Validates incoming records.
* Detects:

  * Missing fields
  * Invalid values
  * Incorrect data types
  * Data inconsistencies

### Data Transformation

* Converts raw sensor data into analytics-ready datasets.
* Applies business logic and categorization rules.

### Cloud Storage

* Stores data in AWS S3 buckets:

  * Raw Data Bucket
  * Processed Data Bucket
  * Athena Data Bucket
  * Query Results Bucket

### Metadata Management

* Uses AWS Glue Crawlers to automatically discover schemas and update metadata catalogs.

### Analytics

* Executes SQL queries directly on S3 data using AWS Athena.
* Enables serverless analytics without maintaining database servers.

### Dashboard Visualization

* Interactive frontend dashboard.
* Displays:

  * Primary Concern Distribution
  * Moisture Analysis
  * Sebum Analysis
  * Validation Results
  * Analytics Insights

---

## System Architecture

```text
Frontend (Vercel)
        │
        ▼
FastAPI Backend (Render)
        │
        ▼
Validation Layer
        │
        ▼
Transformation Layer
        │
        ▼
AWS S3 Data Lake
        │
        ▼
AWS Glue Crawler
        │
        ▼
AWS Athena
        │
        ▼
Analytics Dashboard
```

---

## Technology Stack

### Frontend

* HTML
* CSS
* JavaScript
* Chart.js

### Backend

* FastAPI
* Python

### Data Processing

* Pandas
* NumPy

### Cloud Services

* AWS S3
* AWS Glue
* AWS Athena
* AWS IAM

### Deployment

* Render (Backend)
* Vercel (Frontend)

### Version Control

* Git
* GitHub

---

## AWS Infrastructure

### S3 Buckets

| Bucket               | Purpose                           |
| -------------------- | --------------------------------- |
| Raw Bucket           | Stores generated raw sensor data  |
| Processed Bucket     | Stores transformed datasets       |
| Athena Bucket        | Stores Athena-compatible datasets |
| Query Results Bucket | Stores Athena query results       |

### AWS Glue

Used for:

* Schema discovery
* Metadata cataloging
* Table creation

### AWS Athena

Used for:

* Serverless SQL querying
* Data analytics
* Report generation

---

## Project Workflow

### Step 1: Generate Data

The system generates simulated skincare sensor data.

```text
Device Data
↓
Raw JSON Records
```

### Step 2: Validate Data

Validation engine checks:

* Required fields
* Data types
* Value ranges

### Step 3: Transform Data

Data is transformed into analytics-ready format.

### Step 4: Upload to S3

Processed datasets are uploaded to AWS S3.

### Step 5: Run Glue Crawler

Glue scans S3 data and updates the Data Catalog.

### Step 6: Query with Athena

Athena executes SQL queries on S3 datasets.

### Step 7: Visualize Results

Dashboard displays analytical insights.

---

## Application Areas

* Smart Skincare Analytics
* Healthcare Monitoring Systems
* Wearable Devices
* Wellness Applications
* Remote Monitoring Solutions
* Industrial IoT (IIoT)
* Smart Home Systems
* Telemetry Analytics Platforms

---

## Users

* Skincare and Cosmetic Companies
* Healthcare Professionals
* IoT Solution Providers
* Researchers and Data Analysts
* Wearable Device Manufacturers
* Cloud Engineers
* Data Engineers
* Students and Educators

---

## Project Scope

InsightFlow provides a scalable platform for collecting, validating, transforming, storing, and analyzing IoT-generated sensor data. The project demonstrates modern cloud-native data engineering concepts and can be extended to support real-time streaming, predictive analytics, machine learning models, and integration with actual IoT devices.

---

## Deployment

### Frontend

Hosted on:

* Vercel

### Backend

Hosted on:

* Render

### Cloud Services

Hosted on:

* AWS

---

## Future Enhancements

* Real-Time Data Streaming
* Machine Learning-Based Recommendations
* Predictive Analytics
* User Authentication
* Mobile Application Integration
* Real-Time Monitoring Dashboards
* Multi-Device Support
* Advanced Reporting and Export Features

---

## Learning Outcomes

This project demonstrates practical knowledge of:

* Cloud Computing
* Data Engineering
* ETL Pipelines
* FastAPI Development
* AWS S3
* AWS Glue
* AWS Athena
* Frontend Development
* Cloud Deployment
* Full-Stack Integration

---

## Author

**Ruchir Vyas**
B.E. Computer Science and Engineering (IoT-CS-BCT)
MVSR Engineering College

---

## License

This project is developed for academic and educational purposes as part of Industry Training and cloud-native data engineering practice.
