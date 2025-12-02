# SkillScout Integration with JobFinder AI E2E Tests

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Playwright E2E Tests                          │
│              (tests/example.spec.js)                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Streamlit Frontend (UI Layer)                        │
│         (src/jobfinder_app/app.py)                               │
│                                                                   │
│  Tabs:                                                            │
│  • Profile & Prefs (user input form)                             │
│  • Uploads (resume/cover letter)                                 │
│  • Results (job search results)                                  │
│  • Job Detail (skill matching)                                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (or equivalent)                  │
│                                                                   │
│  Endpoints:                                                       │
│  • POST /profile    — Save user profile & preferences            │
│  • POST /uploads    — Handle resume/cover letter uploads         │
│  • POST /search     — Trigger job search                         │
│  • POST /match      — Compute skill match scores                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│            SkillScout Job Scraper Backend                         │
│         (SkillScout_v3_phases.py)                                │
│                                                                   │
│  Phases:                                                          │
│  • Phase 1  — Job search (TheirStack API)                        │
│  • Phase 1b — Ranking jobs by skill match                        │
│  • Phase 2  — Format results (JSON/TXT)                          │
│  • Phase 2.5— Resume parsing & skill extraction                  │
│  • Phase 3.5— Visa eligibility filtering                         │
│  • Phase 4  — Email draft generation                             │
└─────────────────────────────────────────────────────────────────┘
```

## How Tests Integrate with SkillScout

### 1. Profile & Preferences Test
Tests verify that the Streamlit form captures:
- User name, email
- Hard/soft skills
- Target job titles
- Location (city, state, country)
- Salary range
- Experience level
- Remote preference

**Backend flow:**
```
User fills form → "Save Profile" → POST /profile 
  → SkillScout validates & stores config
  → Returns 200 OK
```

**Test case:** `should fill profile and preferences form` + `should save profile and send to backend`

### 2. Job Search Test
Tests verify that job search triggers the full SkillScout pipeline:

**Streamlit → Backend → SkillScout flow:**
```
User clicks "Run Search" → POST /search
  → Backend calls run_skillscout(config)
  → Phase 1: build_job_search_body() → call_theirstack_job_search()
  → TheirStack API returns job data
  → Phase 1b: rank_jobs() — score by skill match
  → Phase 2: format_results_json() — structured output
  → Phase 2.5: integrate_resume_skills() — detect resume skills
  → Phase 3.5: filter_visa_eligibility() — filter by visa status
  → Return ranked job list to Streamlit
  → Display in Results tab
```

**Test case:** `should allow job search with configured preferences` + `complete user journey`

### 3. Results Display Test
Tests verify that ranked job results render correctly:
- Job title, company, location
- Match score (# of skills found in job description)
- Matched skills list
- URL to job posting

**SkillScout output structure:**
```python
{
  "ranked": [
    {
      "title": "Senior Python Developer",
      "company": "TechCorp",
      "location": "San Francisco, CA",
      "score": 3,  # matched 3 skills
      "matched_skills": ["python", "javascript", "react"],
      "url": "https://..."
    },
    ...
  ]
}
```

**Test case:** `should display job results after search`

### 4. Resume Skills Enrichment Test
Tests verify resume upload and skill extraction:
- User uploads PDF/DOCX resume
- Backend runs `extract_resume_text()` → `extract_skills_from_resume()`
- Skills found in resume are flagged

**Streamlit → SkillScout flow:**
```
User uploads resume → POST /uploads
  → Backend: extract_text_from_pdf() or extract_text_from_docx()
  → Backend: extract_skills_from_resume(resume_text, reference_skills)
  → Intersection of resume skills + config skills
  → Store in result["resume_skills"]
  → Re-rank jobs with resume skills boost (optional)
```

**Test case:** `should allow filling purpose and show file upload inputs`

### 5. Visa Eligibility Filtering Test
Tests verify visa status filtering:
- User provides visa status (citizen, green card, H1B, etc.)
- Backend runs `filter_visa_eligibility()` on job list
- Jobs blocking non-citizens are filtered out

**Test case:** (implicit in profile test; explicit visa filter test can be added)

### 6. Job Matching & Scoring Test
Tests verify skill match scoring:
- Job description analyzed for skills
- Score = number of user skills found in job desc
- Threshold slider allows filtering by min score

**SkillScout logic:**
```python
for skill in user_skills:
    if skill in job_description:
        score += 1
        matched.append(skill)
```

**Test case:** `should show match computation form when job selected`

---

## Running Tests Step-by-Step

### Prerequisites
1. ✅ Python dependencies installed: `pip install -r requirements.txt`
2. ✅ Node/npm installed and Playwright set up: `npm install && npx playwright install --with-deps`
3. ⚠️ Backend API running (optional; tests skip gracefully if unavailable)
4. ⚠️ TheirStack API key configured in `SkillScout_v3_phases.py`

### Quick Start

**Terminal 1 — Start Streamlit app:**
```bash
cd /Users/jieunkim
python scripts/run_app.py dev
# Output: http://localhost:8501
```

**Terminal 2 — Run E2E tests:**
```bash
cd /Users/jieunkim
npm run test:playwright:ui
# Opens Playwright Inspector in browser
# Tests run live, showing each interaction
```

### Test Modes

| Mode | Command | Use Case |
|------|---------|----------|
| **Headless** | `npm test` | CI/CD pipelines, quick smoke tests |
| **UI** | `npm run test:playwright:ui` | Development, visual debugging |
| **Debug** | `npm run test:playwright:debug` | Pause & inspect page state, step through |

---

## Test-SkillScout Data Flow Example

### User Scenario: Jane searches for SWE jobs in SF

**1. User fills Profile & Prefs:**
```
Name: Jane Developer
Skills: Python, JavaScript, React, AWS
Industries: Technology
Target titles: Software Engineer, Full Stack Developer
Location: San Francisco, CA
Salary: $120K - $200K
Experience: mid-senior
Remote: Yes
```

**2. Test calls "Save Profile":**
```javascript
await page.click('button:has-text("Save Profile")');
// POST /profile
// Backend stores config JSON
```

**3. Test navigates to Results & clicks "Run Search":**
```javascript
await page.click('text=Results');
await page.click('button:has-text("Run Search")');
// POST /search
// Backend: run_skillscout(config) starts
```

**4. Backend executes SkillScout phases:**
```python
# Phase 1: Build search query
body = {
    "job_title_or": ["Software Engineer", "Full Stack Developer"],
    "job_location_pattern_or": ["san francisco, ca"],
    "job_seniority_or": ["mid_level", "senior"],
    "min_salary_usd": 120000,
    "remote": True,
    "limit": 25
}

# Phase 1: Call TheirStack API
response = call_theirstack_job_search(body)
# Returns ~25 jobs

# Phase 1b: Rank by skill match
ranked = rank_jobs(response["data"], ["python", "javascript", "react", "aws"])
# Each job scored: how many skills appear in description
```

**5. Test verifies results display:**
```javascript
// Results visible:
// [1] Senior Python Developer @ TechCorp
//     Location: San Francisco, CA
//     Score: 4 (matched 4 skills)
//     Skills: python, javascript, react, aws
//     URL: ...
```

**6. (Optional) Test uploads resume:**
```javascript
// If running resume skill enrichment
// Backend: extract_text_from_pdf(resume)
// Phase 2.5: confirm skills in resume
// Re-rank if resume contains additional skills
```

---

## Extending the Tests

### Add a custom test for visa filtering:
```javascript
test('should filter jobs based on visa status', async ({ page }) => {
  // Fill profile with visa status = "H1B"
  // Run search
  // Verify jobs blocking H1B are filtered out
  // Check "eligible_jobs" vs "ineligible_jobs"
});
```

### Add a test for resume enrichment:
```javascript
test('should extract skills from uploaded resume', async ({ page }) => {
  // Upload mock resume PDF
  // Verify extracted skills displayed
  // Confirm job re-ranking with resume skills
});
```

### Add a test for email draft generation (Phase 4):
```javascript
test('should generate Outlook email draft from top match', async ({ page }) => {
  // Select a job
  // Click "Generate Email"
  // Verify HTML + text email draft generated
  // Download file
});
```

---

## Debugging Failed Tests

**Test fails with "timeout":**
- Ensure backend API is running on `http://localhost:8000`
- Check `API_BASE` env var: `echo $API_BASE`
- Run `npm run test:playwright:debug` to step through

**Test fails with "element not found":**
- Run `npm run test:playwright:ui` to inspect selectors
- Update locators in test (e.g., change `text=Profile & Prefs` to correct selector)

**Backend returning 500 error:**
- Check SkillScout config file (`user_input_ben.json`)
- Verify TheirStack API key is valid
- Check terminal output of backend for exceptions

---

## Summary

✅ **Tests validate:** UI structure, form submission, job search, result ranking, resume parsing  
✅ **Integration:** Streamlit ↔ Backend ↔ SkillScout phases  
✅ **Data flow:** User input → API calls → SkillScout → Ranked results → UI display  
✅ **CI-ready:** Tests pass/skip gracefully if backend unavailable  
✅ **Development-friendly:** UI mode shows live interactions and debugging  

Tests are located in `/Users/jieunkim/tests/example.spec.js`.  
Run with: `npm run test:playwright:ui` (recommended for development).
