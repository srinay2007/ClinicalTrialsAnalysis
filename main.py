import requests
import psycopg2
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

# PostgreSQL connection setup
def connect_db():
    return psycopg2.connect(
        dbname="clinicai",
        user="clinicai",
        password="12345678",
        host="localhost",
        port="5432"
    )

# Pydantic models for API
class SearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = 10

class TrialResponse(BaseModel):
    nct_id: str
    brief_title: str
    official_title: str
    brief_summary: Optional[str]
    detailed_description: Optional[str]
    status: str
    phase: Optional[str]
    study_type: str
    enrollment_count: Optional[int]
    start_date: Optional[str]
    completion_date: Optional[str]
    organization: Optional[str]
    inclusion_criteria: Optional[str]
    exclusion_criteria: Optional[str]

# Initialize FastAPI app
app = FastAPI(title="Clinical Trials API", version="1.0.0")

# Serve static files
app.mount("/static", StaticFiles(directory="."), name="static")

from datetime import datetime

def parse_date(date_str):
    # Handles "YYYY-MM-DD" and "YYYY-MM" date formats, returns date or None
    if not date_str:
        return None
    try:
        if len(date_str) == 7:  # format: YYYY-MM
            return datetime.strptime(date_str, "%Y-%m").date()
        elif len(date_str) == 10:  # format: YYYY-MM-DD
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            return None
    except Exception:
        return None

def search_clinical_trials(query: str, max_results: int = 10):
    """Search for clinical trials using ClinicalTrials.gov API"""
    url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        "query.term": query,
        "pageSize": min(max_results, 100)  # API limit is 100
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            studies = data.get('studies', [])
            return [study.get('protocolSection', {}) for study in studies]
        else:
            print(f"Failed to search trials: HTTP {response.status_code}")
            return []
    except Exception as e:
        print(f"Error searching trials: {e}")
        return []

def get_clinical_trial_details(nct_id):
    url = f"https://clinicaltrials.gov/api/v2/studies/{nct_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('protocolSection', {})
    else:
        print(f"Failed to fetch data: HTTP {response.status_code}")
        return None

def safe_get(d, *keys, default=None):
    """Safely get nested dict keys; return default if not found."""
    for key in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(key, default)
    return d

def insert_basic_info(conn, trial):
    ident = trial.get('identificationModule', {})
    status = trial.get('statusModule', {})
    sponsor = trial.get('sponsorCollaboratorsModule', {})
    desc = trial.get('descriptionModule', {})
    design = trial.get('designModule', {})
    oversight = trial.get('oversightModule', {})
    eligibility = trial.get('eligibilityModule', {})

    criteria = eligibility.get('eligibilityCriteria')
    print("Type of criterea ",type(criteria))
    if isinstance(criteria, dict):
        full_criteria_text = criteria.get('textblock', '')
    else:
        full_criteria_text = criteria
    print("full_criteria_text:",full_criteria_text)

    # Basic text splitting
    inclusion_criteria = None
    exclusion_criteria = None
    if 'Exclusion Criteria' in full_criteria_text:
        parts = full_criteria_text.split('Exclusion Criteria', 1)
        inclusion_criteria = parts[0].replace('Inclusion Criteria:', '').strip()
        exclusion_criteria = parts[1].strip()
    elif full_criteria_text:
        inclusion_criteria = full_criteria_text.strip()

    print("inclusion_criteria=", inclusion_criteria, "exclusion_criteria=", exclusion_criteria)

    # Build the tuple of params
    params = (
        ident.get('nctId'),
        ident.get('orgStudyIdInfo', {}).get('id'),
        ident.get('organization', {}).get('fullName'),
        ident.get('organization', {}).get('class'),
        ident.get('briefTitle'),
        ident.get('officialTitle'),
        status.get('overallStatus'),
        parse_date(status.get('statusVerifiedDate')),
        parse_date(status.get('startDateStruct', {}).get('date')),
        parse_date(status.get('completionDateStruct', {}).get('date')),
        design.get('enrollmentInfo', {}).get('enrollmentCount'),
        design.get('studyType'),
        design.get('phase') or None,
        design.get('allocation') or None,
        design.get('masking') or None,
        oversight.get('isFdaRegulatedDrug'),
        oversight.get('isFdaRegulatedDevice'),
        oversight.get('isDataMonitoringCommittee'),
        inclusion_criteria,
        exclusion_criteria,
        eligibility.get('minimumAge'),
        eligibility.get('maximumAge'),
        eligibility.get('gender') or None,
        eligibility.get('healthyVolunteers'),
        status.get('expandedAccessStatus') or None,
    )

    # Replace empty strings with None
    params = tuple(None if (isinstance(p, str) and p.strip() == '') else p for p in params)

    print(f"Number of params: {len(params)}")
    for i, param in enumerate(params, 1):
        print(f"Param {i} (type {type(param)}): {repr(param)}")

    import pprint
    pprint.pprint(params)

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO trial_basic_info (
                nct_id, protocol_section_id, organization_name, organization_type, brief_title,
                official_title, status, phase, study_type,
                enrollment_count, enrollment_type, start_date, completion_date,
                primary_completion_date, is_fda_regulated_drug, is_fda_regulated_device,
                is_unapproved_device, is_ppsd, is_us_export
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (nct_id) DO UPDATE SET
                protocol_section_id = EXCLUDED.protocol_section_id,
                organization_name = EXCLUDED.organization_name,
                organization_type = EXCLUDED.organization_type,
                brief_title = EXCLUDED.brief_title,
                official_title = EXCLUDED.official_title,
                status = EXCLUDED.status,
                phase = EXCLUDED.phase,
                study_type = EXCLUDED.study_type,
                enrollment_count = EXCLUDED.enrollment_count,
                enrollment_type = EXCLUDED.enrollment_type,
                start_date = EXCLUDED.start_date,
                completion_date = EXCLUDED.completion_date,
                primary_completion_date = EXCLUDED.primary_completion_date,
                is_fda_regulated_drug = EXCLUDED.is_fda_regulated_drug,
                is_fda_regulated_device = EXCLUDED.is_fda_regulated_device,
                is_unapproved_device = EXCLUDED.is_unapproved_device,
                is_ppsd = EXCLUDED.is_ppsd,
                is_us_export = EXCLUDED.is_us_export,
                updated_at = CURRENT_TIMESTAMP
        """,  (
            ident.get('nctId'),
            ident.get('orgStudyIdInfo', {}).get('id'),
            ident.get('organization', {}).get('fullName'),
            ident.get('organization', {}).get('class'),
            ident.get('briefTitle'),
            ident.get('officialTitle'),
            status.get('overallStatus'),
            design.get('phase'),
            design.get('studyType'),
            design.get('enrollmentInfo', {}).get('enrollmentCount'),
            design.get('enrollmentInfo', {}).get('enrollmentType'),
            parse_date(status.get('startDateStruct', {}).get('date')),
            parse_date(status.get('completionDateStruct', {}).get('date')),
            parse_date(status.get('primaryCompletionDateStruct', {}).get('date')),
            oversight.get('isFdaRegulatedDrug'),
            oversight.get('isFdaRegulatedDevice'),
            oversight.get('isUnapprovedDevice'),
            oversight.get('isPpsd'),
            oversight.get('isUsExport')
        ))
        
        # Insert descriptions
        description = trial.get('descriptionModule', {})
        if description.get('briefSummary') or description.get('detailedDescription'):
            cur.execute("""
                INSERT INTO trial_descriptions (nct_id, brief_summary, detailed_description)
                VALUES (%s, %s, %s)
            """, (
                ident.get('nctId'),
                description.get('briefSummary'),
                description.get('detailedDescription')
            ))
        
        # Insert eligibility criteria
        if inclusion_criteria or exclusion_criteria:
            cur.execute("""
                INSERT INTO trial_eligibility (
                    nct_id, inclusion_criteria, exclusion_criteria,
                    minimum_age, maximum_age, gender, healthy_volunteers
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                ident.get('nctId'),
                inclusion_criteria,
                exclusion_criteria,
                eligibility.get('minimumAge'),
                eligibility.get('maximumAge'),
                eligibility.get('gender'),
                eligibility.get('healthyVolunteers')
            ))

def insert_arms_interventions(conn, trial):
    ai = trial.get('armsInterventionsModule', {})
    nct_id = trial.get('identificationModule', {}).get('nctId')

    with conn.cursor() as cur:
        for arm in ai.get('armGroups', []):
            cur.execute("""
                INSERT INTO trial_arms_interventions (nct_id, intervention_type , arm_group_label, intervention_description, intervention_name)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                nct_id,
                'Arm Group',
                arm.get('label'),
                arm.get('description', ''),
                "; ".join(arm.get('interventionNames', []))
            ))
        for intervention in ai.get('interventions', []):
            cur.execute("""
                INSERT INTO trial_arms_interventions (nct_id, intervention_type, arm_group_label, intervention_description, intervention_name)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                nct_id,
                'Intervention',
                intervention.get('name'),
                intervention.get('description', ''),
                "; ".join(intervention.get('armGroupLabels', []))
            ))

def insert_outcomes(conn, trial):
    outcomes = trial.get('outcomesModule', {})
    nct_id = trial.get('identificationModule', {}).get('nctId')

    with conn.cursor() as cur:
        for po in outcomes.get('primaryOutcomes', []):
            cur.execute("""
                INSERT INTO trial_outcomes (nct_id, outcome_type, outcome_measure, outcome_time_frame, outcome_description)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                nct_id,
                'Primary',
                po.get('measure'),
                po.get('timeFrame'),
                po.get('description', '')
            ))
        for so in outcomes.get('secondaryOutcomes', []):
            cur.execute("""
                INSERT INTO trial_outcomes (nct_id, outcome_type, outcome_measure, outcome_time_frame, outcome_description)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                nct_id,
                'Secondary',
                so.get('measure'),
                so.get('timeFrame'),
                so.get('description', '')
            ))

def insert_locations(conn, trial):
    locations = trial.get('contactsLocationsModule', {}).get('locations', [])
    nct_id = trial.get('identificationModule', {}).get('nctId')

    with conn.cursor() as cur:
        for loc in locations:
            geo = loc.get('geoPoint', {})
            cur.execute("""
                INSERT INTO trial_locations (
                    nct_id, facility_name, facility_city, facility_state, facility_zip, facility_country
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                nct_id,
                loc.get('facility'),
                loc.get('city'),
                loc.get('state'),
                loc.get('zip'),
                loc.get('country')
            ))

# FastAPI Endpoints
@app.get("/")
async def root():
    return FileResponse("index.html")

@app.get("/api")
async def api_info():
    return {"message": "Clinical Trials API", "version": "1.0.0"}

@app.post("/search-trials", response_model=List[TrialResponse])
async def search_and_extract_trials(request: SearchRequest):
    """Search for clinical trials and extract their details"""
    try:
        # Search for trials
        trials = search_clinical_trials(request.query, request.max_results)
        
        if not trials:
            raise HTTPException(status_code=404, detail="No trials found for the given query")
        
        if len(trials) > 100:
            raise HTTPException(
                status_code=400, 
                detail="Number of retrieved rows > 100. You have exceeded limits. Narrow your search criteria"
            )
        
        # Extract and store trial data
        extracted_trials = []
        conn = connect_db()
        
        try:
            for trial in trials:
                # Store in database
                insert_basic_info(conn, trial)
                insert_arms_interventions(conn, trial)
                insert_outcomes(conn, trial)
                insert_locations(conn, trial)
                
                # Prepare response data
                ident = trial.get('identificationModule', {})
                status = trial.get('statusModule', {})
                design = trial.get('designModule', {})
                eligibility = trial.get('eligibilityModule', {})
                description = trial.get('descriptionModule', {})
                
                
                # Parse criteria
                criteria = eligibility.get('eligibilityCriteria')
                if isinstance(criteria, dict):
                    full_criteria_text = criteria.get('textblock', '')
                else:
                    full_criteria_text = criteria or ''
                
                inclusion_criteria = None
                exclusion_criteria = None
                if 'Exclusion Criteria' in full_criteria_text:
                    parts = full_criteria_text.split('Exclusion Criteria', 1)
                    inclusion_criteria = parts[0].replace('Inclusion Criteria:', '').strip()
                    exclusion_criteria = parts[1].strip()
                elif full_criteria_text:
                    inclusion_criteria = full_criteria_text.strip()
                
                trial_response = TrialResponse(
                    nct_id=ident.get('nctId', ''),
                    brief_title=ident.get('briefTitle', ''),
                    official_title=ident.get('officialTitle', ''),
                    brief_summary=description.get('briefSummary'),
                    detailed_description=description.get('detailedDescription'),
                    status=status.get('overallStatus', ''),
                    phase=design.get('phase'),
                    study_type=design.get('studyType', ''),
                    enrollment_count=design.get('enrollmentInfo', {}).get('enrollmentCount'),
                    start_date=str(parse_date(status.get('startDateStruct', {}).get('date'))) if parse_date(status.get('startDateStruct', {}).get('date')) else None,
                    completion_date=str(parse_date(status.get('completionDateStruct', {}).get('date'))) if parse_date(status.get('completionDateStruct', {}).get('date')) else None,
                    organization=ident.get('organization', {}).get('fullName'),
                    inclusion_criteria=inclusion_criteria,
                    exclusion_criteria=exclusion_criteria
                )
                extracted_trials.append(trial_response)
            
            conn.commit()
            return extracted_trials
            
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        finally:
            conn.close()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/trial/{nct_id}", response_model=TrialResponse)
async def get_trial_by_id(nct_id: str):
    """Get a specific trial by NCT ID"""
    trial = get_clinical_trial_details(nct_id)
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    # Extract trial data for response
    ident = trial.get('identificationModule', {})
    status = trial.get('statusModule', {})
    design = trial.get('designModule', {})
    eligibility = trial.get('eligibilityModule', {})
    description = trial.get('descriptionModule', {})
    
    # Parse criteria
    criteria = eligibility.get('eligibilityCriteria')
    if isinstance(criteria, dict):
        full_criteria_text = criteria.get('textblock', '')
    else:
        full_criteria_text = criteria or ''
    
    inclusion_criteria = None
    exclusion_criteria = None
    if 'Exclusion Criteria' in full_criteria_text:
        parts = full_criteria_text.split('Exclusion Criteria', 1)
        inclusion_criteria = parts[0].replace('Inclusion Criteria:', '').strip()
        exclusion_criteria = parts[1].strip()
    elif full_criteria_text:
        inclusion_criteria = full_criteria_text.strip()
    
    return TrialResponse(
        nct_id=ident.get('nctId', ''),
        brief_title=ident.get('briefTitle', ''),
        official_title=ident.get('officialTitle', ''),
        brief_summary=description.get('briefSummary'),
        detailed_description=description.get('detailedDescription'),
        status=status.get('overallStatus', ''),
        phase=design.get('phase'),
        study_type=design.get('studyType', ''),
        enrollment_count=design.get('enrollmentInfo', {}).get('enrollmentCount'),
        start_date=str(parse_date(status.get('startDateStruct', {}).get('date'))) if parse_date(status.get('startDateStruct', {}).get('date')) else None,
        completion_date=str(parse_date(status.get('completionDateStruct', {}).get('date'))) if parse_date(status.get('completionDateStruct', {}).get('date')) else None,
        organization=ident.get('organization', {}).get('fullName'),
        inclusion_criteria=inclusion_criteria,
        exclusion_criteria=exclusion_criteria
    )

# New API endpoints for UI
@app.get("/trials", response_model=List[TrialResponse])
async def get_all_trials(limit: int = 50, offset: int = 0, status: Optional[str] = None, phase: Optional[str] = None):
    """Get all trials from database with optional filtering"""
    try:
        conn = connect_db()
        cur = conn.cursor()
        
        # Build query with filters
        query = """
            SELECT 
                tbi.nct_id, tbi.brief_title, tbi.official_title, 
                td.brief_summary, td.detailed_description,
                tbi.status, tbi.phase, tbi.study_type, tbi.enrollment_count,
                tbi.start_date, tbi.completion_date, tbi.organization_name,
                te.inclusion_criteria, te.exclusion_criteria
            FROM trial_basic_info tbi
            LEFT JOIN trial_descriptions td ON tbi.nct_id = td.nct_id
            LEFT JOIN trial_eligibility te ON tbi.nct_id = te.nct_id
            WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND tbi.status = %s"
            params.append(status)
        
        if phase:
            query += " AND tbi.phase = %s"
            params.append(phase)
        
        query += " ORDER BY tbi.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cur.execute(query, params)
        trials_data = cur.fetchall()
        
        trials = []
        for row in trials_data:
            trial = TrialResponse(
                nct_id=row[0] or '',
                brief_title=row[1] or '',
                official_title=row[2] or '',
                brief_summary=row[3],
                detailed_description=row[4],
                status=row[5] or '',
                phase=row[6],
                study_type=row[7] or '',
                enrollment_count=row[8],
                start_date=str(row[9]) if row[9] else None,
                completion_date=str(row[10]) if row[10] else None,
                organization=row[11],
                inclusion_criteria=row[12],
                exclusion_criteria=row[13]
            )
            trials.append(trial)
        
        cur.close()
        conn.close()
        return trials
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/trials/stats")
async def get_trial_stats():
    """Get statistics about trials in database"""
    try:
        conn = connect_db()
        cur = conn.cursor()
        
        # Get total count
        cur.execute("SELECT COUNT(*) FROM trial_basic_info")
        total_trials = cur.fetchone()[0]
        
        # Get status distribution
        cur.execute("""
            SELECT status, COUNT(*) as count 
            FROM trial_basic_info 
            GROUP BY status 
            ORDER BY count DESC
        """)
        status_stats = [{"status": row[0], "count": row[1]} for row in cur.fetchall()]
        
        # Get phase distribution
        cur.execute("""
            SELECT phase, COUNT(*) as count 
            FROM trial_basic_info 
            WHERE phase IS NOT NULL
            GROUP BY phase 
            ORDER BY count DESC
        """)
        phase_stats = [{"phase": row[0], "count": row[1]} for row in cur.fetchall()]
        
        # Get study type distribution
        cur.execute("""
            SELECT study_type, COUNT(*) as count 
            FROM trial_basic_info 
            GROUP BY study_type 
            ORDER BY count DESC
        """)
        study_type_stats = [{"study_type": row[0], "count": row[1]} for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        
        return {
            "total_trials": total_trials,
            "status_distribution": status_stats,
            "phase_distribution": phase_stats,
            "study_type_distribution": study_type_stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/trials/search")
async def search_trials_in_db(q: str, limit: int = 20):
    """Search trials in database by title or description"""
    try:
        conn = connect_db()
        cur = conn.cursor()
        
        search_query = """
            SELECT 
                tbi.nct_id, tbi.brief_title, tbi.official_title, 
                td.brief_summary, td.detailed_description,
                tbi.status, tbi.phase, tbi.study_type, tbi.enrollment_count,
                tbi.start_date, tbi.completion_date, tbi.organization_name,
                te.inclusion_criteria, te.exclusion_criteria
            FROM trial_basic_info tbi
            LEFT JOIN trial_descriptions td ON tbi.nct_id = td.nct_id
            LEFT JOIN trial_eligibility te ON tbi.nct_id = te.nct_id
            WHERE 
                tbi.brief_title ILIKE %s OR 
                tbi.official_title ILIKE %s OR 
                td.brief_summary ILIKE %s OR
                td.detailed_description ILIKE %s
            ORDER BY tbi.created_at DESC 
            LIMIT %s
        """
        
        search_term = f"%{q}%"
        cur.execute(search_query, [search_term, search_term, search_term, search_term, limit])
        trials_data = cur.fetchall()
        
        trials = []
        for row in trials_data:
            trial = TrialResponse(
                nct_id=row[0] or '',
                brief_title=row[1] or '',
                official_title=row[2] or '',
                brief_summary=row[3],
                detailed_description=row[4],
                status=row[5] or '',
                phase=row[6],
                study_type=row[7] or '',
                enrollment_count=row[8],
                start_date=str(row[9]) if row[9] else None,
                completion_date=str(row[10]) if row[10] else None,
                organization=row[11],
                inclusion_criteria=row[12],
                exclusion_criteria=row[13]
            )
            trials.append(trial)
        
        cur.close()
        conn.close()
        return trials
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
