import streamlit as st
from web_api_client import search_jobs, test_backend_connection

st.set_page_config(page_title="Job Search", layout="wide")
st.title("🔍 Job Search")

# Check backend connection
if not test_backend_connection():
    st.error("⚠️ Cannot connect to backend. Please check your API_BASE setting in Streamlit secrets.")
    st.stop()

# User ID
if "user_id" not in st.session_state:
    st.session_state.user_id = "demo_user"

user_id = st.session_state.user_id

st.subheader("Search Parameters")
col1, col2 = st.columns(2)

with col1:
    query = st.text_input(
        "Job Title/Keywords",
        placeholder="e.g., Data Scientist, Product Manager",
        key="search_query"
    )

with col2:
    location = st.text_input(
        "Location",
        placeholder="e.g., San Francisco, CA or Remote",
        key="search_location"
    )

# Search button
if st.button("🚀 Search Jobs", type="primary"):
    if query:
        with st.spinner("Searching for jobs..."):
            jobs = search_jobs(user_id, query, location)
            if jobs:
                st.success(f"Found {len(jobs)} jobs!")
                
                # Display jobs
                for idx, job in enumerate(jobs, 1):
                    with st.expander(f"{idx}. {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}"):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**Company:** {job.get('company', 'N/A')}")
                            st.markdown(f"**Location:** {job.get('location', 'N/A')}")
                            st.markdown(f"**Description:** {job.get('description', 'N/A')[:200]}...")
                            if job.get('url'):
                                st.markdown(f"[View Job]({job['url']})")
                        with col2:
                            st.metric("Match Score", f"{job.get('match_score', 0)}%")
    else:
        st.warning("Please enter a job search query")
