# Testing Guide for SkillScout AI

## Quick Start Testing

### 1. Start the Streamlit App

```bash
streamlit run stremlit_app.py
```

The app will open automatically in your browser at `http://localhost:8501`

### 2. Verify API Connection

**Check the Sidebar:**
- Look for "🔗 API Connection" section
- Should show: `✅ Connected` (green)
- Backend URL: `https://skillscout-ai-1.onrender.com`

If it shows `❌ Cannot reach backend`, the API might be down or there's a network issue.

### 3. Test Each Feature

## Test 1: Save Profile (Tab 1: Profile & Prefs)

1. **Fill in the form:**
   - Name: Enter your name
   - Skills: Enter skills (comma-separated, e.g., "Python, SQL, FastAPI")
   - Industries: Enter industries (e.g., "Tech, Finance")
   - Experience level: Select from dropdown
   - Target titles: Enter job titles (e.g., "Software Engineer, Data Scientist")
   - Location: City, State, Country
   - Salary range: Set min/max
   - Job age limit: Use slider

2. **Click "Save Profile"**

3. **Expected Result:**
   - ✅ Green success message: "Profile saved successfully!"
   - No error messages

4. **If Error Occurs:**
   - Check error message for details
   - Verify API is running (check sidebar)
   - Check browser console for network errors

## Test 2: Upload Files (Tab 2: Uploads)

1. **Enter Purpose:**
   - Type a purpose (e.g., "consulting", "product", "ops")

2. **Upload Files:**
   - Resume: Upload a PDF or DOCX file
   - Cover Letter: Upload a PDF or DOCX file (optional)

3. **Click "Upload"**

4. **Expected Result:**
   - ✅ Green success message: "Files uploaded successfully!"

## Test 3: Search Jobs (Tab 3: Results)

1. **Set Search Parameters:**
   - Use slider to set "How many to fetch (top N)" (5-50)

2. **Click "Run Search"**

3. **Expected Result:**
   - ✅ Success message showing number of jobs found
   - Job cards displayed with:
     - Job title
     - Company name
     - Location
     - URL link
     - Source and posted date
   - "Open" button for each job

4. **Click "Open" on a job:**
   - Should switch to Tab 4 (Job Detail)

## Test 4: Job Match (Tab 4: Job Detail)

1. **Select a Job:**
   - Go to Tab 3 (Results)
   - Click "Open" on any job
   - OR manually select a job in Tab 4

2. **Enter Resume/Cover Letter Text:**
   - Paste resume text in the text area
   - Optionally paste cover letter text

3. **Set Match Threshold:**
   - Use slider (0.5 to 0.95, default 0.70)

4. **Click "Compute Match"**

5. **Expected Result:**
   - Match score displayed as metric
   - Progress bar showing score
   - Coverage and Cosine similarity scores
   - Suggestions/tweaks if score is below threshold

## Manual API Testing (Optional)

### Test API Directly

You can test the API endpoints directly using curl or the Swagger UI:

**Swagger UI:**
- Visit: https://skillscout-ai-1.onrender.com/docs
- Test endpoints interactively

**Using curl:**

```bash
# Health check
curl https://skillscout-ai-1.onrender.com/health

# Save profile
curl -X POST https://skillscout-ai-1.onrender.com/profile \
  -H "Content-Type: application/json" \
  -d '{
    "profile": {
      "name": "Test User",
      "skills": ["Python", "SQL"],
      "industries": ["Tech"],
      "experience_level": "mid-senior",
      "target_titles": ["Software Engineer"]
    },
    "preferences": {
      "location": {"city": "Atlanta", "state": "GA", "country": "US", "remote": false, "radius_miles": 50},
      "salary": {"min": 80000, "max": 150000},
      "employment_type": ["full-time"],
      "exclude_keywords": [],
      "company_preferences": {"preferred": [], "avoid": []},
      "job_age_limit_days": 45
    }
  }'
```

## Troubleshooting

### App won't start?
```bash
# Check if Streamlit is installed
pip install streamlit

# Check if all dependencies are installed
pip install -r requirements.txt
```

### API connection fails?
1. Check if API is online: https://skillscout-ai-1.onrender.com/health
2. Check browser console for CORS errors
3. Verify API URL in sidebar matches: `https://skillscout-ai-1.onrender.com`

### Getting 404 errors?
- Verify the endpoint exists in Swagger docs
- Check that you're using the correct HTTP method (POST vs GET)
- Verify request body format matches API expectations

### Getting 500 errors?
- Check API logs on Render dashboard
- Verify database connection
- Check API dependencies are installed

## Expected Behavior Summary

✅ **Working correctly:**
- Sidebar shows "✅ Connected"
- Save Profile shows success message
- Search returns job results
- Match calculation shows scores
- No error messages in red

❌ **Needs attention:**
- Sidebar shows "❌ Cannot reach backend"
- Red error messages appear
- Buttons don't respond
- Data doesn't save

