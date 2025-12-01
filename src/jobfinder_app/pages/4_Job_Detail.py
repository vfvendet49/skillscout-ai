# pages/4_Job_Detail.py — Job detail & matching page
import streamlit as st
import requests
import os
import json
import time
from openai import OpenAI

st.set_page_config(page_title="Job Detail - SkillScout", layout="wide")

st.title("Job Detail & AI Tweaks")

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
                score = m.get("score", None)
                st.metric("Score", score if score is not None else "N/A")
                try:
                    st.progress(min(1.0, float(score)))
                except Exception:
                    pass
                st.caption(f"Coverage: {m.get('coverage', 'N/A')} · Cosine: {m.get('cosine', 'N/A')}")

                # Display any server-provided tweaks first
                server_tweaks = m.get("tweaks", []) or []
                if server_tweaks:
                    st.subheader("Server suggested tweaks")
                    for tw in server_tweaks:
                        st.warning(f"{tw.get('type', '').title()} — {tw.get('message', '')}")
                        kws = tw.get("keywords", []) or []
                        if kws:
                            st.write(", ".join(kws))

                # If score meets threshold (or user threshold), call OpenAI to generate suggested tweaks client-side
                try:
                    score_val = float(score) if score is not None else 0.0
                except Exception:
                    score_val = 0.0

                # helper to obtain OpenAI client from env or streamlit secrets
                def _get_openai_client():
                    key = os.getenv("OPENAI_API_KEY")
                    if not key:
                        try:
                            key = st.secrets.get("OPENAI_API_KEY")
                        except Exception:
                            key = None
                    if not key:
                        return None
                    # Support a local MOCK mode via OPENAI_API_KEY=MOCK for offline testing
                    if key == "MOCK":
                        return "MOCK"
                    try:
                        return OpenAI(api_key=key)
                    except Exception:
                        return None

                def generate_tweaks_via_openai(client, resume, cover, job_desc, matched_keywords):
                    if client is None:
                        return {"error": "No OpenAI API key configured (OPENAI_API_KEY)."}

                    # If client == 'MOCK', return canned suggestions for smoke tests
                    if client == "MOCK":
                        return {
                            "tweaks": [
                                {"type": "add", "message": "Add a bullet about automating ETL pipelines using Airflow.", "keywords": ["Airflow", "ETL", "automation"]},
                                {"type": "emphasize", "message": "Emphasize your experience with AWS S3 and data lakes.", "keywords": ["AWS S3", "data lake"]},
                                {"type": "remove", "message": "Remove personal projects not related to data engineering.", "keywords": []}
                            ]
                        }

                    system_prompt = (
                        "You are an expert career coach and resume writer. Given a job description, a list of matched keywords that appeared in the job posting, "
                        "and the candidate's resume and cover letter, produce concise, actionable suggestions to: add missing items, emphasize relevant experience, "
                        "and remove or de-emphasize irrelevant or risky statements. Return a JSON array of objects with fields: type (add|emphasize|remove), message, keywords (array). "
                        "Limit the response to 8 suggestions and avoid hallucinations."
                    )

                    user_prompt = (
                        f"Job description:\n{job_desc}\n\nMatched keywords:\n{', '.join(matched_keywords or [])}\n\nResume:\n{resume}\n\nCover Letter:\n{cover}\n\n"
                        "Produce the JSON array only."
                    )

                    try:
                        resp = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt},
                            ],
                            temperature=0.2,
                            max_tokens=500,
                        )

                        # OpenAI Python client returns content in resp.choices[0].message.content
                        text = ""
                        try:
                            text = resp.choices[0].message.get("content")
                        except Exception:
                            try:
                                text = resp.choices[0].get("message", {}).get("content", "")
                            except Exception:
                                text = str(resp)

                        # Try JSON parse; if fails, return raw text
                        try:
                            parsed = json.loads(text)
                            return {"tweaks": parsed}
                        except Exception:
                            return {"raw": text}

                    except Exception as e:
                        return {"error": str(e)}

                # Only trigger OpenAI suggestions when score meets or exceeds threshold
                if score_val >= float(threshold):
                    st.subheader("AI-generated suggestions (ChatGPT)")
                    client = _get_openai_client()
                    if client is None:
                        st.info("No OpenAI API key configured. To enable AI suggestions, set OPENAI_API_KEY in your environment or Streamlit secrets.")
                    else:
                        with st.spinner("Generating AI suggestions..."):
                            # prefer matched keywords provided by server if available
                            matched = m.get("matched_keywords") or m.get("keywords") or []
                            result = generate_tweaks_via_openai(client, resume_txt, cover_txt, sel.get("description", ""), matched)
                            if result.get("error"):
                                st.error(result.get("error"))
                            elif result.get("tweaks"):
                                for t in result.get("tweaks"):
                                    ttype = (t.get("type") or "note").lower()
                                    msg = t.get("message") or t.get("suggestion") or ""
                                    kws = t.get("keywords") or []
                                    if ttype == "add":
                                        st.success(f"Add — {msg}")
                                    elif ttype == "emphasize":
                                        st.info(f"Emphasize — {msg}")
                                    elif ttype == "remove":
                                        st.warning(f"Remove — {msg}")
                                    else:
                                        st.write(f"{ttype.title()} — {msg}")
                                    if kws:
                                        st.write(", ".join(kws))
                            elif result.get("raw"):
                                st.write("Could not parse structured JSON from model. Raw output:")
                                st.code(result.get("raw"))
                else:
                    st.info("Score is below threshold for AI suggestions. Increase threshold to trigger AI tweaks or adjust your resume and try again.")
            else:
                st.error(r.text)
        except requests.exceptions.ConnectionError:
            st.warning(f"ℹ️ Backend not running ({API}). Match computation requires backend API.")
        except Exception as e:
            st.error(f"Error: {str(e)}")
else:
    st.info("Select a job in the Results tab to view details.")
