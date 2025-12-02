"""
SQLAlchemy models for JobFinder app.
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class UserProfile(Base):
    """Store user profile information"""
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), unique=True, index=True)  # unique identifier
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    location = Column(String(255), nullable=True)
    resume_text = Column(Text, nullable=True)
    profile_data = Column(JSON, nullable=True)  # Store full profile as JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserPreferences(Base):
    """Store user job preferences"""
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), unique=True, index=True)
    target_titles = Column(JSON, nullable=True)  # List of target job titles
    target_skills = Column(JSON, nullable=True)  # List of required skills
    industry = Column(String(255), nullable=True)
    location_preference = Column(String(255), nullable=True)
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    preferences_data = Column(JSON, nullable=True)  # Store full preferences as JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserUpload(Base):
    """Store user file uploads (resumes, cover letters, etc.)"""
    __tablename__ = "user_uploads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), index=True)
    purpose = Column(String(50), nullable=False)  # e.g., "consulting", "product", "marketing"
    resume_path = Column(String(500), nullable=True)
    cover_letter_path = Column(String(500), nullable=True)
    file_names = Column(JSON, nullable=True)  # Store original file names
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
