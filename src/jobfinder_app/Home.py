import streamlit as st
from pathlib import Path

# Set page config (must be first Streamlit call)
st.set_page_config(
    page_title="SkillScout - Find Your Dream Role",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Add custom CSS for background
st.markdown(
    """
    <style>
    body {
        background-color: #f7f3ef;
        background-image:
            repeating-linear-gradient(0deg, #ede7df 0px, #ede7df 2px, transparent 2px, transparent 40px),
            repeating-linear-gradient(90deg, #ede7df 0px, #ede7df 2px, transparent 2px, transparent 40px);
        background-size: 40px 40px;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# Hide the sidebar for landing page
st.markdown("""
    <style>
        [data-testid="collapsedControl"] {
            display: none
        }
    </style>
    """, unsafe_allow_html=True)

# Center content with custom styling
st.markdown("""
    <style>
        .center-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            text-align: center;
        }
        .logo-container {
            margin: 40px 0;
        }
        .logo-container img {
            max-width: 300px;
            height: auto;
        }
        h1 {
            font-size: 3em;
            color: #1a4d2e;
            margin: 20px 0;
            font-weight: 700;
        }
        .tagline {
            font-size: 1.3em;
            color: #666;
            margin-bottom: 60px;
            font-weight: 400;
        }
        .cta-button {
            display: inline-block;
            background-color: #1a4d2e;
            color: white;
            padding: 16px 40px;
            font-size: 1.1em;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            transition: background-color 0.3s ease;
            border: none;
            cursor: pointer;
        }
        .cta-button:hover {
            background-color: #0d2417;
        }
    </style>
""", unsafe_allow_html=True)

# Logo and branding
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    
    # Display logo from assets (SVG)
    logo_path = Path(__file__).parent / "assets" / "skillscout_logo.svg"
    if logo_path.exists():
        st.image(str(logo_path), use_column_width=False, width=250)
    else:
        # Fallback: Show emoji
        st.markdown("""
            <div style="font-size: 120px; margin-bottom: 30px;">
                🔍
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Main headline
st.markdown('<h1>SkillScout</h1>', unsafe_allow_html=True)

# Tagline
st.markdown('<p class="tagline">See what\'s out there.</p>', unsafe_allow_html=True)

# Spacing
st.markdown('<div style="margin-bottom: 60px;"></div>', unsafe_allow_html=True)

# Call-to-action button
if st.button("🚀 Start Landing Your Next Dream Role", use_container_width=False, key="cta_button"):
    st.switch_page("pages/1_Profile.py")

# Footer spacing
st.markdown('<div style="margin-top: 100px;"></div>', unsafe_allow_html=True)

st.markdown("""
    <div style="text-align: center; color: #999; font-size: 0.9em; margin-top: 80px;">
        <p>Powered by SkillScout AI</p>
    </div>
""", unsafe_allow_html=True)
