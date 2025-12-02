JobFinder AI Streamlit App — Package Structure

This README explains how to run JobFinder AI in development or production mode.

Project structure

```
/Users/jieunkim/
├── src/
│   └── jobfinder_app/
│       ├── __init__.py
│       └── app.py              # Main Streamlit app
├── scripts/
│   └── run_app.py              # CLI for running app (dev/prod)
├── tests/
│   └── example.spec.js         # Playwright E2E tests
├── requirements.txt            # Python dependencies
├── package.json                # Node.js / Playwright config
└── .streamlit/
    └── secrets.toml            # Streamlit secrets (local, not in git)
```

Run the app

Using the CLI (recommended):

```bash
# Development mode (hot reload, debug logging)
python scripts/run_app.py dev

# Production mode (optimized, reduced logging)
python scripts/run_app.py prod

# Custom port/host
python scripts/run_app.py dev --port 9000 --host 127.0.0.1
python scripts/run_app.py prod --port 8000 --host 0.0.0.0
```

Or directly with streamlit:

```bash
# Development
streamlit run src/jobfinder_app/app.py

# Production
streamlit run src/jobfinder_app/app.py \
  --logger.level=warning \
  --client.showErrorDetails=false \
  --client.toolbarMode=viewer
```

Configuration and secrets

The app reads the API base URL from the following (in order):
1. Environment variable `API_BASE` (recommended for CI/containers)
2. `st.secrets["API_BASE"]` from Streamlit secrets (optional, local dev only)
3. Defaults to `http://localhost:8000` if neither is set

Set environment variable example:

```bash
export API_BASE="https://api.example.com"
python scripts/run_app.py dev
```

Or create a local Streamlit secrets file (kept out of git):

```bash
mkdir -p ~/.streamlit
cat > ~/.streamlit/secrets.toml <<EOF
API_BASE = "https://api.example.com"
EOF
```

Installation & setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. (Optional) Install Playwright for E2E testing:
   ```bash
   npm install
   npx playwright install --with-deps
   ```

3. Run the app:
   ```bash
   python scripts/run_app.py dev
   ```

Development vs. production

**Development mode** (`python scripts/run_app.py dev`):
- Hot reload enabled (auto-restart on file changes)
- Debug logging (verbose output)
- Binds to localhost only
- Shows error details to help debugging

**Production mode** (`python scripts/run_app.py prod`):
- No hot reload
- Warning-level logging only
- Binds to 0.0.0.0 (accessible from any interface)
- Error details hidden from users
- XSRF protection enabled
- CORS disabled by default

Running tests

Run Playwright E2E tests (integrated with SkillScout backend):
```bash
npm test                    # headless (requires app running on localhost:8501)
npm run test:playwright:ui  # interactive UI mode
npm run test:playwright:debug # debug mode
```

### Test coverage

The updated test suite (`tests/example.spec.js`) includes:

**Smoke tests:**
- Page loads with correct title
- All tabs present (Profile & Prefs, Uploads, Results, Job Detail)

**Profile & Preferences Tab:**
- Form fields render (name, skills, industries, experience level, location, salary, etc.)
- User input submission to backend
- Job search triggering via SkillScout integration

**Uploads Tab:**
- Resume/cover letter file upload form
- Purpose selection

**Results Tab:**
- Job results display (from SkillScout API)
- Search limit slider
- Job ranking by skill match score

**Job Detail Tab:**
- Match computation form
- Threshold slider for matching

**Integration tests:**
- Full E2E workflow: fill profile → search → view results

### Running tests with the app

**Terminal 1 — Start the app:**
```bash
python scripts/run_app.py dev
# App runs on http://localhost:8501
```

**Terminal 2 — Run tests:**
```bash
# Interactive mode (recommended for development)
npm run test:playwright:ui

# Headless mode
npm test

# Debug mode (pause and inspect)
npm run test:playwright:debug
```

### Prerequisites for tests

- ✅ Streamlit app running (`python scripts/run_app.py dev`)
- ⚠️ Backend API running on `http://localhost:8000` (optional; tests skip gracefully if unavailable)
- ⚠️ SkillScout API credentials configured in `SkillScout_v3_phases.py` (for full integration)

Notes

- For development, use `python scripts/run_app.py dev` for the best experience.
- For containerized production (Docker/Kubernetes), use `python scripts/run_app.py prod` and inject `API_BASE` as an environment variable.
- Use a proper secrets manager (HashiCorp Vault, AWS Secrets Manager, 1Password) in production instead of local `.streamlit/secrets.toml`.
