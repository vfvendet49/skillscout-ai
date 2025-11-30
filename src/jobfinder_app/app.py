# streamlit_app.py — JobFinder AI main Streamlit application
import streamlit as st
import requests, json
from pathlib import Path
import os

# Resolve API base URL from (in order): environment variable, Streamlit secrets, then default
API = os.getenv("API_BASE")
if not API:
    try:
        # Access Streamlit secrets safely — if secrets are not set, this can raise.
        API = st.secrets.get("API_BASE")
    except Exception:
        API = None
if not API:
    API = "http://localhost:8000"

st.set_page_config(page_title="JobFinder AI", layout="wide")

st.title("JobFinder AI")

tab1, tab2, tab3, tab4 = st.tabs(["Profile & Prefs", "Uploads", "Results", "Job Detail"])

with tab1:
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

with tab2:
    st.subheader("Upload resumes & cover letters per purpose")
    purpose = st.text_input("Purpose (e.g., consulting, product, ops)", value="ops")
    rfile = st.file_uploader("Resume (.pdf or .docx)", type=["pdf","docx"])
    cfile = st.file_uploader("Cover Letter (.pdf or .docx)", type=["pdf","docx"])
    if st.button("Upload"):
        files = {}
        if rfile:
            files["resume"] = (rfile.name, rfile.read(), rfile.type)
        if cfile:
            files["cover"] = (cfile.name, cfile.read(), cfile.type)
        data = {"purpose": purpose}
        try:
            r = requests.post(f"{API}/uploads", data=data, files=files, timeout=5)
            st.success("Uploaded!") if r.ok else st.error(r.text)
        except requests.exceptions.ConnectionError:
            st.warning(f"ℹ️ Backend not running ({API}). Files validated locally. Backend will process when available.")
        except Exception as e:
            st.error(f"Error: {str(e)}")

with tab3:
    st.subheader("Search Jobs")
    limit = st.slider("How many to fetch (top N)", 5, 50, 20)
    if st.button("Run Search"):
        # You would fetch the saved profile/preferences from backend in real app.
        # For demo, ask backend to use stored state or pass st.session_state.
        # Here we just simulate by reusing the form payload you saved already on /profile (backend keeps it).
        # Build a SearchRequest by asking backend for the saved profile (skipped in minimal slice).
        # For now, reuse the last known values on client if needed.
        search_req = {
            "user_profile": {
                "name": name, "skills": [s.strip() for s in skills if s.strip()],
                "industries": [i.strip() for i in industries if i.strip()],
                "experience_level": exp_level,
                "target_titles": [t.strip() for t in target_titles if t.strip()],
            },
            "user_preferences": {
                "location": {"city": city, "state": state, "country": country, "remote": remote, "radius_miles": radius},
                "salary": {"min": int(min_sal), "max": int(max_sal)},
                "employment_type": emp_types,
                "exclude_keywords": [k.strip() for k in exclude_kw if k.strip()],
                "company_preferences": {"preferred": [c.strip() for c in pref_companies if c.strip()],
                                        "avoid": [c.strip() for c in avoid_companies if c.strip()]},
                "job_age_limit_days": int(max_age)
            },
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

    # show results
    jobs = st.session_state.get("jobs", [])
    for j in jobs:
        with st.container(border=True):
            st.markdown(f"**{j['title']}** — {j['company']} · {j['location']}  \n[{j['url']}]({j['url']})")
            st.caption(f"Source: {j['source']}  ·  Posted: {j.get('posted_at','N/A')}")
            if st.button("Open", key=j["id"]):
                st.session_state["selected_job"] = j
                st.switch_page("streamlit_app.py")  # same page, flips to tab4 automatically below

with tab4:
    st.subheader("Job Detail & AI Tweaks")
    sel = st.session_state.get("selected_job")
    if sel:
        st.markdown(f"### {sel['title']} @ {sel['company']}")
        with st.expander("Job Description"):
            st.write(sel["description"][:3000])

        # pick which uploaded purpose to compare
        purpose_for_match = st.text_input("Which resume set to use?", value="ops")
        resume_txt = st.text_area("Paste resume text (temp)", placeholder="(In production, load + parse server-side)")
        cover_txt = st.text_area("Paste cover letter text (optional)")

        threshold = st.slider("Match threshold", 0.5, 0.95, 0.70, 0.01)

        if st.button("Compute Match"):
            payload = {"job": sel, "resume_text": resume_txt, "cover_text": cover_txt, "threshold": threshold}
            try:
                r = requests.post(f"{API}/match", json=payload, timeout=10)
                if r.ok:
                    m = r.json()
                    st.metric("Score", m["score"])
                    st.progress(min(1.0, m["score"]))
                    st.caption(f"Coverage: {m['coverage']} · Cosine: {m['cosine']}")
                    for tw in m["tweaks"]:
                        st.warning(f"{tw['type'].title()} — {tw['message']}")
                        st.write(", ".join(tw["keywords"]))
                else:
                    st.error(r.text)
            except requests.exceptions.ConnectionError:
                st.warning(f"ℹ️ Backend not running ({API}). Match computation requires backend API.")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    else:
        st.info("Select a job in the Results tab to view details.")
