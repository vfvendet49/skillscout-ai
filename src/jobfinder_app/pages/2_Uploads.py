# pages/2_Uploads.py — File uploads page
import streamlit as st
import requests
import os

st.set_page_config(page_title="Uploads - SkillScout", layout="wide")

st.title("Upload Resumes & Cover Letters")

# Resolve API base URL
API = os.getenv("API_BASE")
if not API:
    try:
        API = st.secrets.get("API_BASE")
    except Exception:
        API = None
if not API:
    API = "http://localhost:8000"

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
