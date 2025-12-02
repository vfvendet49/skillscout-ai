"""Pydantic schemas for request/response validation"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class UserProfile(BaseModel):
    name: str
    skills: List[str]
    industries: List[str]
    experience_level: str
    target_titles: List[str]


class LocationPref(BaseModel):
    city: str
    state: str
    country: str
    remote: bool = False
    radius_miles: Optional[int] = 25


class SalaryPref(BaseModel):
    min: Optional[int] = None
    max: Optional[int] = None


class CompanyPrefs(BaseModel):
    preferred: List[str] = []
    avoid: List[str] = []


class UserPreferences(BaseModel):
    location: LocationPref
    salary: Optional[SalaryPref] = None
    employment_type: List[str] = ["full-time"]
    exclude_keywords: List[str] = []
    company_preferences: CompanyPrefs = CompanyPrefs()
    job_age_limit_days: int = 45


class TheirStackSearch(BaseModel):
    """TheirStack API search parameters"""
    q: str
    title: Optional[str] = None
    skills: List[str] = []
    location: Optional[str] = None
    country: Optional[str] = None
    remote: Optional[bool] = None
    posted_at_max_age_days: Optional[int] = None
    salary_gte: Optional[int] = None
    salary_lte: Optional[int] = None
    employment_type: List[str] = []
    exclude: List[str] = []
    company: List[str] = []
    limit: int = 50


class SearchRequest(BaseModel):
    user_profile: UserProfile
    user_preferences: UserPreferences
    limit: int = 50


class Job(BaseModel):
    id: str
    title: str
    company: str
    location: str
    url: str
    description: str
    posted_at: Optional[str] = None
    source: str  # theirstack|indeed|linkedin


class MatchInput(BaseModel):
    job: Job
    resume_text: str
    cover_text: Optional[str] = None
    threshold: float = 0.70
