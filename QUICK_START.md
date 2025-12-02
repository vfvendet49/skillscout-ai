# Quick Start Guide

## The Error You're Seeing

If you see `{"detail":"Not Found"}` or connection errors, it means the **FastAPI backend is not running**.

## Solution: Start the Backend

### Option 1: Using the Helper Script (Easiest)

```bash
python start_backend.py
```

### Option 2: Manual Start

```bash
uvicorn app.main:app --reload
```

The backend will start on `http://localhost:8000`

## Then Start the Streamlit App

In a **separate terminal**, run:

```bash
streamlit run stremlit_app.py
```

Or:

```bash
python -m streamlit run stremlit_app.py
```

## Verify It's Working

1. **Check backend is running:**
   - Open: http://localhost:8000/docs
   - You should see the API documentation

2. **Check Streamlit app:**
   - It should open automatically at http://localhost:8501
   - Try clicking "Save Profile" - it should work now!

## Troubleshooting

### Backend won't start?
- Make sure you've installed dependencies: `pip install -r requirements.txt`
- Check if port 8000 is already in use

### Still getting 404 errors?
- Make sure the backend is running on port 8000
- Check the API URL in Streamlit (should be `http://localhost:8000`)
- Look at the backend terminal for error messages

### Connection refused?
- Backend isn't running - start it first!
- Check firewall settings

