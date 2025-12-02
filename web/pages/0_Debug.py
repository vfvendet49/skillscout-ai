import streamlit as st
import requests

st.set_page_config(page_title="Debug", layout="wide")
st.title("🔧 Debug Information")

# Get API base
api_base = st.secrets.get("API_BASE", "http://localhost:8000")
st.write(f"**API_BASE from secrets:** `{api_base}`")

# Test connection
st.subheader("Test Backend Connection")
col1, col2 = st.columns(2)

with col1:
    if st.button("🧪 Test /health"):
        try:
            url = f"{api_base}/health"
            st.write(f"Testing: `{url}`")
            resp = requests.get(url, timeout=10)
            st.write(f"Status: {resp.status_code}")
            st.json(resp.json())
        except Exception as e:
            st.error(f"Failed: {e}")

with col2:
    if st.button("🧪 Test /test"):
        try:
            url = f"{api_base}/test"
            st.write(f"Testing: `{url}`")
            resp = requests.get(url, timeout=10)
            st.write(f"Status: {resp.status_code}")
            st.json(resp.json())
        except Exception as e:
            st.error(f"Failed: {e}")

st.subheader("Test Profile Endpoint")
if st.button("🧪 Test POST /profile/test_user"):
    try:
        url = f"{api_base}/profile/test_user"
        st.write(f"Testing: `{url}`")
        payload = {"name": "Test", "email": "test@test.com"}
        st.write(f"Payload: {payload}")
        resp = requests.post(url, json=payload, timeout=10)
        st.write(f"Status: {resp.status_code}")
        st.json(resp.json())
    except Exception as e:
        st.error(f"Failed: {e}")
