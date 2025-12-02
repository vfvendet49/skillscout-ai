"""
SkillScout: Proof-of-concept job matcher using TheirStack + user JSON.

Requirements:
    pip install requests
"""

import json
import requests
from typing import Dict, Any, List

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------

USER_CONFIG_PATH = "user_input_ben.json"   # your saved JSON file
THEIRSTACK_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiZmphbWVzQGVtb3J5LmVkdSIsInBlcm1pc3Npb25zIjoidXNlciIsImNyZWF0ZWRfYXQiOiIyMDI1LTExLTI5VDE2OjQ1OjE5Ljg1NTE2MSswMDowMCJ9.KGWBQHZmnmfAm_it82Ft3z9p4m48neIQ7_93MZaVe3I"

THEIRSTACK_URL = "https://api.theirstack.com/v1/jobs/search"


# -------------------------------------------------------------------
# LOADING USER CONFIG
# -------------------------------------------------------------------

def load_user_config(path: str = USER_CONFIG_PATH) -> Dict[str, Any]:
    with open(path, "r") as f:
        return json.load(f)


# -------------------------------------------------------------------
# BUILD SEARCH QUERIES FROM USER PROFILE + PREFERENCES
# -------------------------------------------------------------------

def build_search_payloads(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Build one TheirStack search payload per target title.
    Uses:
      - target_titles
      - top hard skills
      - location
      - job_age_limit_days
    """
    profile = config["user_profile"]
    prefs = config["user_preferences"]

    target_titles: List[str] = profile.get("target_titles", [])
    hard_skills: List[str] = profile.get("skills", {}).get("hard_skills", [])

    location_obj = prefs.get("location", {})
    city = location_obj.get("city")
    state = location_obj.get("state")
    country = location_obj.get("country", "US")

    # Build a human-readable location string for TheirStack
    if city and state:
        location_str = f"{city}, {state}"
    elif city:
        location_str = city
    elif state:
        location_str = state
    else:
        # fallback: just country name or "United States"
        location_str = "United States"

    max_age_days = prefs.get("job_age_limit_days", 30)

    # We'll include the target title + some of the top hard skills in q
    # Example: "Operations Manager Logistics Management Data Analysis"
    payloads: List[Dict[str, Any]] = []
    top_skills_for_query = hard_skills[:5]  # not too long

    for title in target_titles:
        q = " ".join([title] + top_skills_for_query)
        payload = {
            "q": q,
            "location": location_str,
            "posted_at_max_age_days": max_age_days,
            "limit": 25,
            "page": 0
        }
        payloads.append(payload)

    return payloads


# -------------------------------------------------------------------
# CALL THEIRSTACK
# -------------------------------------------------------------------

def call_theirstack(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Make a POST request to TheirStack /v1/jobs/search with the given payload.
    """
    headers = {
        "Authorization": f"Bearer {THEIRSTACK_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.post(THEIRSTACK_URL, json=payload, headers=headers)

    try:
        data = response.json()
    except Exception:
        data = {"error": "Invalid JSON response", "raw": response.text}

    return data


# -------------------------------------------------------------------
# RANKING LOGIC
# -------------------------------------------------------------------

def rank_jobs(jobs: List[Dict[str, Any]], profile_skills: List[str]) -> List[Dict[str, Any]]:
    """
    Rank jobs based on overlap between user's skills and job title/description text.
    """
    ranked: List[Dict[str, Any]] = []

    # Flatten skills list into lowercase phrases
    skill_phrases = [s.lower() for s in profile_skills]

    for job in jobs:
        # Safely grab relevant fields
        title = job.get("job_title") or job.get("title") or ""
        description = job.get("description") or ""
        company = job.get("company_name") or job.get("company") or ""
        location = job.get("location") or ""
        url = job.get("url") or job.get("job_url") or ""

        combined_text = f"{title} {description}".lower()

        # Simple matching: count how many skill phrases appear in the text
        score = 0
        matched_skills = []
        for skill in skill_phrases:
            if skill in combined_text:
                score += 1
                matched_skills.append(skill)

        ranked.append({
            "title": title,
            "company": company,
            "location": location,
            "url": url,
            "score": score,
            "matched_skills": list(set(matched_skills))  # unique
        })

    # Sort descending by score, then by title for stability
    ranked.sort(key=lambda x: (-x["score"], x["title"]))
    return ranked


# -------------------------------------------------------------------
# ORCHESTRATION: RUN SKILLSCOUT
# -------------------------------------------------------------------

def run_skillscout(config_path: str = USER_CONFIG_PATH) -> Dict[str, Any]:
    config = load_user_config(config_path)
    profile = config["user_profile"]
    prefs = config["user_preferences"]

    hard_skills: List[str] = profile.get("skills", {}).get("hard_skills", [])
    soft_skills: List[str] = profile.get("skills", {}).get("soft_skills", [])
    all_skills = hard_skills + soft_skills

    print("\n=== Loaded User Profile: ===")
    print(f"Name: {profile.get('name')}")
    print("Target titles:")
    for t in profile.get("target_titles", []):
        print(f"  - {t}")

    print("\nLocation preference:")
    print(prefs.get("location"))

    print("\nMinimum salary preference:")
    print(prefs.get("salary"))

    # Build payloads for each target title
    payloads = build_search_payloads(config)

    all_jobs_raw: List[Dict[str, Any]] = []
    seen_ids = set()

    print("\n=== Calling TheirStack... ===")
    for i, payload in enumerate(payloads, start=1):
        print(f"\n--- Query {i} ---")
        print(f"q: {payload['q']}")
        print(f"location: {payload['location']}")
        resp = call_theirstack(payload)

        if "error" in resp:
            print("Error from TheirStack:", resp["error"])
            continue

        data = resp.get("data", [])
        print(f"Jobs returned: {len(data)}")

        for job in data:
            job_id = job.get("id")
            if job_id is not None and job_id in seen_ids:
                continue
            if job_id is not None:
                seen_ids.add(job_id)
            all_jobs_raw.append(job)

    print(f"\nTotal unique jobs collected: {len(all_jobs_raw)}")

    ranked = rank_jobs(all_jobs_raw, all_skills)

    return {
        "config": config,
        "jobs_ranked": ranked
    }


# -------------------------------------------------------------------
# PRETTY PRINT RESULTS
# -------------------------------------------------------------------

def print_top_jobs(result: Dict[str, Any], top_n: int = 10) -> None:
    jobs = result["jobs_ranked"][:top_n]

    print(f"\n\n=== Top {len(jobs)} SkillScout Matches ===\n")
    if not jobs:
        print("No jobs found. Try relaxing preferences or checking the API key/config.")
        return

    for i, job in enumerate(jobs, start=1):
        print(f"[{i}] {job['title']} @ {job['company']}")
        print(f"    Location: {job['location']}")
        print(f"    Match score: {job['score']}")
        if job["matched_skills"]:
            print(f"    Matched skills: {', '.join(job['matched_skills'])}")
        if job["url"]:
            print(f"    URL: {job['url']}")
        print()


# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------

if __name__ == "__main__":
    result = run_skillscout(USER_CONFIG_PATH)
    print_top_jobs(result, top_n=10)
