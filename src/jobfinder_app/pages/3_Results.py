# pages/3_Results.py — Job search results page
import streamlit as st
import requests
import os

st.set_page_config(page_title="Results - SkillScout", layout="wide")

st.title("Search Jobs")

# Resolve API base URL
API = os.getenv("API_BASE")
if not API:
    try:
        API = st.secrets.get("API_BASE")
    except Exception:
        API = None
if not API:
    API = "http://localhost:8000"

limit = st.slider("How many to fetch (top N)", 5, 50, 20)

if st.button("Run Search"):
    # Build search request from session state or form
    search_req = {
        "limit": int(limit)
    }
    try:
        r = requests.post(f"{API}/search", json=search_req, timeout=10)
        if r.ok:
            st.session_state["jobs"] = r.json()
            st.success(f"Found {len(st.session_state['jobs'])} jobs")
        else:
            st.error(r.text)
    except requests.exceptions.ConnectionError:
        st.warning(f"ℹ️ Backend not running ({API}). Search request prepared. Connect backend to execute SkillScout job search.")
    except Exception as e:
        st.error(f"Error: {str(e)}")

# Show results
jobs = st.session_state.get("jobs", [])
for j in jobs:
    with st.container(border=True):
        st.markdown(f"**{j.get('title', 'N/A')}** — {j.get('company', 'N/A')} · {j.get('location', 'N/A')}  \n[{j.get('url', '#')}]({j.get('url', '#')})")
        st.caption(f"Source: {j.get('source', 'N/A')}  ·  Posted: {j.get('posted_at','N/A')}")
        if st.button("View Details", key=j.get("id", str(j))):
            st.session_state["selected_job"] = j
            st.switch_page("pages/4_Job_Detail.py")
