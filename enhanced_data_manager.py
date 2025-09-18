"""
Enhanced Data Manager for Clinical Trials API
This script provides better data management, validation, and database operations
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json
import logging
from typing import Dict, List, Optional, Any
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedDataManager:
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.connection = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            self.connection.autocommit = False
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def create_tables(self):
        """Create all database tables using the enhanced schema"""
        try:
            with open('database_schema.sql', 'r') as f:
                schema_sql = f.read()
            
            cursor = self.connection.cursor()
            cursor.execute(schema_sql)
            self.connection.commit()
            cursor.close()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            self.connection.rollback()
            raise
    
    def insert_trial_data(self, trial_data: Dict[str, Any]) -> bool:
        """Insert comprehensive trial data into the database"""
        try:
            cursor = self.connection.cursor()
            
            # Insert basic trial info
            basic_info_sql = """
                INSERT INTO trial_basic_info (
                    nct_id, protocol_section_id, organization_name, organization_type,
                    brief_title, official_title, status, phase, study_type,
                    enrollment_count, enrollment_type, start_date, completion_date,
                    primary_completion_date, is_fda_regulated_drug, is_fda_regulated_device,
                    is_unapproved_device, is_ppsd, is_us_export
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) ON CONFLICT (nct_id) DO UPDATE SET
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
            """
            
            cursor.execute(basic_info_sql, (
                trial_data.get('nct_id'),
                trial_data.get('protocol_section_id'),
                trial_data.get('organization_name'),
                trial_data.get('organization_type'),
                trial_data.get('brief_title'),
                trial_data.get('official_title'),
                trial_data.get('status'),
                trial_data.get('phase'),
                trial_data.get('study_type'),
                trial_data.get('enrollment_count'),
                trial_data.get('enrollment_type'),
                trial_data.get('start_date'),
                trial_data.get('completion_date'),
                trial_data.get('primary_completion_date'),
                trial_data.get('is_fda_regulated_drug'),
                trial_data.get('is_fda_regulated_device'),
                trial_data.get('is_unapproved_device'),
                trial_data.get('is_ppsd'),
                trial_data.get('is_us_export')
            ))
            
            # Insert descriptions
            if trial_data.get('brief_summary') or trial_data.get('detailed_description'):
                desc_sql = """
                    INSERT INTO trial_descriptions (nct_id, brief_summary, detailed_description)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (nct_id) DO UPDATE SET
                        brief_summary = EXCLUDED.brief_summary,
                        detailed_description = EXCLUDED.detailed_description
                """
                cursor.execute(desc_sql, (
                    trial_data.get('nct_id'),
                    trial_data.get('brief_summary'),
                    trial_data.get('detailed_description')
                ))
            
            # Insert eligibility criteria
            if trial_data.get('inclusion_criteria') or trial_data.get('exclusion_criteria'):
                eligibility_sql = """
                    INSERT INTO trial_eligibility (
                        nct_id, inclusion_criteria, exclusion_criteria,
                        minimum_age, maximum_age, gender, healthy_volunteers
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (nct_id) DO UPDATE SET
                        inclusion_criteria = EXCLUDED.inclusion_criteria,
                        exclusion_criteria = EXCLUDED.exclusion_criteria,
                        minimum_age = EXCLUDED.minimum_age,
                        maximum_age = EXCLUDED.maximum_age,
                        gender = EXCLUDED.gender,
                        healthy_volunteers = EXCLUDED.healthy_volunteers
                """
                cursor.execute(eligibility_sql, (
                    trial_data.get('nct_id'),
                    trial_data.get('inclusion_criteria'),
                    trial_data.get('exclusion_criteria'),
                    trial_data.get('minimum_age'),
                    trial_data.get('maximum_age'),
                    trial_data.get('gender'),
                    trial_data.get('healthy_volunteers')
                ))
            
            # Insert arms and interventions
            if trial_data.get('arms_interventions'):
                for arm in trial_data['arms_interventions']:
                    arm_sql = """
                        INSERT INTO trial_arms_interventions (
                            nct_id, arm_group_label, arm_group_type, arm_group_description,
                            intervention_name, intervention_type, intervention_description
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(arm_sql, (
                        trial_data.get('nct_id'),
                        arm.get('arm_group_label'),
                        arm.get('arm_group_type'),
                        arm.get('arm_group_description'),
                        arm.get('intervention_name'),
                        arm.get('intervention_type'),
                        arm.get('intervention_description')
                    ))
            
            # Insert outcomes
            if trial_data.get('outcomes'):
                for outcome in trial_data['outcomes']:
                    outcome_sql = """
                        INSERT INTO trial_outcomes (
                            nct_id, outcome_type, outcome_measure, outcome_description, outcome_time_frame
                        ) VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(outcome_sql, (
                        trial_data.get('nct_id'),
                        outcome.get('outcome_type'),
                        outcome.get('outcome_measure'),
                        outcome.get('outcome_description'),
                        outcome.get('outcome_time_frame')
                    ))
            
            # Insert locations
            if trial_data.get('locations'):
                for location in trial_data['locations']:
                    location_sql = """
                        INSERT INTO trial_locations (
                            nct_id, facility_name, facility_address, facility_city,
                            facility_state, facility_zip, facility_country,
                            facility_contact_name, facility_contact_phone, facility_contact_email
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(location_sql, (
                        trial_data.get('nct_id'),
                        location.get('facility_name'),
                        location.get('facility_address'),
                        location.get('facility_city'),
                        location.get('facility_state'),
                        location.get('facility_zip'),
                        location.get('facility_country'),
                        location.get('facility_contact_name'),
                        location.get('facility_contact_phone'),
                        location.get('facility_contact_email')
                    ))
            
            # Insert conditions
            if trial_data.get('conditions'):
                for condition in trial_data['conditions']:
                    condition_sql = """
                        INSERT INTO trial_conditions (nct_id, condition_name)
                        VALUES (%s, %s)
                    """
                    cursor.execute(condition_sql, (
                        trial_data.get('nct_id'),
                        condition
                    ))
            
            # Insert keywords
            if trial_data.get('keywords'):
                for keyword in trial_data['keywords']:
                    keyword_sql = """
                        INSERT INTO trial_keywords (nct_id, keyword)
                        VALUES (%s, %s)
                    """
                    cursor.execute(keyword_sql, (
                        trial_data.get('nct_id'),
                        keyword
                    ))
            
            self.connection.commit()
            cursor.close()
            logger.info(f"Trial data inserted successfully: {trial_data.get('nct_id')}")
            return True
            
        except Exception as e:
            logger.error(f"Error inserting trial data: {e}")
            self.connection.rollback()
            return False
    
    def search_trials_advanced(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Advanced search with filters and full-text search"""
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            # Build dynamic WHERE clause
            where_conditions = []
            params = []
            
            # Full-text search
            if query:
                where_conditions.append("""
                    (to_tsvector('english', tbi.brief_title || ' ' || tbi.official_title) @@ plainto_tsquery('english', %s)
                    OR to_tsvector('english', td.brief_summary || ' ' || td.detailed_description) @@ plainto_tsquery('english', %s)
                    OR to_tsvector('english', tc.condition_name) @@ plainto_tsquery('english', %s)
                    OR to_tsvector('english', tk.keyword) @@ plainto_tsquery('english', %s))
                """)
                params.extend([query, query, query, query])
            
            # Apply filters
            if filters:
                if filters.get('status'):
                    where_conditions.append("tbi.status = %s")
                    params.append(filters['status'])
                
                if filters.get('phase'):
                    where_conditions.append("tbi.phase = %s")
                    params.append(filters['phase'])
                
                if filters.get('study_type'):
                    where_conditions.append("tbi.study_type = %s")
                    params.append(filters['study_type'])
                
                if filters.get('start_date_from'):
                    where_conditions.append("tbi.start_date >= %s")
                    params.append(filters['start_date_from'])
                
                if filters.get('start_date_to'):
                    where_conditions.append("tbi.start_date <= %s")
                    params.append(filters['start_date_to'])
                
                if filters.get('organization'):
                    where_conditions.append("tbi.organization_name ILIKE %s")
                    params.append(f"%{filters['organization']}%")
            
            # Build final query
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            search_sql = f"""
                SELECT DISTINCT
                    tbi.nct_id,
                    tbi.brief_title,
                    tbi.official_title,
                    tbi.status,
                    tbi.phase,
                    tbi.study_type,
                    tbi.enrollment_count,
                    tbi.start_date,
                    tbi.completion_date,
                    tbi.organization_name,
                    td.brief_summary,
                    td.detailed_description,
                    te.inclusion_criteria,
                    te.exclusion_criteria,
                    te.minimum_age,
                    te.maximum_age,
                    te.gender,
                    te.healthy_volunteers
                FROM trial_basic_info tbi
                LEFT JOIN trial_descriptions td ON tbi.nct_id = td.nct_id
                LEFT JOIN trial_eligibility te ON tbi.nct_id = te.nct_id
                LEFT JOIN trial_conditions tc ON tbi.nct_id = tc.nct_id
                LEFT JOIN trial_keywords tk ON tbi.nct_id = tk.nct_id
                WHERE {where_clause}
                ORDER BY tbi.start_date DESC
                LIMIT %s
            """
            
            params.append(filters.get('limit', 50))
            cursor.execute(search_sql, params)
            
            results = cursor.fetchall()
            cursor.close()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error in advanced search: {e}")
            return []
    
    def get_trial_statistics(self) -> Dict[str, Any]:
        """Get database statistics and insights"""
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            stats_sql = """
                SELECT 
                    COUNT(*) as total_trials,
                    COUNT(CASE WHEN status = 'RECRUITING' THEN 1 END) as recruiting_trials,
                    COUNT(CASE WHEN status = 'ACTIVE_NOT_RECRUITING' THEN 1 END) as active_trials,
                    COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END) as completed_trials,
                    COUNT(CASE WHEN phase = 'PHASE_1' THEN 1 END) as phase_1_trials,
                    COUNT(CASE WHEN phase = 'PHASE_2' THEN 1 END) as phase_2_trials,
                    COUNT(CASE WHEN phase = 'PHASE_3' THEN 1 END) as phase_3_trials,
                    COUNT(CASE WHEN study_type = 'INTERVENTIONAL' THEN 1 END) as interventional_trials,
                    COUNT(CASE WHEN study_type = 'OBSERVATIONAL' THEN 1 END) as observational_trials,
                    AVG(enrollment_count) as avg_enrollment,
                    MIN(start_date) as earliest_trial,
                    MAX(start_date) as latest_trial
                FROM trial_basic_info
            """
            
            cursor.execute(stats_sql)
            stats = dict(cursor.fetchone())
            
            # Get top organizations
            org_sql = """
                SELECT organization_name, COUNT(*) as trial_count
                FROM trial_basic_info
                WHERE organization_name IS NOT NULL
                GROUP BY organization_name
                ORDER BY trial_count DESC
                LIMIT 10
            """
            cursor.execute(org_sql)
            stats['top_organizations'] = [dict(row) for row in cursor.fetchall()]
            
            # Get top conditions
            condition_sql = """
                SELECT condition_name, COUNT(*) as trial_count
                FROM trial_conditions
                GROUP BY condition_name
                ORDER BY trial_count DESC
                LIMIT 10
            """
            cursor.execute(condition_sql)
            stats['top_conditions'] = [dict(row) for row in cursor.fetchall()]
            
            cursor.close()
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def export_data(self, format: str = 'json', filepath: str = None) -> str:
        """Export trial data in various formats"""
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            export_sql = """
                SELECT * FROM trial_complete_info
                ORDER BY start_date DESC
            """
            cursor.execute(export_sql)
            data = [dict(row) for row in cursor.fetchall()]
            cursor.close()
            
            if format.lower() == 'json':
                if filepath:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, default=str)
                    return f"Data exported to {filepath}"
                else:
                    return json.dumps(data, indent=2, default=str)
            
            elif format.lower() == 'csv':
                import csv
                if not filepath:
                    filepath = f"trials_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    if data:
                        writer = csv.DictWriter(f, fieldnames=data[0].keys())
                        writer.writeheader()
                        writer.writerows(data)
                return f"Data exported to {filepath}"
            
            else:
                return "Unsupported format. Use 'json' or 'csv'"
                
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return f"Export failed: {e}"

# Example usage
if __name__ == "__main__":
    db_config = {
        'host': 'localhost',
        'database': 'clinicai',
        'user': 'clinicai',
        'password': '12345678',
        'port': '5432'
    }
    
    manager = EnhancedDataManager(db_config)
    manager.connect()
    
    # Create tables
    manager.create_tables()
    
    # Get statistics
    stats = manager.get_trial_statistics()
    print("Database Statistics:")
    print(json.dumps(stats, indent=2, default=str))
    
    manager.disconnect()

