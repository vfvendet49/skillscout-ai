import streamlit as st
from web_api_client import get_user_profile, save_user_profile, test_backend_connection

st.set_page_config(page_title="Profile & Preferences", layout="wide")
st.title("📋 Profile & Preferences")

# Check backend connection
if not test_backend_connection():
    st.error("⚠️ Cannot connect to backend. Please check your API_BASE setting in Streamlit secrets.")
    st.stop()

# User ID from session state
if "user_id" not in st.session_state:
    st.session_state.user_id = "demo_user"  # TODO: Replace with real auth

user_id = st.session_state.user_id

# Load existing profile
profile = get_user_profile(user_id)

st.subheader("Your Profile")
col1, col2 = st.columns(2)

with col1:
    name = st.text_input(
        "Full Name",
        value=profile.get("name", "") if profile else "",
        key="name"
    )
    email = st.text_input(
        "Email",
        value=profile.get("email", "") if profile else "",
        key="email"
    )
    title = st.text_input(
        "Job Title",
        value=profile.get("title", "") if profile else "",
        key="title"
    )

with col2:
    location = st.text_input(
        "Location",
        value=profile.get("location", "") if profile else "",
        key="location"
    )
    years_exp = st.number_input(
        "Years of Experience",
        value=profile.get("years_experience", 0) if profile else 0,
        min_value=0,
        max_value=60,
        key="years_exp"
    )

st.subheader("Preferences")
col1, col2 = st.columns(2)

with col1:
    job_types = st.multiselect(
        "Interested Job Types",
        ["Full-time", "Part-time", "Contract", "Remote", "On-site"],
        default=profile.get("job_types", []) if profile else [],
        key="job_types"
    )
    industries = st.multiselect(
        "Preferred Industries",
        ["Technology", "Finance", "Healthcare", "Consulting", "Startup"],
        default=profile.get("industries", []) if profile else [],
        key="industries"
    )

with col2:
    min_salary = st.number_input(
        "Minimum Salary (USD)",
        value=profile.get("min_salary", 0) if profile else 0,
        min_value=0,
        step=1000,
        key="min_salary"
    )
    max_salary = st.number_input(
        "Maximum Salary (USD)",
        value=profile.get("max_salary", 0) if profile else 0,
        min_value=0,
        step=1000,
        key="max_salary"
    )

# Save button
if st.button("💾 Save Profile", type="primary"):
    profile_data = {
        "name": name,
        "email": email,
        "title": title,
        "location": location,
        "years_experience": years_exp,
        "job_types": job_types,
        "industries": industries,
        "min_salary": min_salary,
        "max_salary": max_salary,
    }
    save_user_profile(user_id, profile_data)
