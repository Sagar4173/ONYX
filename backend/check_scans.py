#!/usr/bin/env python3
"""
Check scan status from the reports API
"""
import requests
import json

def check_scans():
    """Check recent scan reports"""
    try:
        response = requests.get("http://localhost:8000/api/reports/")
        if response.status_code == 200:
            data = response.json()
            reports = data.get('reports', [])
            
            print(f"Found {len(reports)} scan reports:")
            print("=" * 80)
            
            for report in reports[:5]:  # Show last 5 scans
                print(f"Project: {report['project_name']}")
                print(f"Scan ID: {report['scan_id']}")
                print(f"Status: {report['status']}")
                print(f"Repository: {report['repository_url']}")
                print(f"Branch: {report['branch']}")
                print(f"Created: {report['created_at']}")
                print(f"Total Findings: {report['total_findings']}")
                print(f"Duration: {report['duration_seconds']} seconds")
                print(f"Findings by Severity: {json.dumps(report['findings_by_severity'], indent=2)}")
                print("-" * 80)
                
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Error checking scans: {e}")

if __name__ == "__main__":
    check_scans()
