"""
SkillScout v2
-------------
Proof-of-concept job matcher using TheirStack + user JSON.

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

# >>>>>> PUT YOUR REAL THEIRSTACK KEY HERE (the long eyJhbG... string) <<<<<<
THEIRSTACK_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiZmphbWVzQGVtb3J5LmVkdSIsInBlcm1pc3Npb25zIjoidXNlciIsImNyZWF0ZWRfYXQiOiIyMDI1LTExLTI5VDE2OjQ1OjE5Ljg1NTE2MSswMDowMCJ9.KGWBQHZmnmfAm_it82Ft3z9p4m48neIQ7_93MZaVe3I"

THEIRSTACK_URL = "https://api.theirstack.com/v1/jobs/search"


# -------------------------------------------------------------------
# LOAD USER CONFIG
# -------------------------------------------------------------------

def load_user_config(path: str = USER_CONFIG_PATH) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# -------------------------------------------------------------------
# BUILD THEIRSTACK JOB SEARCH FILTERS BODY
# -------------------------------------------------------------------

def map_experience_to_seniority(exp_level: str) -> List[str]:
    """
    Map our user-friendly experience string to TheirStack seniority enums.
    TheirStack enums: "c_level", "staff", "senior", "junior", "mid_level"
    """
    if not exp_level:
        return []

    exp_lower = exp_level.lower()

    if "mid" in exp_lower and "senior" in exp_lower:
        return ["mid_level", "senior"]
    if "mid" in exp_lower:
        return ["mid_level"]
    if "senior" in exp_lower:
        return ["senior"]
    if "junior" in exp_lower or "entry" in exp_lower:
        return ["junior"]
    if "c" in exp_lower or "executive" in exp_lower:
        return ["c_level"]

    return []


def build_job_search_body(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a JobSearchFilters body for TheirStack /v1/jobs/search.

    We use:
      - job_title_or
      - job_location_pattern_or
      - posted_at_max_age_days
      - min_salary_usd
      - remote
      - job_seniority_or
      - limit
    """
    profile = config["user_profile"]
    prefs = config["user_preferences"]

    target_titles: List[str] = profile.get("target_titles", [])
    hard_skills: List[str] = profile.get("skills", {}).get("hard_skills", [])
    soft_skills: List[str] = profile.get("skills", {}).get("soft_skills", [])

    location_obj = prefs.get("location", {})
    city = location_obj.get("city")
    state = location_obj.get("state")
    country = location_obj.get("country", "US")
    remote_pref = location_obj.get("remote", None)  # bool or None

    # Build simple location pattern for TheirStack
    if city and state:
        location_pattern = f"{city}, {state}"
    elif city:
        location_pattern = city
    elif state:
        location_pattern = state
    else:
        location_pattern = country or "united states"

    max_age_days = prefs.get("job_age_limit_days", 30)
    min_salary = prefs.get("salary", {}).get("min", None)
    exp_level = profile.get("experience_level", "")
    seniority_filters = map_experience_to_seniority(exp_level)

    body: Dict[str, Any] = {
        # Which job titles we’re looking for
        "job_title_or": target_titles,

        # Where (pattern-based – TheirStack uses regex-like search)
        "job_location_pattern_or": [location_pattern.lower()],

        # Time window
        "posted_at_max_age_days": max_age_days,

        # Salary preference (in USD)
        "min_salary_usd": float(min_salary) if min_salary else None,

        # Remote preference
        # True  -> only remote
        # False -> only non-remote
        # None  -> both
        "remote": remote_pref,

        # Seniority
        "job_seniority_or": seniority_filters,

        # How many results to pull
        "limit": 25,
    }

    # Remove keys with value None (TheirStack doesn't want them)
    body = {k: v for k, v in body.items() if v is not None and v != []}

    return body, hard_skills + soft_skills


# -------------------------------------------------------------------
# CALL THEIRSTACK
# -------------------------------------------------------------------

def call_theirstack_job_search(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Make a POST request to TheirStack /v1/jobs/search with JSON body.
    """
    headers = {
        "Authorization": f"Bearer {THEIRSTACK_API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(THEIRSTACK_URL, headers=headers, json=body)

    try:
        data = response.json()
    except Exception:
        data = {"error": "Invalid JSON response", "raw": response.text}

    # Helpful debug print
    if "error" in data:
        print("\n[TheirStack ERROR]")
        print(data)
    elif "data" not in data:
        print("\n[TheirStack WARNING] No 'data' field in response.")
        print(response.text[:500])

    return data


# -------------------------------------------------------------------
# RANKING LOGIC
# -------------------------------------------------------------------

def rank_jobs(jobs: List[Dict[str, Any]], profile_skills: List[str]) -> List[Dict[str, Any]]:
    """
    Rank jobs based on overlap between user's skills and job title/description text.
    Simple heuristic: count how many skill phrases appear.
    """
    ranked: List[Dict[str, Any]] = []

    skill_phrases = [s.lower() for s in profile_skills]

    for job in jobs:
        title = job.get("job_title") or ""
        description = job.get("description") or ""
        company = job.get("company_name") or job.get("company") or ""
        location = job.get("long_location") or job.get("location") or job.get("short_location") or ""
        url = job.get("final_url") or job.get("url") or job.get("source_url") or ""

        combined_text = f"{title} {description}".lower()

        score = 0
        matched_skills = []
        for skill in skill_phrases:
            if skill and skill in combined_text:
                score += 1
                matched_skills.append(skill)

        ranked.append({
            "title": title,
            "company": company,
            "location": location,
            "url": url,
            "score": score,
            "matched_skills": sorted(set(matched_skills)),
        })

    ranked.sort(key=lambda x: (-x["score"], x["title"]))
    return ranked


# -------------------------------------------------------------------
# ORCHESTRATION: RUN SKILLSCOUT
# -------------------------------------------------------------------

def run_skillscout(config_path: str = USER_CONFIG_PATH) -> Dict[str, Any]:
    config = load_user_config(config_path)

    print("\n=== Loaded User Profile ===")
    print("Name:", config["user_profile"].get("name"))
    print("Target titles:")
    for t in config["user_profile"].get("target_titles", []):
        print("  -", t)

    body, all_skills = build_job_search_body(config)

    print("\n=== TheirStack Search Body ===")
    print(json.dumps(body, indent=2))

    print("\n=== Calling TheirStack /v1/jobs/search ===")
    resp = call_theirstack_job_search(body)

    if "data" not in resp:
        print("\nNo 'data' field in response; cannot rank jobs.")
        return {"config": config, "jobs_ranked": []}

    jobs_raw = resp.get("data", [])
    print(f"\nTotal jobs returned: {len(jobs_raw)}")

    ranked = rank_jobs(jobs_raw, all_skills)

    return {
        "config": config,
        "jobs_ranked": ranked,
        "raw_response": resp,
    }


# -------------------------------------------------------------------
# PRETTY-PRINT RESULTS
# -------------------------------------------------------------------

def print_top_jobs(result: Dict[str, Any], top_n: int = 10) -> None:
    jobs = result.get("jobs_ranked", [])[:top_n]

    print(f"\n\n=== Top {len(jobs)} SkillScout Matches ===\n")
    if not jobs:
        print("No jobs found. Try relaxing preferences or verifying filters/API key.")
        return

    for i, job in enumerate(jobs, start=1):
        print(f"[{i}] {job['title']} @ {job['company']}")
        if job["location"]:
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
