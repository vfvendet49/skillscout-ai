# pages/4_Job_Detail.py — Job detail & matching page
import streamlit as st
import requests
import os

st.set_page_config(page_title="Job Detail - SkillScout", layout="wide")

st.title("Job Detail & AI Tweaks")

# Resolve API base URL
API = os.getenv("API_BASE")
if not API:
    try:
        API = st.secrets.get("API_BASE")
    except Exception:
        API = None
if not API:
    API = "http://localhost:8000"

sel = st.session_state.get("selected_job")
if sel:
    st.markdown(f"### {sel.get('title', 'N/A')} @ {sel.get('company', 'N/A')}")
    with st.expander("Job Description"):
        st.write(sel.get("description", "N/A")[:3000])

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
                st.metric("Score", m.get("score", "N/A"))
                st.progress(min(1.0, m.get("score", 0)))
                st.caption(f"Coverage: {m.get('coverage', 'N/A')} · Cosine: {m.get('cosine', 'N/A')}")
                for tw in m.get("tweaks", []):
                    st.warning(f"{tw.get('type', '').title()} — {tw.get('message', '')}")
                    st.write(", ".join(tw.get("keywords", [])))
            else:
                st.error(r.text)
        except requests.exceptions.ConnectionError:
            st.warning(f"ℹ️ Backend not running ({API}). Match computation requires backend API.")
        except Exception as e:
            st.error(f"Error: {str(e)}")
else:
    st.info("Select a job in the Results tab to view details.")
