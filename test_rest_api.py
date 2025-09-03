#!/usr/bin/env python3
"""
Test script for the new REST API endpoints for Confluence MCP tools.
"""

import json
import requests
import sys
from typing import Dict, Any

def test_confluence_search_api(base_url: str = "http://localhost:8000", auth_token: str = None) -> Dict[str, Any]:
    """Test the /api/confluence/search endpoint."""
    url = f"{base_url}/api/confluence/search"
    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    payload = {
        "query": "test",
        "limit": 5
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Search API Status Code: {response.status_code}")
        print(f"Search API Response: {response.json()}")
        return response.json()
    except Exception as e:
        print(f"Error testing search API: {e}")
        return {"error": str(e)}

def test_confluence_get_page_api(base_url: str = "http://localhost:8000", auth_token: str = None) -> Dict[str, Any]:
    """Test the /api/confluence/get_page endpoint."""
    url = f"{base_url}/api/confluence/get_page"
    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    payload = {
        "page_id": "12345",  # This will likely fail but tests the endpoint
        "include_metadata": True,
        "convert_to_markdown": True
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Get Page API Status Code: {response.status_code}")
        print(f"Get Page API Response: {response.json()}")
        return response.json()
    except Exception as e:
        print(f"Error testing get_page API: {e}")
        return {"error": str(e)}

def test_health_check(base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """Test the health check endpoint."""
    url = f"{base_url}/healthz"

    try:
        response = requests.get(url)
        print(f"Health Check Status Code: {response.status_code}")
        print(f"Health Check Response: {response.json()}")
        return response.json()
    except Exception as e:
        print(f"Error testing health check: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8000"

    if len(sys.argv) > 2:
        auth_token = sys.argv[2]
    else:
        auth_token = None

    print(f"Testing REST API endpoints at {base_url}")
    print("=" * 50)

    # Test health check
    print("\n1. Testing Health Check:")
    test_health_check(base_url)

    # Test search API
    print("\n2. Testing Confluence Search API:")
    test_confluence_search_api(base_url, auth_token)

    # Test get_page API
    print("\n3. Testing Confluence Get Page API:")
    test_confluence_get_page_api(base_url, auth_token)

    print("\n" + "=" * 50)
    print("REST API testing completed!")
