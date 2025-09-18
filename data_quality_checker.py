"""
Data Quality Checker for Clinical Trials Database
This script validates data integrity, completeness, and quality
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from typing import Dict, List, Any
import re
from datetime import datetime, date

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataQualityChecker:
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.connection = None
        self.quality_issues = []
    
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
    
    def check_data_completeness(self) -> Dict[str, Any]:
        """Check for missing required fields"""
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            completeness_checks = {
                'missing_nct_id': "SELECT COUNT(*) as count FROM trial_basic_info WHERE nct_id IS NULL OR nct_id = ''",
                'missing_brief_title': "SELECT COUNT(*) as count FROM trial_basic_info WHERE brief_title IS NULL OR brief_title = ''",
                'missing_official_title': "SELECT COUNT(*) as count FROM trial_basic_info WHERE official_title IS NULL OR official_title = ''",
                'missing_status': "SELECT COUNT(*) as count FROM trial_basic_info WHERE status IS NULL OR status = ''",
                'missing_study_type': "SELECT COUNT(*) as count FROM trial_basic_info WHERE study_type IS NULL OR study_type = ''",
                'missing_organization': "SELECT COUNT(*) as count FROM trial_basic_info WHERE organization_name IS NULL OR organization_name = ''",
                'missing_descriptions': "SELECT COUNT(*) as count FROM trial_basic_info tbi LEFT JOIN trial_descriptions td ON tbi.nct_id = td.nct_id WHERE td.nct_id IS NULL",
                'missing_eligibility': "SELECT COUNT(*) as count FROM trial_basic_info tbi LEFT JOIN trial_eligibility te ON tbi.nct_id = te.nct_id WHERE te.nct_id IS NULL"
            }
            
            results = {}
            for check_name, query in completeness_checks.items():
                cursor.execute(query)
                result = cursor.fetchone()
                results[check_name] = result['count']
                if result['count'] > 0:
                    self.quality_issues.append(f"{check_name}: {result['count']} records missing")
            
            cursor.close()
            return results
            
        except Exception as e:
            logger.error(f"Error checking data completeness: {e}")
            return {}
    
    def check_data_consistency(self) -> Dict[str, Any]:
        """Check for data consistency issues"""
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            consistency_checks = {
                'invalid_dates': """
                    SELECT COUNT(*) as count FROM trial_basic_info 
                    WHERE (start_date > completion_date AND start_date IS NOT NULL AND completion_date IS NOT NULL)
                    OR (start_date > primary_completion_date AND start_date IS NOT NULL AND primary_completion_date IS NOT NULL)
                """,
                'invalid_enrollment': """
                    SELECT COUNT(*) as count FROM trial_basic_info 
                    WHERE enrollment_count < 0 OR enrollment_count > 1000000
                """,
                'duplicate_nct_ids': """
                    SELECT nct_id, COUNT(*) as count 
                    FROM trial_basic_info 
                    GROUP BY nct_id 
                    HAVING COUNT(*) > 1
                """,
                'orphaned_records': """
                    SELECT COUNT(*) as count FROM trial_descriptions td 
                    LEFT JOIN trial_basic_info tbi ON td.nct_id = tbi.nct_id 
                    WHERE tbi.nct_id IS NULL
                """
            }
            
            results = {}
            for check_name, query in consistency_checks.items():
                cursor.execute(query)
                if check_name == 'duplicate_nct_ids':
                    duplicates = cursor.fetchall()
                    results[check_name] = len(duplicates)
                    if duplicates:
                        self.quality_issues.append(f"{check_name}: {len(duplicates)} duplicate NCT IDs found")
                        for dup in duplicates:
                            self.quality_issues.append(f"  - NCT ID {dup['nct_id']} appears {dup['count']} times")
                else:
                    result = cursor.fetchone()
                    results[check_name] = result['count']
                    if result['count'] > 0:
                        self.quality_issues.append(f"{check_name}: {result['count']} records with issues")
            
            cursor.close()
            return results
            
        except Exception as e:
            logger.error(f"Error checking data consistency: {e}")
            return {}
    
    def check_data_format(self) -> Dict[str, Any]:
        """Check for data format issues"""
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            format_checks = {
                'invalid_nct_format': """
                    SELECT nct_id FROM trial_basic_info 
                    WHERE nct_id !~ '^NCT[0-9]{8}$'
                """,
                'invalid_email_format': """
                    SELECT facility_contact_email FROM trial_locations 
                    WHERE facility_contact_email IS NOT NULL 
                    AND facility_contact_email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'
                """,
                'invalid_phone_format': """
                    SELECT facility_contact_phone FROM trial_locations 
                    WHERE facility_contact_phone IS NOT NULL 
                    AND facility_contact_phone !~ '^[+]?[0-9\\s\\-\\(\\)]{10,}$'
                """,
                'invalid_date_format': """
                    SELECT nct_id, start_date, completion_date FROM trial_basic_info 
                    WHERE (start_date IS NOT NULL AND start_date < '1900-01-01')
                    OR (completion_date IS NOT NULL AND completion_date < '1900-01-01')
                    OR (start_date IS NOT NULL AND start_date > CURRENT_DATE + INTERVAL '10 years')
                    OR (completion_date IS NOT NULL AND completion_date > CURRENT_DATE + INTERVAL '10 years')
                """
            }
            
            results = {}
            for check_name, query in format_checks.items():
                cursor.execute(query)
                records = cursor.fetchall()
                results[check_name] = len(records)
                if records:
                    self.quality_issues.append(f"{check_name}: {len(records)} records with format issues")
                    for record in records[:5]:  # Show first 5 examples
                        self.quality_issues.append(f"  - Example: {record}")
            
            cursor.close()
            return results
            
        except Exception as e:
            logger.error(f"Error checking data format: {e}")
            return {}
    
    def check_data_relationships(self) -> Dict[str, Any]:
        """Check for relationship integrity"""
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            relationship_checks = {
                'missing_conditions': """
                    SELECT COUNT(*) as count FROM trial_basic_info tbi 
                    LEFT JOIN trial_conditions tc ON tbi.nct_id = tc.nct_id 
                    WHERE tc.nct_id IS NULL
                """,
                'missing_keywords': """
                    SELECT COUNT(*) as count FROM trial_basic_info tbi 
                    LEFT JOIN trial_keywords tk ON tbi.nct_id = tk.nct_id 
                    WHERE tk.nct_id IS NULL
                """,
                'missing_outcomes': """
                    SELECT COUNT(*) as count FROM trial_basic_info tbi 
                    LEFT JOIN trial_outcomes t_outcomes ON tbi.nct_id = t_outcomes.nct_id 
                    WHERE t_outcomes.nct_id IS NULL
                """,
                'missing_locations': """
                    SELECT COUNT(*) as count FROM trial_basic_info tbi 
                    LEFT JOIN trial_locations tl ON tbi.nct_id = tl.nct_id 
                    WHERE tl.nct_id IS NULL
                """
            }
            
            results = {}
            for check_name, query in relationship_checks.items():
                cursor.execute(query)
                result = cursor.fetchone()
                results[check_name] = result['count']
                if result['count'] > 0:
                    self.quality_issues.append(f"{check_name}: {result['count']} trials missing related data")
            
            cursor.close()
            return results
            
        except Exception as e:
            logger.error(f"Error checking data relationships: {e}")
            return {}
    
    def check_data_quality_score(self) -> Dict[str, Any]:
        """Calculate overall data quality score"""
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            # Get total number of trials
            cursor.execute("SELECT COUNT(*) as total FROM trial_basic_info")
            total_trials = cursor.fetchone()['total']
            
            if total_trials == 0:
                return {
                    "overall_score": 0, 
                    "completeness_score": 0,
                    "consistency_score": 0,
                    "format_score": 0,
                    "relationship_score": 0,
                    "total_trials": 0,
                    "total_issues": 0,
                    "quality_level": "No Data",
                    "message": "No trials found"
                }
            
            # Calculate completeness score
            completeness_checks = self.check_data_completeness()
            missing_fields = sum(completeness_checks.values())
            completeness_score = max(0, 100 - (missing_fields / total_trials) * 100)
            
            # Calculate consistency score
            consistency_checks = self.check_data_consistency()
            inconsistent_records = sum(consistency_checks.values())
            consistency_score = max(0, 100 - (inconsistent_records / total_trials) * 100)
            
            # Calculate format score
            format_checks = self.check_data_format()
            format_issues = sum(format_checks.values())
            format_score = max(0, 100 - (format_issues / total_trials) * 100)
            
            # Calculate relationship score
            relationship_checks = self.check_data_relationships()
            missing_relationships = sum(relationship_checks.values())
            relationship_score = max(0, 100 - (missing_relationships / total_trials) * 100)
            
            # Overall quality score (weighted average)
            overall_score = (
                completeness_score * 0.3 +
                consistency_score * 0.3 +
                format_score * 0.2 +
                relationship_score * 0.2
            )
            
            quality_assessment = {
                "overall_score": round(overall_score, 2),
                "completeness_score": round(completeness_score, 2),
                "consistency_score": round(consistency_score, 2),
                "format_score": round(format_score, 2),
                "relationship_score": round(relationship_score, 2),
                "total_trials": total_trials,
                "total_issues": len(self.quality_issues),
                "quality_level": self._get_quality_level(overall_score)
            }
            
            cursor.close()
            return quality_assessment
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return {"quality_score": 0, "error": str(e)}
    
    def _get_quality_level(self, score: float) -> str:
        """Get quality level based on score"""
        if score >= 90:
            return "Excellent"
        elif score >= 80:
            return "Good"
        elif score >= 70:
            return "Fair"
        elif score >= 60:
            return "Poor"
        else:
            return "Critical"
    
    def generate_quality_report(self) -> str:
        """Generate comprehensive quality report"""
        report = []
        report.append("=" * 60)
        report.append("CLINICAL TRIALS DATABASE QUALITY REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Overall quality score
        quality_assessment = self.check_data_quality_score()
        report.append("OVERALL QUALITY ASSESSMENT")
        report.append("-" * 30)
        report.append(f"Overall Score: {quality_assessment['overall_score']}/100")
        report.append(f"Quality Level: {quality_assessment['quality_level']}")
        report.append(f"Total Trials: {quality_assessment['total_trials']}")
        report.append(f"Total Issues: {quality_assessment['total_issues']}")
        report.append("")
        
        # Detailed scores
        report.append("DETAILED SCORES")
        report.append("-" * 20)
        report.append(f"Completeness: {quality_assessment['completeness_score']}/100")
        report.append(f"Consistency: {quality_assessment['consistency_score']}/100")
        report.append(f"Format: {quality_assessment['format_score']}/100")
        report.append(f"Relationships: {quality_assessment['relationship_score']}/100")
        report.append("")
        
        # Issues found
        if self.quality_issues:
            report.append("ISSUES FOUND")
            report.append("-" * 15)
            for i, issue in enumerate(self.quality_issues, 1):
                report.append(f"{i}. {issue}")
        else:
            report.append("No issues found!")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def run_full_quality_check(self) -> Dict[str, Any]:
        """Run all quality checks and return comprehensive results"""
        logger.info("Starting comprehensive data quality check...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "completeness": self.check_data_completeness(),
            "consistency": self.check_data_consistency(),
            "format": self.check_data_format(),
            "relationships": self.check_data_relationships(),
            "quality_assessment": self.check_data_quality_score(),
            "issues": self.quality_issues.copy()
        }
        
        logger.info("Data quality check completed")
        return results

# Example usage
if __name__ == "__main__":
    db_config = {
        'host': 'localhost',
        'database': 'clinicai',
        'user': 'clinicai',
        'password': '12345678',
        'port': '5432'
    }
    
    checker = DataQualityChecker(db_config)
    checker.connect()
    
    # Run full quality check
    results = checker.run_full_quality_check()
    
    # Generate and print report
    report = checker.generate_quality_report()
    print(report)
    
    # Save report to file
    with open(f"quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", 'w') as f:
        f.write(report)
    
    checker.disconnect()
