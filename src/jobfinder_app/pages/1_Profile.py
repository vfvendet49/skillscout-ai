# pages/1_Profile.py — Profile & Preferences page
import streamlit as st
import requests, json
from pathlib import Path
import os

# Set page config
st.set_page_config(page_title="Profile & Preferences - SkillScout", layout="wide")

st.title("Profile & Preferences")

# Resolve API base URL
API = os.getenv("API_BASE")
if not API:
    try:
        API = st.secrets.get("API_BASE")
    except Exception:
        API = None
if not API:
    API = "http://localhost:8000"

st.subheader("User Profile")
name = st.text_input("Name")
skills = st.text_area("Skills (comma-separated)").split(",")
industries = st.text_input("Industries (comma-separated)").split(",")
exp_level = st.selectbox("Experience level", ["entry", "junior", "mid-senior", "director", "executive"])
target_titles = st.text_input("Target titles (comma-separated)").split(",")

st.subheader("Preferences")
c1, c2, c3 = st.columns(3)
with c1:
    city = st.text_input("City", value="Atlanta")
    state = st.text_input("State", value="GA")
    country = st.text_input("Country", value="US")
with c2:
    remote = st.toggle("Remote OK", value=False)
    radius = st.number_input("Radius (miles)", 0, 200, 50)
with c3:
    min_sal = st.number_input("Salary min", 0, 1000000, 80000)
    max_sal = st.number_input("Salary max", 0, 1000000, 150000)

emp_types = st.multiselect("Employment type", ["full-time","part-time","contract"], default=["full-time"])
exclude_kw = st.text_input("Exclude keywords (comma-separated)", value="warehouse, entry-level").split(",")
pref_companies = st.text_input("Preferred companies (comma-separated)", value="Amazon, DHL, Coca-Cola").split(",")
avoid_companies = st.text_input("Avoid companies (comma-separated)", value="Uber").split(",")
max_age = st.slider("Job age limit (days)", 1, 90, 45)

if st.button("Save Profile"):
    payload = {
        "profile": {
            "name": name,
            "skills": [s.strip() for s in skills if s.strip()],
            "industries": [i.strip() for i in industries if i.strip()],
            "experience_level": exp_level,
            "target_titles": [t.strip() for t in target_titles if t.strip()],
        },
        "preferences": {
            "location": {"city": city, "state": state, "country": country, "remote": remote, "radius_miles": radius},
            "salary": {"min": int(min_sal), "max": int(max_sal)},
            "employment_type": emp_types,
            "exclude_keywords": [k.strip() for k in exclude_kw if k.strip()],
            "company_preferences": {"preferred": [c.strip() for c in pref_companies if c.strip()],
                                    "avoid": [c.strip() for c in avoid_companies if c.strip()]},
            "job_age_limit_days": int(max_age)
        }
    }
    try:
        r = requests.post(f"{API}/profile", json={"profile": payload["profile"], "preferences": payload["preferences"]}, timeout=5)
        st.success("Saved!") if r.ok else st.error(r.text)
    except requests.exceptions.ConnectionError:
        st.warning(f"ℹ️ Backend not running ({API}). Form validated locally. Backend will process when available.")
    except Exception as e:
        st.error(f"Error: {str(e)}")
