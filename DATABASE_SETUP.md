# Database Setup Guide

## Problem
The "Not Found" error might be caused by missing database tables. The application uses SQLAlchemy to create tables, but on production (Render), tables might not be created automatically.

## Solution: Initialize Database Tables

### Option 1: Automatic Initialization (Recommended)

The app now automatically creates tables on startup. However, if tables are missing, you can manually initialize them.

### Option 2: Run Initialization Script

```bash
# For local development (SQLite)
python app/db_init.py

# Or for production (PostgreSQL)
# Make sure DATABASE_URL is set in environment
python app/db_init.py
```

### Option 3: Manual SQL Scripts

**For SQLite:**
```bash
sqlite3 jobfinder.db < app/db_init.sql
```

**For PostgreSQL:**
```bash
psql $DATABASE_URL -f app/db_init_postgresql.sql
```

## Verify Tables Exist

### Check via API

Visit the health endpoint:
```
GET https://skillscout-ai-1.onrender.com/health
```

Should return:
```json
{
  "status": "healthy",
  "database": "connected",
  "api": "SkillScout"
}
```

### Check via Swagger UI

1. Go to: https://skillscout-ai-1.onrender.com/docs
2. Try the `/health` endpoint
3. Check the response for database status

## Tables Required

The application needs these tables:

1. **user_profiles** - Stores user profile information
2. **user_preferences** - Stores user job preferences  
3. **user_uploads** - Stores uploaded files metadata

## For Render Deployment

### Add Build Command (Optional)

In your `render.yaml` or Render dashboard, you can add:

```yaml
services:
  - type: web
    name: skillscout-api
    env: python
    buildCommand: pip install -r requirements.txt && python app/db_init.py
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Environment Variables

Make sure `DATABASE_URL` is set in Render:
- Go to your service → Environment
- Add: `DATABASE_URL=postgresql://user:pass@host:port/dbname`

## Troubleshooting

### Error: "table user_profiles does not exist"

**Solution:** Run the initialization script:
```bash
python app/db_init.py
```

### Error: "database is locked" (SQLite)

**Solution:** 
- Make sure only one process is accessing the database
- For production, use PostgreSQL instead of SQLite

### Error: "relation does not exist" (PostgreSQL)

**Solution:**
1. Check DATABASE_URL is correct
2. Run: `python app/db_init.py`
3. Or manually run: `psql $DATABASE_URL -f app/db_init_postgresql.sql`

## Testing Database Connection

```python
# Test script
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./jobfinder.db")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print("✅ Database connection successful!")
```

