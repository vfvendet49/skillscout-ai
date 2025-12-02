import streamlit as st
import requests
from typing import Optional, Dict, Any

def get_api_base() -> str:
    """Get the API base URL from secrets with fallback."""
    api_base = st.secrets.get("API_BASE", "http://localhost:8000")
    print(f"DEBUG: Using API_BASE = {api_base}")
    return api_base

def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Fetch user profile from backend."""
    try:
        api_url = f"{get_api_base()}/profile/{user_id}"
        print(f"DEBUG: GET {api_url}")
        response = requests.get(api_url, timeout=30)
        print(f"DEBUG: Response status {response.status_code}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"❌ Error fetching profile: {str(e)}")
        return None

def save_user_profile(user_id: str, profile_data: Dict[str, Any]) -> bool:
    """Save user profile to backend."""
    try:
        api_url = f"{get_api_base()}/profile/{user_id}"
        print(f"DEBUG: POST {api_url}")
        print(f"DEBUG: Data: {profile_data}")
        response = requests.post(api_url, json=profile_data, timeout=30)
        print(f"DEBUG: Response status {response.status_code}")
        print(f"DEBUG: Response body: {response.text}")
        response.raise_for_status()
        st.success("✅ Profile saved successfully!")
        return True
    except Exception as e:
        st.error(f"❌ Error saving profile: {str(e)}")
        print(f"DEBUG: Exception: {e}")
        return False

def search_jobs(user_id: str, query: str, location: Optional[str] = None) -> Optional[list]:
    """Search for jobs using backend."""
    try:
        api_url = f"{get_api_base()}/search"
        payload = {"user_id": user_id, "query": query, "location": location}
        response = requests.post(api_url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"❌ Error searching jobs: {str(e)}")
        return None

def upload_resume(user_id: str, file_content: bytes, filename: str) -> Optional[Dict[str, Any]]:
    """Upload resume to backend."""
    try:
        api_url = f"{get_api_base()}/uploads"
        files = {"file": (filename, file_content)}
        data = {"user_id": user_id, "upload_type": "resume"}
        response = requests.post(api_url, files=files, data=data, timeout=60)
        response.raise_for_status()
        st.success(f"✅ Resume uploaded: {filename}")
        return response.json()
    except Exception as e:
        st.error(f"❌ Error uploading resume: {str(e)}")
        return None

def get_job_matches(user_id: str) -> Optional[list]:
    """Get matching jobs for user from backend."""
    try:
        api_url = f"{get_api_base()}/match"
        response = requests.get(api_url, params={"user_id": user_id}, timeout=60)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"❌ Error fetching matches: {str(e)}")
        return None

def test_backend_connection() -> bool:
    """Test if backend is accessible."""
    try:
        api_url = f"{get_api_base()}/health"
        print(f"DEBUG: Testing connection to {api_url}")
        response = requests.get(api_url, timeout=10)
        is_healthy = response.status_code == 200
        print(f"DEBUG: Backend health check: {is_healthy}")
        return is_healthy
    except Exception as e:
        print(f"DEBUG: Connection failed: {e}")
        st.warning(f"⚠️ Backend connection failed: {str(e)}")
        return False
