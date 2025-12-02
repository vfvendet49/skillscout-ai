#!/usr/bin/env python3
"""Helper script to start the FastAPI backend"""
import subprocess
import sys
import os

def main():
    print("=" * 60)
    print("Starting SkillScout FastAPI Backend")
    print("=" * 60)
    print(f"Backend will be available at: http://localhost:8000")
    print(f"API Documentation: http://localhost:8000/docs")
    print(f"Press Ctrl+C to stop the server\n")
    
    # Change to the project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        # Start uvicorn with the FastAPI app
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
    except FileNotFoundError:
        print("ERROR: uvicorn not found. Install it with:")
        print("  pip install uvicorn[standard]")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

