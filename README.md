# Clinical Trials API

A FastAPI application that searches and extracts clinical trial data from ClinicalTrials.gov and stores it in a PostgreSQL database.

## Features

- Search clinical trials by query (e.g., "Effects of CagriSema in People Living With Diseases in the Heart and Blood Vessels")
- Extract detailed trial information including eligibility criteria, outcomes, locations, and interventions
- Store data in PostgreSQL database with proper normalization
- RESTful API with automatic documentation
- Error handling and validation

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Database Setup

Create a PostgreSQL database named `clinicai` with user `clinicai` and password `12345678`:

```sql
CREATE DATABASE clinicai;
CREATE USER clinicai WITH PASSWORD '12345678';
GRANT ALL PRIVILEGES ON DATABASE clinicai TO clinicai;
```

### 3. Create Database Tables

Run the following SQL to create the required tables:

```sql
-- Basic trial information
CREATE TABLE trial_basic_info (
    nct_id VARCHAR(20) PRIMARY KEY,
    org_study_id VARCHAR(100),
    organization VARCHAR(500),
    sponsor_type VARCHAR(100),
    brief_title TEXT,
    official_title TEXT,
    overall_status VARCHAR(100),
    status_verified_date DATE,
    start_date DATE,
    completion_date DATE,
    enrollment_count INTEGER,
    study_type VARCHAR(100),
    phase VARCHAR(50),
    allocation VARCHAR(100),
    masking VARCHAR(100),
    fda_regulated_drug BOOLEAN,
    fda_regulated_device BOOLEAN,
    dmc BOOLEAN,
    inclusion_criteria TEXT,
    exclusion_criteria TEXT,
    minimum_age VARCHAR(50),
    maximum_age VARCHAR(50),
    gender VARCHAR(50),
    healthy_volunteers VARCHAR(50),
    expanded_access_status VARCHAR(100)
);

-- Trial arms and interventions
CREATE TABLE trial_arms_interventions (
    id SERIAL PRIMARY KEY,
    nct_id VARCHAR(20) REFERENCES trial_basic_info(nct_id),
    intervention_type VARCHAR(50),
    arm_group_label VARCHAR(200),
    intervention_description TEXT,
    intervention_name TEXT
);

-- Trial outcomes
CREATE TABLE trial_outcomes (
    id SERIAL PRIMARY KEY,
    nct_id VARCHAR(20) REFERENCES trial_basic_info(nct_id),
    outcome_type VARCHAR(50),
    measure TEXT,
    time_frame VARCHAR(200),
    description TEXT
);

-- Trial locations
CREATE TABLE trial_locations (
    id SERIAL PRIMARY KEY,
    nct_id VARCHAR(20) REFERENCES trial_basic_info(nct_id),
    facility_name VARCHAR(500),
    city VARCHAR(100),
    state VARCHAR(100),
    zip VARCHAR(20),
    country VARCHAR(100),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8)
);
```

### 4. Run the Application

```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### 1. Search and Extract Trials
**POST** `/search-trials`

Search for clinical trials and extract their details.

**Request Body:**
```json
{
    "query": "Effects of CagriSema in People Living With Diseases in the Heart and Blood Vessels",
    "max_results": 10
}
```

**Response:**
```json
[
    {
        "nct_id": "NCT12345678",
        "brief_title": "Study Title",
        "official_title": "Official Study Title",
        "status": "Recruiting",
        "phase": "Phase 2",
        "study_type": "Interventional",
        "enrollment_count": 100,
        "start_date": "2024-01-01",
        "completion_date": "2025-12-31",
        "organization": "Study Organization",
        "inclusion_criteria": "Inclusion criteria text...",
        "exclusion_criteria": "Exclusion criteria text..."
    }
]
```

### 2. Get Trial by NCT ID
**GET** `/trial/{nct_id}`

Get details of a specific trial by its NCT ID.

### 3. API Documentation
**GET** `/docs`

Interactive API documentation (Swagger UI)

**GET** `/redoc`

Alternative API documentation

## Example Usage

```bash
# Search for trials
curl -X POST "http://localhost:8000/search-trials" \
     -H "Content-Type: application/json" \
     -d '{"query": "diabetes type 2", "max_results": 5}'

# Get specific trial
curl "http://localhost:8000/trial/NCT06383871"
```

## Error Handling

- **400 Bad Request**: When search returns more than 100 results
- **404 Not Found**: When no trials are found for the query
- **500 Internal Server Error**: For database or server errors

## Database Schema

The application stores trial data in four normalized tables:
- `trial_basic_info`: Core trial information
- `trial_arms_interventions`: Study arms and interventions
- `trial_outcomes`: Primary and secondary outcomes
- `trial_locations`: Trial locations with geographic data

