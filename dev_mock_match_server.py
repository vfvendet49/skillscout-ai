#!/usr/bin/env python3
"""
A tiny mock server that responds to POST /match with a canned JSON match result.
Run: python3 dev_mock_match_server.py
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class MockHandler(BaseHTTPRequestHandler):
    def _set_json(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_POST(self):
        if self.path == '/match':
            length = int(self.headers.get('content-length', 0))
            body = self.rfile.read(length).decode('utf-8') if length else ''
            try:
                data = json.loads(body) if body else {}
            except Exception:
                data = {}
            # Return a high-scoring match with matched keywords
            resp = {
                'score': 0.8,
            }
            # Provide coverage/cosine and matched keywords
            resp.update({
                'coverage': 0.72,
                'cosine': 0.81,
                'matched_keywords': ['Airflow', 'ETL', 'AWS S3'],
                'tweaks': []
            })
            self._set_json()
            self.wfile.write(json.dumps(resp).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    server = HTTPServer(('localhost', 8000), MockHandler)
    print('Mock match server running at http://localhost:8000')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        print('Server stopped')
