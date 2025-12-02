-- PostgreSQL initialization script for SkillScout AI database
-- This creates all necessary tables for the application

-- User Profiles table
CREATE TABLE IF NOT EXISTS user_profiles (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(20),
    location VARCHAR(255),
    resume_text TEXT,
    profile_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);

-- User Preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    target_titles JSONB,
    target_skills JSONB,
    industry VARCHAR(255),
    location_preference VARCHAR(255),
    salary_min INTEGER,
    salary_max INTEGER,
    preferences_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);

-- User Uploads table
CREATE TABLE IF NOT EXISTS user_uploads (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    purpose VARCHAR(50) NOT NULL,
    resume_path VARCHAR(500),
    cover_letter_path VARCHAR(500),
    file_names JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_uploads_user_id ON user_uploads(user_id);

