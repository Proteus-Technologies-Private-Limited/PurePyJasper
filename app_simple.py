#!/usr/bin/env python3
"""
Simplified version of the main app to test step by step.
"""

from flask import Flask, render_template, redirect, url_for
import os

app = Flask(__name__)
app.secret_key = 'change-me'
app.config['DEBUG'] = True

@app.route('/')
def index():
    return '<h1>Jasper Reports App</h1><p><a href="/editor/">Go to Editor</a></p>'

@app.route('/editor/')
def editor_index():
    return '<h1>Editor Main Page</h1><p>This would be the editor</p>'

@app.route('/editor/test/<report_id>')
def test_route(report_id):
    return f'<h1>Test Route</h1><p>Report ID: {report_id}</p>'

@app.route('/editor/simple_sample/<report_id>')
def simple_sample(report_id):
    """Simple sample report route without complex dependencies."""
    valid_reports = ['customer_orders', 'customer_summary', 'orders_by_date']
    
    if report_id not in valid_reports:
        return f'<h1>Invalid Report</h1><p>Report ID: {report_id} not in {valid_reports}</p>'
    
    # Simple JRXML content
    jrxml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<jasperReport xmlns="http://jasperreports.sourceforge.net/jasperreports"
              name="{report_id}_Report" pageWidth="595" pageHeight="842">
    <title>
        <band height="60">
            <staticText>
                <reportElement x="0" y="20" width="555" height="30"/>
                <textElement textAlignment="Center">
                    <font size="18" isBold="true"/>
                </textElement>
                <text><![CDATA[{report_id.replace('_', ' ').title()} Report]]></text>
            </staticText>
        </band>
    </title>
</jasperReport>'''
    
    return f'''
    <html>
    <head><title>Sample: {report_id}</title></head>
    <body>
        <h1>Sample Report: {report_id}</h1>
        <p><a href="/editor/">Back to Editor</a></p>
        <h3>JRXML Content:</h3>
        <pre style="background: #f5f5f5; padding: 10px;">{jrxml_content}</pre>
    </body>
    </html>
    '''

if __name__ == '__main__':
    print("Starting simplified Flask app...")
    print("URLs:")
    print("  Root: http://127.0.0.1:8080/")
    print("  Editor: http://127.0.0.1:8080/editor/")
    print("  Test: http://127.0.0.1:8080/editor/test/customer_summary")
    print("  Sample: http://127.0.0.1:8080/editor/simple_sample/customer_summary")
    app.run(host='0.0.0.0', port=8080, debug=True)