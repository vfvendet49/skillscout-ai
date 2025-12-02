"""
===============================================================================
SkillScout v7 — Phase 1 → Phase 4 (Full Backend Version, Outlook Email Draft)
===============================================================================
Includes:
    ✔ Phase 1   — Job matching engine
    ✔ Phase 2   — JSON + TXT formatted export system
    ✔ Phase 2.5 — Resume parsing & skill extraction
    ✔ Phase 3   — Daily & weekly history logging
    ✔ Phase 3.5 — Visa / sponsorship eligibility filter
    ✔ Phase 4   — HTML + text email draft builder for Outlook (no auto-send)

Phase 4 is now Outlook-focused:
    - Builds professional HTML + plain text email content
    - Saves them as files so you can copy/paste into Outlook
    - No Gmail / SMTP sending in this version

This file is your main working backend codebase.
===============================================================================
"""

import json
import requests
import os
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
import datetime
from typing import Dict, Any, List

# ----------------------------------------------------------------------
# Optional resume parsing libraries (PDF + DOCX)
# ----------------------------------------------------------------------
try:
    # Preferred modern library
    from pypdf import PdfReader  # type: ignore
except ImportError:
    try:
        # Legacy library, in case only PyPDF2 is installed
        from PyPDF2 import PdfReader  # type: ignore
    except ImportError:
        PdfReader = None  # type: ignore

try:
    import docx  # python-docx
except ImportError:
    docx = None  # type: ignore


# ======================================================================
# CONFIGURATION CONSTANTS
# ======================================================================

USER_CONFIG_PATH = "user_input_ben.json"

THEIRSTACK_API_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJzdWIiOiJiZmphbWVzQGVtb3J5LmVkdSIsInBlcm"
    "1pc3Npb25zIjoidXNlciIsImNyZWF0ZWRfYXQiOiIy"
    "MDI1LTExLTI5VDE2OjQ1OjE5Ljg1NTE2MSswMDowMC"
    "J9.KGWBQHZmnmfAm_it82Ft3z9p4m48neIQ7_93MZaVe3I"
)

THEIRSTACK_URL = "https://api.theirstack.com/v1/jobs/search"


# ======================================================================
# PHASE 1 — USER INPUT
# ======================================================================

def prompt_user_info() -> Dict[str, str]:
    print("\n=== SkillScout User Setup ===")

    name = input("Enter your name (example: John Doe): ").strip()
    if not name:
        name = "User"

    email = input(
        "Enter your email (for later notifications):\n"
        "Example: JohnDoe1@gmail.com\n> "
    ).strip()

    resume_path = input(
        "Enter the path to your resume (optional):\n"
        "Examples:\n"
        "  C:/Users/John/Desktop/resume.pdf\n"
        "  /Users/john/Resume.docx\n"
        "(Press Enter to skip)\n> "
    ).strip()

    if resume_path == "":
        resume_path = "Not provided"

    # Visa / citizenship status question (for Phase 3.5)
    visa_status = input(
        "\nAre you a US citizen / permanent resident, or do you need sponsorship?\n"
        "Examples:\n"
        "  - citizen\n"
        "  - green card\n"
        "  - opt\n"
        "  - h1b\n"
        "  - international student\n"
        "Enter your status (for visa filter logic):\n> "
    ).strip()

    return {
        "name": name,
        "email": email,
        "resume_path": resume_path,
        "visa_status": visa_status or "unspecified"
    }


# ======================================================================
# PHASE 1 — LOAD USER CONFIG JSON
# ======================================================================

def load_user_config(path: str = USER_CONFIG_PATH) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] Config file not found: {path}")
        raise
    except json.JSONDecodeError:
        print("[ERROR] Invalid JSON format.")
        raise


# ======================================================================
# PHASE 1 — EXPERIENCE → SENIORITY MAPPING
# ======================================================================

def map_experience_to_seniority(exp_level: str) -> List[str]:
    if not exp_level:
        return []

    e = exp_level.lower()

    if "mid" in e and "senior" in e:
        return ["mid_level", "senior"]
    if "mid" in e:
        return ["mid_level"]
    if "senior" in e:
        return ["senior"]
    if "junior" in e or "entry" in e:
        return ["junior"]
    if "c" in e or "executive" in e:
        return ["c_level"]

    return []


# ======================================================================
# PHASE 1 — BUILD THEIRSTACK FILTER BODY
# ======================================================================

def build_job_search_body(config: Dict[str, Any]):
    profile = config["user_profile"]
    prefs = config["user_preferences"]

    target_titles = profile.get("target_titles", [])
    hard_skills = profile.get("skills", {}).get("hard_skills", [])
    soft_skills = profile.get("skills", {}).get("soft_skills", [])

    loc = prefs.get("location", {})
    city = loc.get("city")
    state = loc.get("state")
    country = loc.get("country", "US")
    remote_pref = loc.get("remote")

    if city and state:
        loc_pattern = f"{city}, {state}"
    elif city:
        loc_pattern = city
    elif state:
        loc_pattern = state
    else:
        loc_pattern = country

    max_age_days = prefs.get("job_age_limit_days", 30)
    min_salary = prefs.get("salary", {}).get("min")
    exp_level = profile.get("experience_level", "")
    seniority_filters = map_experience_to_seniority(exp_level)

    body = {
        "job_title_or": target_titles,
        "job_location_pattern_or": [loc_pattern.lower()],
        "posted_at_max_age_days": max_age_days,
        "min_salary_usd": float(min_salary) if min_salary else None,
        "remote": remote_pref,
        "job_seniority_or": seniority_filters,
        "limit": 25
    }

    clean_body = {k: v for k, v in body.items() if v not in [None, [], ""]}
    return clean_body, hard_skills + soft_skills


# ======================================================================
# PHASE 1 — CALL THEIRSTACK API
# ======================================================================

def call_theirstack_job_search(body: Dict[str, Any]) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {THEIRSTACK_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(THEIRSTACK_URL, headers=headers, json=body)
        return resp.json()
    except Exception as e:
        print(f"[ERROR] Failed API request: {e}")
        return {"error": str(e)}


# ======================================================================
# PHASE 1 — RANK JOBS BY SKILL MATCH
# ======================================================================

def rank_jobs(jobs: List[Dict[str, Any]], skills: List[str]):
    ranked = []
    skills = [s.lower() for s in skills]

    for job in jobs:
        title = job.get("job_title", "")
        desc = job.get("description", "")
        combined = f"{title} {desc}".lower()

        score = 0
        matched = []

        for s in skills:
            if s and s in combined:
                score += 1
                matched.append(s)

        ranked.append({
            "title": job.get("job_title", ""),
            "company": job.get("company_name") or job.get("company") or "",
            "location": (
                job.get("long_location")
                or job.get("location")
                or job.get("short_location")
                or ""
            ),
            "url": job.get("final_url") or job.get("url") or "",
            "score": score,
            "matched_skills": sorted(set(matched)),
            # Keep raw description for visa filter (Phase 3.5)
            "description": desc or ""
        })

    return sorted(ranked, key=lambda x: (-x["score"], x["title"]))


# ======================================================================
# PHASE 1 — ORCHESTRATION
# ======================================================================

def run_skillscout(config_path: str = USER_CONFIG_PATH):
    print("\n[PHASE 1] Starting core SkillScout pipeline...")
    user = prompt_user_info()
    config = load_user_config(config_path)

    print("\n=== TheirStack Search Body ===")
    body, skills = build_job_search_body(config)
    print(json.dumps(body, indent=2))

    print("\n=== Calling TheirStack API ===")
    resp = call_theirstack_job_search(body)

    if "data" not in resp:
        print("[ERROR] No jobs returned.")
        return {"user": user, "ranked": [], "raw": resp, "config": config}

    ranked = rank_jobs(resp["data"], skills)

    print(f"[PHASE 1] Jobs retrieved and ranked: {len(ranked)}")

    return {
        "user": user,
        "ranked": ranked,
        "raw": resp,
        "config": config
    }


# ======================================================================
# PHASE 1 — TERMINAL OUTPUT
# ======================================================================

def print_top_jobs(result, top_n=10):
    jobs = result["ranked"][:top_n]

    print(f"\n=== Top {len(jobs)} SkillScout Matches ===\n")

    for i, job in enumerate(jobs, start=1):
        print(f"[{i}] {job['title']} @ {job['company']}")
        print(f"     Location: {job['location']}")
        print(f"     Score: {job['score']}")
        print(f"     Skills: {', '.join(job['matched_skills'])}")
        print(f"     URL: {job['url']}\n")


# ======================================================================
# PHASE 2 — FORMATTED OUTPUT + EXPORT SYSTEM
# ======================================================================

def format_results_json(result: Dict[str, Any], top_n: int = 10) -> Dict[str, Any]:
    jobs = result["ranked"][:top_n]

    formatted = {
        "user": {
            "name": result["user"]["name"],
            "email": result["user"]["email"],
            "resume_path": result["user"]["resume_path"],
            "visa_status": result["user"].get("visa_status", "unspecified")
        },
        "matches": []
    }

    for job in jobs:
        formatted["matches"].append({
            "title": job["title"],
            "company": job["company"],
            "location": job["location"],
            "score": job["score"],
            "matched_skills": job["matched_skills"],
            "url": job["url"]
        })

    return formatted


def format_results_text(result: Dict[str, Any], top_n: int = 10) -> str:
    jobs = result["ranked"][:top_n]
    lines: List[str] = []

    lines.append(f"=== SkillScout Job Matches for {result['user']['name']} ===\n")

    for i, job in enumerate(jobs, start=1):
        lines.append(f"🔹 Job Match #{i}")
        lines.append(f"Title: {job['title']}")
        lines.append(f"Company: {job['company']}")
        lines.append(f"Location: {job['location']}")
        lines.append(f"Score: {job['score']}")
        lines.append(f"Matched Skills: {', '.join(job['matched_skills'])}")
        lines.append(f"URL: {job['url']}")
        lines.append("")  # blank line

    return "\n".join(lines)


def export_results(result: Dict[str, Any], folder="skillscout_output", top_n=10):
    if not os.path.exists(folder):
        os.makedirs(folder)

    json_ready = format_results_json(result, top_n=top_n)
    text_ready = format_results_text(result, top_n=top_n)

    json_path = os.path.join(folder, "job_matches.json")
    txt_path = os.path.join(folder, "job_matches.txt")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_ready, f, indent=2)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text_ready)

    print(f"\n[PHASE 2] Export complete → {folder}/")
    print("  - job_matches.json")
    print("  - job_matches.txt\n")


# ======================================================================
# PHASE 2.5 — RESUME SKILL EXTRACTION
# ======================================================================

def extract_text_from_pdf(path: str) -> str:
    if PdfReader is None:
        print("[PHASE 2.5] WARNING: No PDF library installed (pypdf / PyPDF2).")
        return ""
    try:
        reader = PdfReader(path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.lower()
    except Exception as e:
        print(f"[PHASE 2.5] PDF read error: {e}")
        return ""


def extract_text_from_docx(path: str) -> str:
    if docx is None:
        print("[PHASE 2.5] WARNING: python-docx not installed; cannot read DOCX.")
        return ""
    try:
        document = docx.Document(path)
        full_text = [para.text for para in document.paragraphs]
        return "\n".join(full_text).lower()
    except Exception as e:
        print(f"[PHASE 2.5] DOCX read error: {e}")
        return ""


def extract_resume_text(path: str) -> str:
    if not path or path == "Not provided":
        return ""

    path = path.strip().strip('"').strip("'")

    if not os.path.exists(path):
        print(f"[PHASE 2.5] WARNING: Resume file not found at: {path}")
        return ""

    if path.lower().endswith(".pdf"):
        return extract_text_from_pdf(path)
    elif path.lower().endswith(".docx"):
        return extract_text_from_docx(path)
    elif path.lower().endswith(".txt"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().lower()
        except Exception as e:
            print(f"[PHASE 2.5] TXT read error: {e}")
            return ""

    print("[PHASE 2.5] WARNING: Unsupported resume format (use PDF, DOCX, or TXT).")
    return ""


def extract_skills_from_resume(resume_text: str, reference_skills: List[str]) -> List[str]:
    resume_skills = []
    text = resume_text.lower()

    for skill in reference_skills:
        if skill.lower() in text:
            resume_skills.append(skill.lower())

    return sorted(set(resume_skills))


def integrate_resume_skills(result: Dict[str, Any]) -> Dict[str, Any]:
    print("\n[PHASE 2.5] Resume skill enrichment step starting...")

    resume_path = result["user"].get("resume_path", "")
    if not resume_path or resume_path == "Not provided":
        print("[PHASE 2.5] No resume path provided. Skipping.")
        result["resume_skills"] = []
        return result

    text = extract_resume_text(resume_path)
    if not text:
        print("[PHASE 2.5] Could not extract text from resume. Skipping skill detection.")
        result["resume_skills"] = []
        return result

    base_skills = (
        result["config"]["user_profile"]["skills"]["hard_skills"] +
        result["config"]["user_profile"]["skills"]["soft_skills"]
    )

    resume_skills = extract_skills_from_resume(text, base_skills)
    result["resume_skills"] = resume_skills

    print(f"[PHASE 2.5] Resume skills found: {resume_skills}")
    return result


# ======================================================================
# PHASE 3.5 — VISA & SPONSORSHIP ELIGIBILITY FILTERING
# ======================================================================

def filter_visa_eligibility(result: Dict[str, Any]) -> Dict[str, Any]:
    print("\n[PHASE 3.5] Visa / sponsorship eligibility filter starting...")

    visa_status = result["user"].get("visa_status", "").lower()
    ranked_jobs = result["ranked"]

    # US citizens / PR: everything allowed
    if visa_status in [
        "citizen", "us citizen", "u.s. citizen",
        "pr", "green card", "green-card", "permanent resident",
        "us citizen / pr", "citizen/pr"
    ]:
        print("[PHASE 3.5] Status indicates US citizen / PR → all jobs eligible.")
        result["eligible_jobs"] = ranked_jobs
        result["ineligible_jobs"] = []
        return result

    # Otherwise: apply visa restriction filters
    visa_block_keywords = [
        # citizenship / PR
        "us citizen", "u.s. citizen", "citizen only",
        "us person", "u.s. person",
        "green card required", "permanent resident only",
        "permanent resident",
        # clearance / federal
        "security clearance", "ts/sci", "top secret",
        "dod clearance", "federal contractor",
        # sponsorship bans
        "no sponsorship", "cannot sponsor", "not able to sponsor",
        "sponsorship not available",
        "h1b not supported", "h-1b not supported",
        "opt/cpt not accepted",
        "must be authorized to work in the us without sponsorship",
        "must be authorized to work in the united states without sponsorship"
    ]

    eligible, ineligible = [], []

    for job in ranked_jobs:
        combined = (
            job["title"] + " " +
            job["company"] + " " +
            job.get("description", "")
        ).lower()

        failed = None
        for kw in visa_block_keywords:
            if kw in combined:
                failed = f"Failed visa eligibility check due to: '{kw}'"
                break

        if failed:
            j = job.copy()
            j["ineligibility_reason"] = failed
            ineligible.append(j)
        else:
            eligible.append(job)

    result["eligible_jobs"] = eligible
    result["ineligible_jobs"] = ineligible

    print(f"[PHASE 3.5] Eligible jobs: {len(eligible)} | Ineligible: {len(ineligible)}")
    return result


# ======================================================================
# PHASE 3 — AUTOMATION (Daily & Weekly Job Pull Framework)
# ======================================================================

def save_daily_run(result: Dict[str, Any], folder: str = "history_daily"):
    if not os.path.exists(folder):
        os.makedirs(folder)

    today = datetime.date.today().isoformat()
    path = os.path.join(folder, f"jobs_{today}.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "date": today,
            "eligible_jobs": result.get("eligible_jobs", []),
            "ineligible_jobs": result.get("ineligible_jobs", []),
            "user": result["user"]
        }, f, indent=2)

    print(f"[PHASE 3] Daily job report saved → {path}")


def save_weekly_summary(result: Dict[str, Any], folder: str = "history_weekly"):
    if not os.path.exists(folder):
        os.makedirs(folder)

    week = datetime.date.today().isocalendar().week
    path = os.path.join(folder, f"week_{week}.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "week": week,
            "eligible_jobs": result.get("eligible_jobs", []),
            "ineligible_jobs": result.get("ineligible_jobs", []),
            "user": result["user"]
        }, f, indent=2)

    print(f"[PHASE 3] Weekly summary saved → {path}")


# ======================================================================
# PHASE 4 — SIMPLE HTML EMAIL (OUTLOOK DESKTOP SEND)
# ======================================================================

def build_html_email_body(
    user: Dict[str, Any],
    jobs: List[Dict[str, Any]],
    ineligible_jobs: List[Dict[str, Any]],
    max_jobs: int = 10
) -> Dict[str, str]:
    """
    Builds a simple, email-safe HTML + plain-text body for the daily report.
    Returns:
        {
            "subject": "...",
            "text": "...",
            "html": "..."
        }
    """
    today = datetime.date.today().isoformat()
    subject = f"SkillScout Daily Matches — {today}"

    # Plain text
    lines = [f"Hi {user['name']},", "", "Here are your top job matches for today:", ""]
    for i, job in enumerate(jobs[:max_jobs], start=1):
        lines.append(f"{i}. {job['title']} @ {job['company']}")
        lines.append(f"   Location: {job['location']}")
        lines.append(f"   Match Score: {job['score']}")
        if job["matched_skills"]:
            lines.append(f"   Matched Skills: {', '.join(job['matched_skills'])}")
        lines.append(f"   URL: {job['url']}")
        lines.append("")
    if ineligible_jobs:
        lines.append("Jobs removed due to visa/eligibility rules:")
        for j in ineligible_jobs[:5]:
            lines.append(f"- {j['title']} @ {j['company']}  ({j['ineligibility_reason']})")
    lines.append("")
    lines.append("Best,")
    lines.append("SkillScout")

    text_body = "\n".join(lines)

    # HTML version
    html_rows = ""
    for i, job in enumerate(jobs[:max_jobs], start=1):
        skills_str = ", ".join(job["matched_skills"]) if job["matched_skills"] else "None listed"
        html_rows += f"""
        <tr>
          <td style="padding:8px;border-bottom:1px solid #dddddd;">{i}</td>
          <td style="padding:8px;border-bottom:1px solid #dddddd;">{job['title']}</td>
          <td style="padding:8px;border-bottom:1px solid #dddddd;">{job['company']}</td>
          <td style="padding:8px;border-bottom:1px solid #dddddd;">{job['location']}</td>
          <td style="padding:8px;border-bottom:1px solid #dddddd;">{job['score']}</td>
          <td style="padding:8px;border-bottom:1px solid #dddddd;">{skills_str}</td>
          <td style="padding:8px;border-bottom:1px solid #dddddd;"><a href="{job['url']}">Link</a></td>
        </tr>
        """

    ineligible_html = ""
    if ineligible_jobs:
        ineligible_html_rows = ""
        for j in ineligible_jobs[:5]:
            ineligible_html_rows += f"""
            <tr>
              <td style="padding:8px;border-bottom:1px solid #dddddd;">{j['title']}</td>
              <td style="padding:8px;border-bottom:1px solid #dddddd;">{j['company']}</td>
              <td style="padding:8px;border-bottom:1px solid #dddddd;">{j.get('ineligibility_reason', '')}</td>
            </tr>
            """
        ineligible_html = f"""
        <h3 style="font-family:Arial;">Jobs Removed Due to Eligibility</h3>
        <table cellpadding="0" cellspacing="0" style="border-collapse:collapse;width:100%;font-family:Arial;font-size:13px;">
          <tr style="background-color:#f0f0f0;">
            <th style="padding:8px;border-bottom:1px solid #dddddd;text-align:left;">Title</th>
            <th style="padding:8px;border-bottom:1px solid #dddddd;text-align:left;">Company</th>
            <th style="padding:8px;border-bottom:1px solid #dddddd;text-align:left;">Reason</th>
          </tr>
          {ineligible_html_rows}
        </table>
        """

    html_body = f"""
    <html>
      <body style="font-family:Arial, sans-serif; font-size:14px; color:#333;">
        <p>Hi {user['name']},</p>
        <p>Here are your top job matches for <strong>{today}</strong>:</p>

        <table cellpadding="0" cellspacing="0" style="border-collapse:collapse;width:100%;font-family:Arial;font-size:13px;">
          <tr style="background-color:#f0f0f0;">
            <th style="padding:8px;border-bottom:1px solid #dddddd;text-align:left;">#</th>
            <th style="padding:8px;border-bottom:1px solid #dddddd;text-align:left;">Title</th>
            <th style="padding:8px;border-bottom:1px solid #dddddd;text-align:left;">Company</th>
            <th style="padding:8px;border-bottom:1px solid #dddddd;text-align:left;">Location</th>
            <th style="padding:8px;border-bottom:1px solid #dddddd;text-align:left;">Score</th>
            <th style="padding:8px;border-bottom:1px solid #dddddd;text-align:left;">Matched Skills</th>
            <th style="padding:8px;border-bottom:1px solid #dddddd;text-align:left;">Job Link</th>
          </tr>
          {html_rows}
        </table>

        {ineligible_html}

        <p style="margin-top:20px;">Best,<br/>SkillScout</p>
      </body>
    </html>
    """

    return {
        "subject": subject,
        "text": text_body,
        "html": html_body
    }
def save_email_draft(*args, **kwargs):
    # TODO: implement saving email draft
    pass
import win32com.client as win32

def send_daily_email(result: Dict[str, Any], max_jobs: int = 10) -> None:
    """
    Sends an HTML email to the user with top matches using Outlook Desktop.
    Requires:
        - Windows
        - Outlook installed and logged in
        - pywin32 installed
    Controlled by EMAIL_ENABLED flag.
    """
    if not EMAIL_ENABLED:
        print("[PHASE 4] EMAIL_DISABLED → Skipping Outlook send. Set EMAIL_ENABLED = True to enable.")
        return

    user = result["user"]
    eligible_jobs = result.get("eligible_jobs", [])
    ineligible_jobs = result.get("ineligible_jobs", [])

    if not eligible_jobs:
        print("[PHASE 4] No eligible jobs to email.")
        return

    email_content = build_html_email_body(user, eligible_jobs, ineligible_jobs, max_jobs=max_jobs)

    try:
        print("[PHASE 4] Attempting to send email via Outlook Desktop...")
        outlook = win32.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)  # 0 = MailItem

        mail.To = user["email"]
        mail.Subject = email_content["subject"]
        # Body (plain text) is optional but good practice
        mail.Body = email_content["text"]
        # HTMLBody overrides Body for supported clients
        mail.HTMLBody = email_content["html"]

        # If you wanted to see the email before sending:
        # mail.Display()  # Comment this out in production

        mail.Send()
        print(f"[PHASE 4] Outlook email successfully sent to {user['email']}")

    except Exception as e:
        print(f"[PHASE 4 ERROR] Failed to send via Outlook: {e}")

# ======================================================================
# MAIN EXECUTION
# ======================================================================

if __name__ == "__main__":
    # Phase 1 — core flow (scrape + rank)
    result = run_skillscout(USER_CONFIG_PATH)

    # Phase 2.5 — resume enrichment (optional)
    result = integrate_resume_skills(result)

    # Phase 3.5 — visa eligibility filtering
    result = filter_visa_eligibility(result)

    # Phase 1 / 2 — print and export only ELIGIBLE jobs
    eligible_result = {
        "user": result["user"],
        "ranked": result.get("eligible_jobs", [])
    }

    print_top_jobs(eligible_result, top_n=10)
    export_results(eligible_result, top_n=10)

    # Phase 3 — logging
    save_daily_run(result)
    save_weekly_summary(result)

    # Phase 4 — save Outlook-ready email drafts (HTML + text)
    save_email_draft(result, max_jobs=10)

    # Show removed jobs (if any)
    if result.get("ineligible_jobs"):
        print("\n=== Jobs Removed Due to Visa Restrictions ===\n")
        for j in result["ineligible_jobs"]:
            print(f"{j['title']} @ {j['company']}")
            print(f"Reason: {j['ineligibility_reason']}\n")
