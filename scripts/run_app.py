#!/usr/bin/env python3
"""
run_app.py — CLI for running JobFinder AI app in dev or production mode.

Usage:
    python scripts/run_app.py dev
    python scripts/run_app.py prod
    python scripts/run_app.py --help
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory (parent of scripts/)."""
    return Path(__file__).parent.parent


def run_dev(port: int = 8501, host: str = "localhost") -> None:
    """Run Streamlit app in development mode with hot reload."""
    project_root = get_project_root()
    app_path = project_root / "src" / "jobfinder_app" / "app.py"
    
    if not app_path.exists():
        print(f"Error: app.py not found at {app_path}")
        sys.exit(1)
    
    print(f"Starting JobFinder AI in DEV mode on http://{host}:{port}")
    print(f"App path: {app_path}")
    print(f"Press Ctrl+C to stop.\n")
    
    # Run streamlit with development settings
    cmd = [
        "streamlit",
        "run",
        str(app_path),
        "--logger.level=debug",
        f"--server.port={port}",
        f"--server.address={host}",
    ]
    
    try:
        subprocess.run(cmd, check=False)
    except KeyboardInterrupt:
        print("\nShutdown requested.")
        sys.exit(0)
    except FileNotFoundError:
        print("Error: streamlit command not found. Install with: pip install streamlit")
        sys.exit(1)


def run_prod(port: int = 8501, host: str = "0.0.0.0") -> None:
    """Run Streamlit app in production mode."""
    project_root = get_project_root()
    app_path = project_root / "src" / "jobfinder_app" / "app.py"
    
    if not app_path.exists():
        print(f"Error: app.py not found at {app_path}")
        sys.exit(1)
    
    print(f"Starting JobFinder AI in PRODUCTION mode on {host}:{port}")
    print(f"App path: {app_path}")
    print(f"Press Ctrl+C to stop.\n")
    
    # Run streamlit with production settings
    cmd = [
        "streamlit",
        "run",
        str(app_path),
        "--logger.level=warning",
        "--client.showErrorDetails=false",
        "--client.toolbarMode=viewer",
        f"--server.port={port}",
        f"--server.address={host}",
        "--server.enableXsrfProtection=true",
        "--server.enableCORS=false",
    ]
    
    try:
        subprocess.run(cmd, check=False)
    except KeyboardInterrupt:
        print("\nShutdown requested.")
        sys.exit(0)
    except FileNotFoundError:
        print("Error: streamlit command not found. Install with: pip install streamlit")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="JobFinder AI app runner",
        epilog="Examples:\n  python scripts/run_app.py dev\n  python scripts/run_app.py prod --port 9000"
    )
    
    parser.add_argument(
        "mode",
        choices=["dev", "prod"],
        help="Run mode: dev (development) or prod (production)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to run on (default: 8501 for dev, 8501 for prod)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Host to bind to (default: localhost for dev, 0.0.0.0 for prod)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "dev":
        port = args.port or 8501
        host = args.host or "localhost"
        run_dev(port=port, host=host)
    elif args.mode == "prod":
        port = args.port or 8501
        host = args.host or "0.0.0.0"
        run_prod(port=port, host=host)


if __name__ == "__main__":
    main()
