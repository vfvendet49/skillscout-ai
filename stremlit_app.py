# streamlit_app.py
import streamlit as st
import requests, json
import os
from pathlib import Path

# ==============================================
# API BASE URL DETECTION
# ==============================================
API = os.getenv("API_BASE")

if not API:
    try:
        API = st.secrets.get("API_BASE")
    except:
        API = None

# Default for deployed version
if not API:
    API = "https://skillscout-ai-1.onrender.com"


# ==============================================
# PAGE CONFIG
# ==============================================
st.set_page_config(page_title="SkillScout AI", layout="wide")
st.title("SkillScout AI")


# ==============================================
# API HEALTH CHECK
# ==============================================
with st.sidebar:
    st.subheader("API Connection")
    st.write(f"Backend: {API}")

    try:
        health = requests.get(f"{API}/health", timeout=3)
        if health.status_code == 200:
            st.success("Connected")
        else:
            st.warning("Backend reachable but returned an error")
    except:
        st.error("Cannot reach backend")


# ==============================================
# TABS
# ==============================================
tab1, tab2, tab3, tab4 = st.tabs([
    "Profile & Prefs",
    "Uploads",
    "Results",
    "Job Detail"
])


# ==========================================================
# TAB 1 — PROFILE
# ==========================================================
with tab1:
    st.subheader("User Profile")

    name = st.text_input("Name")

    skills_raw = st.text_area("Skills (comma-separated)")
    skills = [s.strip() for s in skills_raw.split(",") if s.strip()]

    industries_raw = st.text_input("Industries (comma-separated)")
    industries = [i.strip() for i in industries_raw.split(",") if i.strip()]

    exp_level = st.selectbox("Experience level", 
                             ["entry", "junior", "mid-senior", "director", "executive"])

    titles_raw = st.text_input("Target titles (comma-separated)")
    target_titles = [t.strip() for t in titles_raw.split(",") if t.strip()]


    # Preferences Section
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
        min_sal = st.number_input("Minimum Salary", 0, 500000, 80000)
        max_sal = st.number_input("Maximum Salary", 0, 500000, 150000)

    emp_types = st.multiselect(
        "Employment Type",
        ["full-time", "part-time", "contract"],
        default=["full-time"]
    )

    exclude_raw = st.text_input("Exclude keywords (comma-separated)", value="warehouse, entry-level")
    exclude_kw = [k.strip() for k in exclude_raw.split(",") if k.strip()]

    pref_companies_raw = st.text_input("Preferred companies", value="Amazon, DHL, Coca-Cola")
    pref_companies = [c.strip() for c in pref_companies_raw.split(",") if c.strip()]

    avoid_raw = st.text_input("Avoid companies", value="Uber")
    avoid_companies = [c.strip() for c in avoid_raw.split(",") if c.strip()]

    max_age = st.slider("Job age limit (days)", 1, 90, 45)


    # SAVE PROFILE BUTTON
    if st.button("Save Profile"):
        payload = {
            "profile": {
                "name": name,
                "skills": skills,
                "industries": industries,
                "experience_level": exp_level,
                "target_titles": target_titles,
            },
            "preferences": {
                "location": {
                    "city": city,
                    "state": state,
                    "country": country,
                    "remote": remote,
                    "radius_miles": radius
                },
                "salary": {"min": min_sal, "max": max_sal},
                "employment_type": emp_types,
                "exclude_keywords": exclude_kw,
                "company_preferences": {
                    "preferred": pref_companies,
                    "avoid": avoid_companies
                },
                "job_age_limit_days": max_age
            }
        }

        try:
            res = requests.post(f"{API}/profile", json=payload, timeout=5)
            if res.status_code == 200:
                st.success("Profile saved successfully")
            else:
                st.error(f"Error {res.status_code}: {res.text}")
        except Exception as e:
            st.error(f"Failed to contact backend: {e}")


# ==========================================================
# TAB 2 — UPLOADS
# ==========================================================
with tab2:
    st.subheader("Upload resumes & cover letters per category")

    purpose = st.text_input("Purpose", value="ops")

    rfile = st.file_uploader("Upload Resume", type=["pdf", "docx"])
    cfile = st.file_uploader("Upload Cover Letter", type=["pdf", "docx"])

    if st.button("Upload Files"):
        files = {}
        if rfile:
            files["resume"] = (rfile.name, rfile.read(), rfile.type)
        if cfile:
            files["cover"] = (cfile.name, cfile.read(), cfile.type)

        try:
            res = requests.post(f"{API}/uploads", data={"purpose": purpose}, files=files, timeout=10)
            if res.status_code == 200:
                st.success("Files uploaded successfully")
            else:
                st.error(f"Upload error {res.status_code}: {res.text}")
        except Exception as e:
            st.error(f"Error: {e}")


# ==========================================================
# TAB 3 — JOB RESULTS
# ==========================================================
with tab3:
    st.subheader("Search Jobs")

    limit = st.slider("How many jobs to fetch", 5, 50, 20)

    if st.button("Run Search"):
        search_req = {
            "user_profile": {
                "name": name,
                "skills": skills,
                "industries": industries,
                "experience_level": exp_level,
                "target_titles": target_titles,
            },
            "user_preferences": {
                "location": {"city": city, "state": state, "country": country, "remote": remote, "radius_miles": radius},
                "salary": {"min": min_sal, "max": max_sal},
                "employment_type": emp_types,
                "exclude_keywords": exclude_kw,
                "company_preferences": {
                    "preferred": pref_companies,
                    "avoid": avoid_companies
                },
                "job_age_limit_days": max_age
            },
            "limit": limit
        }

        try:
            res = requests.post(f"{API}/search", json=search_req, timeout=10)
            if res.status_code == 200:
                st.session_state["jobs"] = res.json()
                st.success(f"Found {len(st.session_state['jobs'])} jobs")
            else:
                st.error(f"Search error {res.status_code}: {res.text}")

        except Exception as e:
            st.error(f"Error: {e}")


    # DISPLAY RESULTS
    jobs = st.session_state.get("jobs", [])

    for job in jobs:
        with st.container():
            st.markdown(f"### {job['title']} — {job['company']}")
            st.write(job["location"])
            st.write(f"[Job Link]({job['url']})")
            st.caption(f"Source: {job['source']} · Posted: {job.get('posted_at','N/A')}")

            if st.button("Open Details", key=job["id"]):
                st.session_state["selected_job"] = job


# ==========================================================
# TAB 4 — DETAIL VIEW
# ==========================================================
with tab4:
    st.subheader("Job Detail")

    selected = st.session_state.get("selected_job")

    if not selected:
        st.info("Select a job from the Results tab to view details.")
    else:
        st.markdown(f"## {selected['title']} @ {selected['company']}")
        st.write(selected["location"])

        with st.expander("Job Description"):
            st.write(selected["description"][:5000])

        # Resume comparison
        resume_text = st.text_area("Paste resume text")
        cover_text = st.text_area("Paste cover letter text (optional)")

        threshold = st.slider("Match threshold", 0.5, 0.95, 0.70)

        if st.button("Compute Match"):
            try:
                payload = {
                    "job": selected,
                    "resume_text": resume_text,
                    "cover_text": cover_text,
                    "threshold": threshold
                }
                res = requests.post(f"{API}/match", json=payload, timeout=10)
                if res.status_code == 200:
                    match_result = res.json()
                    st.metric("Match Score", match_result["score"])
                    st.progress(match_result["score"])
                    st.caption(f"Coverage: {match_result['coverage']}, Cosine: {match_result['cosine']}")

                    for tweak in match_result.get("tweaks", []):
                        st.warning(tweak["message"])
                else:
                    st.error(f"Match error: {res.text}")
            except Exception as e:
                st.error(str(e))
