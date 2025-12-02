import streamlit as st
from web_api_client import upload_resume, test_backend_connection

st.set_page_config(page_title="Upload Documents", layout="wide")
st.title("📤 Upload Resumes & Documents")

# Check backend connection
if not test_backend_connection():
    st.error("⚠️ Cannot connect to backend. Please check your API_BASE setting in Streamlit secrets.")
    st.stop()

# User ID
if "user_id" not in st.session_state:
    st.session_state.user_id = "demo_user"

user_id = st.session_state.user_id

st.subheader("Upload Your Documents")
st.info("Supported formats: PDF, DOCX, TXT")

uploaded_file = st.file_uploader(
    "Choose a file",
    type=["pdf", "docx", "txt"],
    key="file_uploader"
)

if uploaded_file:
    st.write(f"**File:** {uploaded_file.name}")
    st.write(f"**Size:** {uploaded_file.size / 1024:.1f} KB")
    
    if st.button("📤 Upload File", type="primary"):
        with st.spinner(f"Uploading {uploaded_file.name}..."):
            result = upload_resume(user_id, uploaded_file.read(), uploaded_file.name)
            if result:
                st.json(result)
