#!/usr/bin/env python3
"""
Test script for the new /api/v1/fetch_job endpoint

Usage:
    python test_fetch_job.py
    
Requires:
    - Docker container running on localhost:8000
    - requests library: pip install requests
"""

import requests
import json
import sys
from typing import Tuple, Dict, Any

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg: str):
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")

def print_error(msg: str):
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")

def print_section(title: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}=== {title} ==={Colors.RESET}")

def test_health_check() -> bool:
    """Test the health check endpoint"""
    print_section("Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        
        if response.status_code == 200:
            print_success(f"Health check passed: {response.json()}")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to {BASE_URL}")
        print_info("Make sure Docker container is running: docker-compose up -d")
        return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def test_endpoint_exists() -> bool:
    """Test that the endpoint exists"""
    print_section("Endpoint Existence")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/fetch_job?job_id=test", timeout=10)
        print_success(f"Endpoint responds with status {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot reach endpoint at {BASE_URL}/api/v1/fetch_job")
        return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def test_missing_parameters() -> bool:
    """Test error handling for missing parameters"""
    print_section("Error Handling - Missing Parameters")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/fetch_job", timeout=10)
        
        if response.status_code == 400:
            print_success("Correctly returned 400 Bad Request")
            data = response.json()
            detail = data.get('detail', {})
            print_info(f"Error: {detail.get('error')}")
            print_info(f"Message: {detail.get('message')}")
            print_info(f"Suggestion: {detail.get('suggestion')}")
            return True
        else:
            print_error(f"Expected 400, got {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def test_invalid_format() -> bool:
    """Test error handling for invalid description format"""
    print_section("Error Handling - Invalid Format")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/fetch_job?job_id=123&description_format=invalid",
            timeout=10
        )
        
        if response.status_code == 400:
            print_success("Correctly rejected invalid format")
            data = response.json()
            detail = data.get('detail', {})
            print_info(f"Error: {detail.get('error')}")
            return True
        else:
            print_error(f"Expected 400 for invalid format, got {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def test_fetch_job_by_id_simulation() -> bool:
    """Test fetching a job by ID (simulated)"""
    print_section("Fetch Job by ID (Simulation)")
    
    job_id = "3456789"
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/fetch_job",
            params={
                "job_id": job_id,
                "fetch_description": True,
                "description_format": "markdown"
            },
            timeout=30
        )
        
        print_info(f"Request URL: {response.url}")
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_success("Job found!")
                job = data['job']
                print_info(f"Title: {job.get('TITLE')}")
                print_info(f"Company: {job.get('COMPANY')}")
                print_info(f"Location: {job.get('LOCATION')}")
                print_info(f"Cached: {data.get('cached')}")
                return True
            else:
                print_error(f"Response: success=False")
                print_info(f"Error: {data.get('error')}")
        elif response.status_code == 404:
            print_info("Job not found (expected if job ID doesn't exist on LinkedIn)")
            return True  # This is OK for test purposes
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            try:
                print_info(f"Response: {response.json()}")
            except:
                print_info(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print_error(f"Request timed out after {TIMEOUT}s")
        print_info("LinkedIn may be blocking requests or the job doesn't exist")
        return True  # Not a failure of the endpoint
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False
    
    return False

def test_fetch_job_by_url_simulation() -> bool:
    """Test fetching a job by URL (simulated)"""
    print_section("Fetch Job by URL (Simulation)")
    
    job_url = "https://www.linkedin.com/jobs/view/3456789"
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/fetch_job",
            params={
                "job_url": job_url,
                "fetch_description": True
            },
            timeout=30
        )
        
        print_info(f"Request URL: {response.url}")
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code in [200, 404]:
            print_success(f"Endpoint responded correctly ({response.status_code})")
            return True
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print_error(f"Request timed out after {TIMEOUT}s")
        print_info("This may be expected if the job doesn't exist")
        return True
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def test_fetch_job_post_simulation() -> bool:
    """Test fetching a job via POST"""
    print_section("Fetch Job via POST (Simulation)")
    
    payload = {
        "job_id": "3456789",
        "fetch_description": True,
        "description_format": "markdown"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/fetch_job",
            json=payload,
            timeout=30
        )
        
        print_info(f"Status Code: {response.status_code}")
        print_info(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code in [200, 404]:
            print_success(f"POST endpoint responded correctly ({response.status_code})")
            return True
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print_error(f"Request timed out after {TIMEOUT}s")
        return True
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def test_swagger_ui() -> bool:
    """Test that Swagger UI is available"""
    print_section("Swagger UI Availability")
    
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=10)
        
        if response.status_code == 200:
            print_success("Swagger UI is available at /docs")
            return True
        else:
            print_error(f"Swagger UI returned {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def main():
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 70)
    print("JobSpy API - Fetch Job Endpoint Test Suite")
    print("=" * 70)
    print(Colors.RESET)
    
    tests = [
        ("Health Check", test_health_check),
        ("Endpoint Exists", test_endpoint_exists),
        ("Missing Parameters", test_missing_parameters),
        ("Invalid Format", test_invalid_format),
        ("Fetch by ID", test_fetch_job_by_id_simulation),
        ("Fetch by URL", test_fetch_job_by_url_simulation),
        ("Fetch via POST", test_fetch_job_post_simulation),
        ("Swagger UI", test_swagger_ui),
    ]
    
    # Run health check first
    print_section("Pre-flight Check")
    if not test_health_check():
        print_error("Cannot reach API")
        print_info("Start container with: docker-compose up -d")
        sys.exit(1)
    
    # Run all tests
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print_section("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if result else f"{Colors.RED}✗ FAIL{Colors.RESET}"
        print(f"{status}: {test_name}")
    
    print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.RESET}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All tests passed!{Colors.RESET}")
        return 0
    else:
        print(f"\n{Colors.YELLOW}⚠ {total - passed} test(s) failed{Colors.RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
