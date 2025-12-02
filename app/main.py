# app/main.py - SkillScout API
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Dict, Any, Optional
from pydantic import BaseModel
from .schemas import MatchInput, UserProfile, UserPreferences, SearchRequest
from .services.matching import compute_match

# Load environment variables
load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./jobfinder.db")
if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"connect_timeout": 10})
else:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine)

# Import models
try:
    from .models import Base, UserProfile as UserProfileModel
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"DB init warning: {e}")

# Create FastAPI app
app = FastAPI(title="SkillScout API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ===== PYDANTIC MODELS =====
class ProfileData(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    title: Optional[str] = None
    location: Optional[str] = None
    years_experience: Optional[int] = None
    job_types: Optional[list] = None
    industries: Optional[list] = None
    min_salary: Optional[int] = None
    max_salary: Optional[int] = None

# ===== ENDPOINTS =====

@app.get("/")
def root():
    """Root endpoint"""
    return {"status": "running", "api": "SkillScout"}

@app.get("/health")
def health():
    """Health check"""
    return {"status": "healthy"}

@app.get("/test")
def test_endpoint():
    """Test endpoint for debugging"""
    return {
        "message": "Backend is working!",
        "endpoints": {
            "GET /profile/{user_id}": "Fetch user profile",
            "POST /profile/{user_id}": "Save user profile (send JSON body)",
            "POST /search": "Search jobs",
            "POST /uploads": "Upload files",
            "GET /docs": "API documentation"
        }
    }

@app.get("/profile/{user_id}")
def get_profile(user_id: str):
    """Get profile - returns empty dict for now"""
    try:
        db = SessionLocal()
        profile = db.query(UserProfileModel).filter(UserProfileModel.user_id == user_id).first()
        db.close()
        if profile and profile.profile_data:
            return profile.profile_data
        return {}
    except Exception as e:
        return {"error": str(e)}

@app.post("/profile")
def save_profile(body: Dict[str, Any] = Body(...)):
    """Save profile - accepts profile and preferences from Streamlit app"""
    try:
        db = SessionLocal()
        # Use a default user_id or extract from body if provided
        user_id = body.get("user_id", "default_user")
        profile_data = body.get("profile", {})
        preferences_data = body.get("preferences", {})
        
        # Combine profile and preferences
        combined_data = {
            "profile": profile_data,
            "preferences": preferences_data
        }
        
        existing = db.query(UserProfileModel).filter(UserProfileModel.user_id == user_id).first()
        if existing:
            existing.profile_data = combined_data
        else:
            new_profile = UserProfileModel(user_id=user_id, profile_data=combined_data)
            db.add(new_profile)
        
        db.commit()
        db.close()
        return {"ok": True, "user_id": user_id, "message": "Profile saved"}
    except Exception as e:
        db.rollback()
        db.close()
        return {"ok": False, "error": str(e)}

@app.post("/profile/{user_id}")
def save_profile_by_id(user_id: str, body: ProfileData = Body(...)):
    """Save profile - accepts ProfileData model (legacy endpoint)"""
    try:
        db = SessionLocal()
        profile_dict = body.dict(exclude_none=True)
        
        existing = db.query(UserProfileModel).filter(UserProfileModel.user_id == user_id).first()
        if existing:
            existing.profile_data = profile_dict
        else:
            new_profile = UserProfileModel(user_id=user_id, profile_data=profile_dict)
            db.add(new_profile)
        
        db.commit()
        db.close()
        return {"ok": True, "user_id": user_id, "message": "Profile saved"}
    except Exception as e:
        db.rollback()
        db.close()
        return {"ok": False, "error": str(e)}

@app.post("/search")
def search(body: SearchRequest = Body(...)):
    """Search jobs - accepts SearchRequest with user_profile and user_preferences"""
    try:
        # TODO: Integrate with TheirStack API or other job search services
        # For now, return mock data based on the search request
        limit = body.limit or 20
        
        # Mock job results
        jobs = [
            {
                "id": f"job_{i}",
                "title": body.user_profile.target_titles[0] if body.user_profile.target_titles else "Software Engineer",
                "company": f"Tech Corp {i}",
                "location": f"{body.user_preferences.location.city}, {body.user_preferences.location.state}",
                "description": f"Great opportunity for {body.user_profile.experience_level} level position",
                "url": f"https://example.com/job/{i}",
                "posted_at": "2024-01-15",
                "source": "theirstack"
            }
            for i in range(1, min(limit + 1, 11))
        ]
        
        return jobs
    except Exception as e:
        return {"error": str(e)}

@app.post("/uploads")
def upload():
    """Upload placeholder"""
    return {"ok": True}

@app.post("/match")
def match_job(body: MatchInput = Body(...)):
    """Compute match score between job and resume/cover letter"""
    try:
        result = compute_match(
            job_description=body.job.description,
            resume_text=body.resume_text,
            cover_text=body.cover_text,
            threshold=body.threshold
        )
        return result
    except Exception as e:
        return {"ok": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
