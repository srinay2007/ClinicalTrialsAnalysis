-- Enhanced Clinical Trials Database Schema
-- This schema provides better organization and relationships for clinical trial data

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS trial_locations CASCADE;
DROP TABLE IF EXISTS trial_outcomes CASCADE;
DROP TABLE IF EXISTS trial_arms_interventions CASCADE;
DROP TABLE IF EXISTS trial_basic_info CASCADE;
DROP TABLE IF EXISTS trial_descriptions CASCADE;
DROP TABLE IF EXISTS trial_eligibility CASCADE;
DROP TABLE IF EXISTS trial_contacts CASCADE;
DROP TABLE IF EXISTS trial_keywords CASCADE;
DROP TABLE IF EXISTS trial_conditions CASCADE;
DROP TABLE IF EXISTS trial_interventions CASCADE;

-- Main trial information table
CREATE TABLE trial_basic_info (
    id SERIAL PRIMARY KEY,
    nct_id VARCHAR(20) UNIQUE NOT NULL,
    protocol_section_id VARCHAR(50),
    organization_name VARCHAR(500),
    organization_type VARCHAR(100),
    brief_title TEXT,
    official_title TEXT,
    status VARCHAR(100),
    phase VARCHAR(100),
    study_type VARCHAR(100),
    enrollment_count INTEGER,
    enrollment_type VARCHAR(100),
    start_date DATE,
    completion_date DATE,
    primary_completion_date DATE,
    is_fda_regulated_drug BOOLEAN,
    is_fda_regulated_device BOOLEAN,
    is_unapproved_device BOOLEAN,
    is_ppsd BOOLEAN,
    is_us_export BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trial descriptions table
CREATE TABLE trial_descriptions (
    id SERIAL PRIMARY KEY,
    nct_id VARCHAR(20) REFERENCES trial_basic_info(nct_id) ON DELETE CASCADE,
    brief_summary TEXT,
    detailed_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Eligibility criteria table
CREATE TABLE trial_eligibility (
    id SERIAL PRIMARY KEY,
    nct_id VARCHAR(20) REFERENCES trial_basic_info(nct_id) ON DELETE CASCADE,
    inclusion_criteria TEXT,
    exclusion_criteria TEXT,
    minimum_age VARCHAR(50),
    maximum_age VARCHAR(50),
    gender VARCHAR(50),
    healthy_volunteers BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Study arms and interventions table
CREATE TABLE trial_arms_interventions (
    id SERIAL PRIMARY KEY,
    nct_id VARCHAR(20) REFERENCES trial_basic_info(nct_id) ON DELETE CASCADE,
    arm_group_label VARCHAR(500),
    arm_group_type VARCHAR(500),
    arm_group_description TEXT,
    intervention_name VARCHAR(500),
    intervention_type VARCHAR(500),
    intervention_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Primary and secondary outcomes table
CREATE TABLE trial_outcomes (
    id SERIAL PRIMARY KEY,
    nct_id VARCHAR(20) REFERENCES trial_basic_info(nct_id) ON DELETE CASCADE,
    outcome_type VARCHAR(100), -- 'PRIMARY' or 'SECONDARY'
    outcome_measure TEXT,
    outcome_description TEXT,
    outcome_time_frame TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Study locations table
CREATE TABLE trial_locations (
    id SERIAL PRIMARY KEY,
    nct_id VARCHAR(20) REFERENCES trial_basic_info(nct_id) ON DELETE CASCADE,
    facility_name VARCHAR(500),
    facility_address TEXT,
    facility_city VARCHAR(200),
    facility_state VARCHAR(200),
    facility_zip VARCHAR(50),
    facility_country VARCHAR(200),
    facility_contact_name VARCHAR(200),
    facility_contact_phone VARCHAR(100),
    facility_contact_email VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trial contacts table
CREATE TABLE trial_contacts (
    id SERIAL PRIMARY KEY,
    nct_id VARCHAR(20) REFERENCES trial_basic_info(nct_id) ON DELETE CASCADE,
    contact_type VARCHAR(100), -- 'PRIMARY', 'BACKUP', 'OVERALL_OFFICIAL'
    contact_name VARCHAR(200),
    contact_phone VARCHAR(100),
    contact_email VARCHAR(200),
    contact_affiliation VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trial keywords table
CREATE TABLE trial_keywords (
    id SERIAL PRIMARY KEY,
    nct_id VARCHAR(20) REFERENCES trial_basic_info(nct_id) ON DELETE CASCADE,
    keyword VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trial conditions table
CREATE TABLE trial_conditions (
    id SERIAL PRIMARY KEY,
    nct_id VARCHAR(20) REFERENCES trial_basic_info(nct_id) ON DELETE CASCADE,
    condition_name VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trial interventions table (separate from arms)
CREATE TABLE trial_interventions (
    id SERIAL PRIMARY KEY,
    nct_id VARCHAR(20) REFERENCES trial_basic_info(nct_id) ON DELETE CASCADE,
    intervention_name VARCHAR(500),
    intervention_type VARCHAR(500),
    intervention_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_trial_basic_info_nct_id ON trial_basic_info(nct_id);
CREATE INDEX idx_trial_basic_info_status ON trial_basic_info(status);
CREATE INDEX idx_trial_basic_info_phase ON trial_basic_info(phase);
CREATE INDEX idx_trial_basic_info_study_type ON trial_basic_info(study_type);
CREATE INDEX idx_trial_basic_info_organization ON trial_basic_info(organization_name);
CREATE INDEX idx_trial_basic_info_start_date ON trial_basic_info(start_date);
CREATE INDEX idx_trial_basic_info_completion_date ON trial_basic_info(completion_date);

CREATE INDEX idx_trial_descriptions_nct_id ON trial_descriptions(nct_id);
CREATE INDEX idx_trial_eligibility_nct_id ON trial_eligibility(nct_id);
CREATE INDEX idx_trial_arms_interventions_nct_id ON trial_arms_interventions(nct_id);
CREATE INDEX idx_trial_outcomes_nct_id ON trial_outcomes(nct_id);
CREATE INDEX idx_trial_locations_nct_id ON trial_locations(nct_id);
CREATE INDEX idx_trial_contacts_nct_id ON trial_contacts(nct_id);
CREATE INDEX idx_trial_keywords_nct_id ON trial_keywords(nct_id);
CREATE INDEX idx_trial_conditions_nct_id ON trial_conditions(nct_id);
CREATE INDEX idx_trial_interventions_nct_id ON trial_interventions(nct_id);

-- Create full-text search indexes for better search capabilities
CREATE INDEX idx_trial_basic_info_title_search ON trial_basic_info USING gin(to_tsvector('english', brief_title || ' ' || official_title));
CREATE INDEX idx_trial_descriptions_summary_search ON trial_descriptions USING gin(to_tsvector('english', brief_summary || ' ' || detailed_description));
CREATE INDEX idx_trial_conditions_search ON trial_conditions USING gin(to_tsvector('english', condition_name));
CREATE INDEX idx_trial_keywords_search ON trial_keywords USING gin(to_tsvector('english', keyword));

-- Create a view for easy querying of complete trial information
CREATE VIEW trial_complete_info AS
SELECT 
    tbi.*,
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
LEFT JOIN trial_eligibility te ON tbi.nct_id = te.nct_id;

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update the updated_at column
CREATE TRIGGER update_trial_basic_info_updated_at BEFORE UPDATE ON trial_basic_info
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions to clinicai user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO clinicai;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO clinicai;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO clinicai;

