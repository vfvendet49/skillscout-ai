#!/usr/bin/env python3
"""
Smoke test: POST to mock /match server, then (if score >= threshold) print mocked ChatGPT suggestions.
Run with: OPENAI_API_KEY=MOCK python3 dev_smoke_test.py
"""
import os
import requests
import json

API = 'http://localhost:8000'

def main():
    payload = {
        'job': {'title': 'Data Engineer', 'company': 'Acme', 'description': 'Build pipelines'},
        'resume_text': 'Experienced data engineer with 3 years building pipelines',
        'cover_text': 'I love data',
        'threshold': 0.7
    }
    r = requests.post(f"{API}/match", json=payload)
    print('POST /match ->', r.status_code)
    m = r.json()
    print('Match response:', json.dumps(m, indent=2))
    score = float(m.get('score', 0))
    threshold = float(payload['threshold'])
    if score >= threshold:
        key = os.getenv('OPENAI_API_KEY')
        if key == 'MOCK' or key is None:
            print('\nMOCK ChatGPT suggestions:')
            tweaks = [
                {"type": "add", "message": "Add a bullet about automating ETL pipelines using Airflow.", "keywords": ["Airflow", "ETL", "automation"]},
                {"type": "emphasize", "message": "Emphasize your experience with AWS S3 and data lakes.", "keywords": ["AWS S3", "data lake"]},
                {"type": "remove", "message": "Remove personal projects not related to data engineering.", "keywords": []}
            ]
            print(json.dumps(tweaks, indent=2))
        else:
            print('OPENAI_API_KEY provided but live API call not implemented in this smoke test.')
    else:
        print('Score below threshold; no AI suggestions triggered.')

if __name__ == '__main__':
    main()
