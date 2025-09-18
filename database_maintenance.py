"""
Database Maintenance and Backup Script for Clinical Trials API
This script handles backups, maintenance, and database optimization
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import os
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
import gzip
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseMaintenance:
    def __init__(self, db_config: Dict[str, str], backup_dir: str = "backups"):
        self.db_config = db_config
        self.backup_dir = backup_dir
        self.connection = None
        
        # Create backup directory if it doesn't exist
        os.makedirs(backup_dir, exist_ok=True)
    
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
    
    def create_backup(self, backup_type: str = "full") -> str:
        """Create database backup"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"clinicai_backup_{backup_type}_{timestamp}.sql"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Use pg_dump to create backup
            cmd = [
                "pg_dump",
                "-h", self.db_config["host"],
                "-p", str(self.db_config["port"]),
                "-U", self.db_config["user"],
                "-d", self.db_config["database"],
                "-f", backup_path,
                "--verbose",
                "--no-password"
            ]
            
            # Set password via environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = self.db_config["password"]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Compress the backup
                compressed_path = f"{backup_path}.gz"
                with open(backup_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # Remove uncompressed file
                os.remove(backup_path)
                
                logger.info(f"Backup created successfully: {compressed_path}")
                return compressed_path
            else:
                logger.error(f"Backup failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return None
    
    def restore_backup(self, backup_path: str) -> bool:
        """Restore database from backup"""
        try:
            # Check if backup file exists
            if not os.path.exists(backup_path):
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Handle compressed backups
            if backup_path.endswith('.gz'):
                # Decompress temporarily
                temp_path = backup_path.replace('.gz', '_temp.sql')
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(temp_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                restore_path = temp_path
            else:
                restore_path = backup_path
            
            # Use psql to restore
            cmd = [
                "psql",
                "-h", self.db_config["host"],
                "-p", str(self.db_config["port"]),
                "-U", self.db_config["user"],
                "-d", self.db_config["database"],
                "-f", restore_path
            ]
            
            # Set password via environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = self.db_config["password"]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            # Clean up temporary file if created
            if backup_path.endswith('.gz') and os.path.exists(temp_path):
                os.remove(temp_path)
            
            if result.returncode == 0:
                logger.info(f"Backup restored successfully from: {backup_path}")
                return True
            else:
                logger.error(f"Restore failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False
    
    def cleanup_old_backups(self, days_to_keep: int = 30) -> int:
        """Remove old backup files"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            removed_count = 0
            
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("clinicai_backup_") and filename.endswith(".sql.gz"):
                    file_path = os.path.join(self.backup_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    
                    if file_time < cutoff_date:
                        os.remove(file_path)
                        removed_count += 1
                        logger.info(f"Removed old backup: {filename}")
            
            logger.info(f"Cleaned up {removed_count} old backup files")
            return removed_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
            return 0
    
    def optimize_database(self) -> Dict[str, Any]:
        """Optimize database performance"""
        try:
            cursor = self.connection.cursor()
            
            # Analyze tables for better query planning
            cursor.execute("ANALYZE;")
            
            # Update table statistics
            cursor.execute("""
                SELECT schemaname, tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
            """)
            tables = cursor.fetchall()
            
            for schema, table in tables:
                cursor.execute(f"ANALYZE {schema}.{table};")
            
            # Vacuum tables to reclaim space
            cursor.execute("VACUUM ANALYZE;")
            
            # Get database size
            cursor.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as size
            """)
            db_size = cursor.fetchone()[0]
            
            # Get table sizes
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """)
            table_sizes = cursor.fetchall()
            
            self.connection.commit()
            cursor.close()
            
            optimization_results = {
                "database_size": db_size,
                "table_sizes": [{"table": f"{schema}.{table}", "size": size} for schema, table, size in table_sizes],
                "optimization_completed": True,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("Database optimization completed")
            return optimization_results
            
        except Exception as e:
            logger.error(f"Error optimizing database: {e}")
            self.connection.rollback()
            return {"error": str(e), "optimization_completed": False}
    
    def check_database_health(self) -> Dict[str, Any]:
        """Check database health and performance"""
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            # Check database size
            cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database())) as size")
            db_size = cursor.fetchone()["size"]
            
            # Check table sizes
            cursor.execute("""
                SELECT 
                    tablename,
                    pg_size_pretty(pg_total_relation_size('public.'||tablename)) as size,
                    pg_total_relation_size('public.'||tablename) as size_bytes
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size('public.'||tablename) DESC
            """)
            table_sizes = cursor.fetchall()
            
            # Check index usage
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes 
                WHERE schemaname = 'public'
                ORDER BY idx_scan DESC
            """)
            index_usage = cursor.fetchall()
            
            # Check slow queries
            cursor.execute("""
                SELECT 
                    query,
                    calls,
                    total_time,
                    mean_time,
                    rows
                FROM pg_stat_statements 
                ORDER BY total_time DESC 
                LIMIT 10
            """)
            slow_queries = cursor.fetchall()
            
            # Check connection count
            cursor.execute("SELECT count(*) as connections FROM pg_stat_activity")
            connections = cursor.fetchone()["connections"]
            
            # Check for long-running queries
            cursor.execute("""
                SELECT 
                    pid,
                    now() - pg_stat_activity.query_start AS duration,
                    query
                FROM pg_stat_activity 
                WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes'
                AND state = 'active'
            """)
            long_queries = cursor.fetchall()
            
            cursor.close()
            
            health_report = {
                "database_size": db_size,
                "table_sizes": [dict(row) for row in table_sizes],
                "index_usage": [dict(row) for row in index_usage],
                "slow_queries": [dict(row) for row in slow_queries],
                "active_connections": connections,
                "long_running_queries": [dict(row) for row in long_queries],
                "timestamp": datetime.now().isoformat()
            }
            
            return health_report
            
        except Exception as e:
            logger.error(f"Error checking database health: {e}")
            return {"error": str(e)}
    
    def schedule_maintenance(self) -> Dict[str, Any]:
        """Schedule and run maintenance tasks"""
        try:
            maintenance_log = {
                "timestamp": datetime.now().isoformat(),
                "tasks_completed": [],
                "errors": []
            }
            
            # 1. Create backup
            try:
                backup_path = self.create_backup("maintenance")
                if backup_path:
                    maintenance_log["tasks_completed"].append(f"Backup created: {backup_path}")
                else:
                    maintenance_log["errors"].append("Backup creation failed")
            except Exception as e:
                maintenance_log["errors"].append(f"Backup error: {e}")
            
            # 2. Clean up old backups
            try:
                removed_count = self.cleanup_old_backups()
                maintenance_log["tasks_completed"].append(f"Cleaned up {removed_count} old backups")
            except Exception as e:
                maintenance_log["errors"].append(f"Cleanup error: {e}")
            
            # 3. Optimize database
            try:
                optimization_results = self.optimize_database()
                if optimization_results.get("optimization_completed"):
                    maintenance_log["tasks_completed"].append("Database optimization completed")
                else:
                    maintenance_log["errors"].append("Database optimization failed")
            except Exception as e:
                maintenance_log["errors"].append(f"Optimization error: {e}")
            
            # 4. Check database health
            try:
                health_report = self.check_database_health()
                maintenance_log["health_report"] = health_report
            except Exception as e:
                maintenance_log["errors"].append(f"Health check error: {e}")
            
            # Save maintenance log
            log_filename = f"maintenance_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            log_path = os.path.join(self.backup_dir, log_filename)
            with open(log_path, 'w') as f:
                json.dump(maintenance_log, f, indent=2, default=str)
            
            logger.info("Maintenance tasks completed")
            return maintenance_log
            
        except Exception as e:
            logger.error(f"Error in scheduled maintenance: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def get_backup_list(self) -> List[Dict[str, Any]]:
        """Get list of available backups"""
        try:
            backups = []
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("clinicai_backup_") and filename.endswith(".sql.gz"):
                    file_path = os.path.join(self.backup_dir, filename)
                    file_stat = os.stat(file_path)
                    
                    backup_info = {
                        "filename": filename,
                        "path": file_path,
                        "size": file_stat.st_size,
                        "size_mb": round(file_stat.st_size / (1024 * 1024), 2),
                        "created": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                        "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                    }
                    backups.append(backup_info)
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x["created"], reverse=True)
            return backups
            
        except Exception as e:
            logger.error(f"Error getting backup list: {e}")
            return []

# Example usage
if __name__ == "__main__":
    db_config = {
        'host': 'localhost',
        'database': 'clinicai',
        'user': 'clinicai',
        'password': '12345678',
        'port': '5432'
    }
    
    maintenance = DatabaseMaintenance(db_config)
    maintenance.connect()
    
    # Run maintenance tasks
    maintenance_log = maintenance.schedule_maintenance()
    print("Maintenance completed:")
    print(json.dumps(maintenance_log, indent=2, default=str))
    
    # List available backups
    backups = maintenance.get_backup_list()
    print(f"\nAvailable backups: {len(backups)}")
    for backup in backups[:5]:  # Show first 5
        print(f"- {backup['filename']} ({backup['size_mb']} MB, {backup['created']})")
    
    maintenance.disconnect()

