#!/usr/bin/env python3
"""
Minimal Flask app test to isolate the issue.
"""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '<h1>Minimal Flask App Works!</h1><p>This is a test.</p>'

@app.route('/test')
def test():
    return '<h1>Test Route Works!</h1>'

if __name__ == '__main__':
    print("Starting minimal Flask app...")
    print("Visit: http://127.0.0.1:8080/")
    app.run(host='0.0.0.0', port=8080, debug=True)