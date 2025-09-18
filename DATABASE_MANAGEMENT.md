# Clinical Trials Database Management Guide

This guide covers comprehensive database management for the Clinical Trials API, including data storage, quality assurance, maintenance, and optimization.

## 📊 Database Schema Overview

### Enhanced Schema Features

The enhanced database schema includes:

- **Normalized Tables**: Better data organization with proper relationships
- **Full-Text Search**: Advanced search capabilities using PostgreSQL's GIN indexes
- **Data Validation**: Built-in constraints and validation rules
- **Audit Trails**: Timestamps and change tracking
- **Performance Optimization**: Strategic indexing for fast queries

### Table Structure

```
trial_basic_info          # Main trial information
├── trial_descriptions    # Brief and detailed descriptions
├── trial_eligibility     # Inclusion/exclusion criteria
├── trial_arms_interventions # Study arms and interventions
├── trial_outcomes        # Primary and secondary outcomes
├── trial_locations       # Study locations and contacts
├── trial_contacts        # Trial contacts and officials
├── trial_keywords        # Search keywords
├── trial_conditions      # Medical conditions
└── trial_interventions   # Study interventions
```

## 🚀 Getting Started

### 1. Database Setup

```bash
# Create the enhanced schema
psql -h localhost -U clinicai -d clinicai -f database_schema.sql

# Or use Python
python enhanced_data_manager.py
```

### 2. Data Management

```python
from enhanced_data_manager import EnhancedDataManager

# Initialize data manager
db_config = {
    'host': 'localhost',
    'database': 'clinicai',
    'user': 'clinicai',
    'password': '12345678',
    'port': '5432'
}

manager = EnhancedDataManager(db_config)
manager.connect()

# Insert trial data
trial_data = {
    'nct_id': 'NCT12345678',
    'brief_title': 'Example Trial',
    'official_title': 'A Phase III Study of Example Drug',
    'status': 'RECRUITING',
    'phase': 'PHASE_3',
    'study_type': 'INTERVENTIONAL',
    'organization_name': 'Example University',
    'brief_summary': 'This is a brief summary...',
    'detailed_description': 'This is a detailed description...',
    'inclusion_criteria': 'Age 18-65 years...',
    'exclusion_criteria': 'Pregnant women...',
    'conditions': ['Diabetes', 'Hypertension'],
    'keywords': ['diabetes', 'treatment', 'phase3']
}

success = manager.insert_trial_data(trial_data)
```

## 🔍 Data Quality Management

### Quality Checking

```python
from data_quality_checker import DataQualityChecker

checker = DataQualityChecker(db_config)
checker.connect()

# Run comprehensive quality check
results = checker.run_full_quality_check()

# Generate quality report
report = checker.generate_quality_report()
print(report)
```

### Quality Metrics

- **Completeness Score**: Percentage of required fields populated
- **Consistency Score**: Data consistency and validation
- **Format Score**: Data format compliance
- **Relationship Score**: Referential integrity

## 🛠️ Database Maintenance

### Automated Maintenance

```python
from database_maintenance import DatabaseMaintenance

maintenance = DatabaseMaintenance(db_config)
maintenance.connect()

# Run scheduled maintenance
maintenance_log = maintenance.schedule_maintenance()

# Create backup
backup_path = maintenance.create_backup("full")

# Optimize database
optimization_results = maintenance.optimize_database()
```

### Maintenance Tasks

1. **Backup Creation**: Automated daily backups
2. **Cleanup**: Remove old backup files
3. **Optimization**: Analyze and vacuum tables
4. **Health Monitoring**: Check database performance

## 📈 Performance Optimization

### Indexing Strategy

The database includes strategic indexes for:

- **Primary Keys**: Fast lookups by NCT ID
- **Status/Phase**: Filter by trial status and phase
- **Full-Text Search**: GIN indexes for content search
- **Date Ranges**: Efficient date-based queries
- **Organization**: Quick organization filtering

### Query Optimization

```sql
-- Use the optimized view for complete trial information
SELECT * FROM trial_complete_info 
WHERE status = 'RECRUITING' 
AND phase = 'PHASE_3'
ORDER BY start_date DESC;

-- Full-text search
SELECT * FROM trial_complete_info 
WHERE to_tsvector('english', brief_title || ' ' || official_title) 
@@ plainto_tsquery('english', 'diabetes treatment');

-- Advanced filtering
SELECT * FROM trial_complete_info 
WHERE start_date >= '2023-01-01' 
AND organization_name ILIKE '%university%'
AND study_type = 'INTERVENTIONAL';
```

## 🔒 Data Security

### Access Control

```sql
-- Grant specific permissions
GRANT SELECT ON trial_basic_info TO readonly_user;
GRANT INSERT, UPDATE ON trial_basic_info TO data_entry_user;
GRANT ALL PRIVILEGES ON ALL TABLES TO admin_user;

-- Create read-only user
CREATE USER readonly_user WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE clinicai TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
```

### Backup Security

- **Encrypted Backups**: Use GPG encryption for sensitive data
- **Secure Storage**: Store backups in encrypted storage
- **Access Control**: Limit backup access to authorized personnel
- **Regular Testing**: Test backup restoration regularly

## 📊 Monitoring and Analytics

### Database Statistics

```python
# Get comprehensive statistics
stats = manager.get_trial_statistics()
print(f"Total Trials: {stats['total_trials']}")
print(f"Recruiting: {stats['recruiting_trials']}")
print(f"Phase 3: {stats['phase_3_trials']}")
print(f"Average Enrollment: {stats['avg_enrollment']}")
```

### Health Monitoring

```python
# Check database health
health_report = maintenance.check_database_health()
print(f"Database Size: {health_report['database_size']}")
print(f"Active Connections: {health_report['active_connections']}")
print(f"Long Running Queries: {len(health_report['long_running_queries'])}")
```

## 🚨 Troubleshooting

### Common Issues

1. **Connection Errors**
   ```bash
   # Check PostgreSQL service
   sudo systemctl status postgresql
   
   # Check connection
   psql -h localhost -U clinicai -d clinicai
   ```

2. **Performance Issues**
   ```sql
   -- Check slow queries
   SELECT query, calls, total_time, mean_time 
   FROM pg_stat_statements 
   ORDER BY total_time DESC;
   
   -- Analyze table statistics
   ANALYZE trial_basic_info;
   ```

3. **Data Quality Issues**
   ```python
   # Run quality check
   checker = DataQualityChecker(db_config)
   results = checker.run_full_quality_check()
   
   # Fix common issues
   if results['completeness']['missing_descriptions'] > 0:
       print("Some trials missing descriptions")
   ```

### Recovery Procedures

1. **Restore from Backup**
   ```python
   # List available backups
   backups = maintenance.get_backup_list()
   
   # Restore specific backup
   success = maintenance.restore_backup(backup_path)
   ```

2. **Data Repair**
   ```sql
   -- Fix orphaned records
   DELETE FROM trial_descriptions 
   WHERE nct_id NOT IN (SELECT nct_id FROM trial_basic_info);
   
   -- Update missing data
   UPDATE trial_basic_info 
   SET status = 'UNKNOWN' 
   WHERE status IS NULL;
   ```

## 📋 Best Practices

### Data Entry

1. **Validate Input**: Always validate data before insertion
2. **Use Transactions**: Wrap related operations in transactions
3. **Handle Duplicates**: Use ON CONFLICT for upsert operations
4. **Log Changes**: Track all data modifications

### Performance

1. **Use Indexes**: Leverage database indexes for queries
2. **Batch Operations**: Group multiple operations together
3. **Monitor Queries**: Use EXPLAIN ANALYZE for slow queries
4. **Regular Maintenance**: Run VACUUM and ANALYZE regularly

### Security

1. **Principle of Least Privilege**: Grant minimum required permissions
2. **Regular Backups**: Maintain multiple backup copies
3. **Monitor Access**: Log and monitor database access
4. **Update Regularly**: Keep PostgreSQL and extensions updated

## 🔧 Maintenance Schedule

### Daily Tasks
- [ ] Create automated backup
- [ ] Monitor database health
- [ ] Check for long-running queries

### Weekly Tasks
- [ ] Run data quality checks
- [ ] Analyze query performance
- [ ] Clean up old logs

### Monthly Tasks
- [ ] Full database optimization
- [ ] Review and update indexes
- [ ] Test backup restoration
- [ ] Security audit

### Quarterly Tasks
- [ ] Review data retention policies
- [ ] Update documentation
- [ ] Performance tuning
- [ ] Disaster recovery testing

## 📞 Support

For database management issues:

1. Check the logs: `tail -f /var/log/postgresql/postgresql.log`
2. Run quality checks: `python data_quality_checker.py`
3. Review maintenance logs: `ls -la backups/maintenance_log_*.json`
4. Check database health: `python database_maintenance.py`

## 📚 Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Database Design Best Practices](https://www.postgresql.org/docs/current/ddl.html)
- [Performance Tuning Guide](https://www.postgresql.org/docs/current/performance-tips.html)
- [Backup and Recovery](https://www.postgresql.org/docs/current/backup.html)

