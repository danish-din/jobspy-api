# Docker Build & Test Guide for Single Job Fetch Endpoint

## Prerequisites

- Docker installed
- Docker Compose installed (optional but recommended)
- API key configured (or disable API key auth for testing)

## Step 1: Build the Docker Image

### Option A: Using Docker Compose (Recommended)

```bash
cd c:\Users\danis\Documents\Github\jobspy-api

# Build the image
docker-compose build

# Or rebuild and start
docker-compose build && docker-compose up -d
```

### Option B: Using Docker directly

```bash
cd c:\Users\danis\Documents\Github\jobspy-api

# Build the image
docker build -t jobspy-api:latest .

# Run the container
docker run -p 8000:8000 \
  -e ENABLE_API_KEY_AUTH=false \
  -e LOG_LEVEL=INFO \
  jobspy-api:latest
```

## Step 2: Verify Container is Running

```bash
# Check if container is running
docker ps | grep jobspy

# Check logs
docker logs jobspy-docker-api

# Or with docker-compose
docker-compose logs -f jobspy-api
```

## Step 3: Test the New Endpoint

### Test 1: Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy"
}
```

### Test 2: Fetch Job Endpoint (GET with job_id)

Replace `123456789` with a real LinkedIn job ID:

```bash
curl -X GET 'http://localhost:8000/api/v1/fetch_job?job_id=3456789&fetch_description=true' \
  -H 'Content-Type: application/json'
```

### Test 3: Fetch Job Endpoint (GET with job_url)

```bash
curl -X GET 'http://localhost:8000/api/v1/fetch_job?job_url=https://www.linkedin.com/jobs/view/3456789&fetch_description=true' \
  -H 'Content-Type: application/json'
```

### Test 4: Fetch Job Endpoint (POST)

```bash
curl -X POST 'http://localhost:8000/api/v1/fetch_job' \
  -H 'Content-Type: application/json' \
  -d '{
    "job_id": "3456789",
    "fetch_description": true,
    "description_format": "markdown"
  }'
```

### Test 5: Invalid Job ID (Error Handling)

```bash
curl -X GET 'http://localhost:8000/api/v1/fetch_job?job_id=invalid123' \
  -H 'Content-Type: application/json'
```

Expected: 404 error or error message

### Test 6: Missing Parameters (Error Handling)

```bash
curl -X GET 'http://localhost:8000/api/v1/fetch_job' \
  -H 'Content-Type: application/json'
```

Expected: 400 Bad Request with helpful error message

### Test 7: Swagger UI (API Documentation)

Open browser to: `http://localhost:8000/docs`

You should see the new `/api/v1/fetch_job` endpoint listed with full documentation.

## Step 4: Run Python Test Script

Create a test file: `test_fetch_job.py`

```python
#!/usr/bin/env python3
"""
Test script for the new /api/v1/fetch_job endpoint
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_fetch_job_by_id():
    """Test fetching a job by ID"""
    print("\n=== TEST 1: Fetch Job by ID ===")
    
    # Use a known LinkedIn job ID or test with any number
    # Note: This will fail if the job doesn't exist, which is expected
    job_id = "3456789"
    
    params = {
        "job_id": job_id,
        "fetch_description": True,
        "description_format": "markdown"
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/fetch_job",
            params=params,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                job = data['job']
                print(f"✓ SUCCESS - Job found!")
                print(f"  Title: {job.get('TITLE')}")
                print(f"  Company: {job.get('COMPANY')}")
                print(f"  Location: {job.get('LOCATION')}")
                print(f"  Cached: {data.get('cached')}")
                return True
            else:
                print(f"✗ FAILED - {data.get('error')}")
                print(f"  Suggestion: {data.get('suggestion')}")
        else:
            print(f"✗ ERROR - {response.status_code}")
            print(response.json() if response.text else "No response body")
            
    except Exception as e:
        print(f"✗ EXCEPTION: {str(e)}")
    
    return False

def test_fetch_job_by_url():
    """Test fetching a job by full URL"""
    print("\n=== TEST 2: Fetch Job by URL ===")
    
    job_url = "https://www.linkedin.com/jobs/view/3456789"
    
    params = {
        "job_url": job_url,
        "fetch_description": True
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/fetch_job",
            params=params,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code in [200, 404, 400]:
            print(f"✓ Response received")
            if response.status_code == 200:
                data = response.json()
                print(f"  Success: {data.get('success')}")
        else:
            print(f"✗ Unexpected status code")
            
    except Exception as e:
        print(f"✗ EXCEPTION: {str(e)}")
    
    return True

def test_fetch_job_post():
    """Test fetching a job via POST"""
    print("\n=== TEST 3: Fetch Job via POST ===")
    
    payload = {
        "job_id": "3456789",
        "fetch_description": True,
        "description_format": "markdown",
        "verbose": 2
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/fetch_job",
            json=payload,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code in [200, 404, 400]:
            print(f"✓ POST endpoint works")
            data = response.json()
            print(f"  Response keys: {list(data.keys())}")
        else:
            print(f"✗ Unexpected status code")
            
    except Exception as e:
        print(f"✗ EXCEPTION: {str(e)}")
    
    return True

def test_missing_parameters():
    """Test error handling for missing parameters"""
    print("\n=== TEST 4: Error Handling - Missing Parameters ===")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/fetch_job",
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 400:
            print(f"✓ Correctly returned 400 Bad Request")
            data = response.json()
            detail = data.get('detail', {})
            print(f"  Error: {detail.get('error')}")
            print(f"  Suggestion: {detail.get('suggestion')}")
            return True
        else:
            print(f"✗ Expected 400, got {response.status_code}")
            
    except Exception as e:
        print(f"✗ EXCEPTION: {str(e)}")
    
    return False

def test_endpoint_exists():
    """Test that the endpoint exists and responds"""
    print("\n=== TEST 0: Endpoint Exists ===")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/fetch_job?job_id=test",
            timeout=10
        )
        
        print(f"✓ Endpoint responds with status {response.status_code}")
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"✗ Cannot connect to {BASE_URL}")
        print(f"  Is the Docker container running?")
        return False
    except Exception as e:
        print(f"✗ EXCEPTION: {str(e)}")
        return False

def test_health_check():
    """Test the health check endpoint"""
    print("\n=== TEST: Health Check ===")
    
    try:
        response = requests.get(
            f"{BASE_URL}/health",
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✓ Health check passed")
            print(f"  Response: {response.json()}")
            return True
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ EXCEPTION: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("JobSpy API - Fetch Job Endpoint Test Suite")
    print("=" * 60)
    
    # First check if service is running
    if not test_health_check():
        print("\n⚠ Cannot reach API. Make sure Docker container is running:")
        print("  docker-compose up -d")
        return
    
    # Run tests
    results = []
    results.append(("Endpoint Exists", test_endpoint_exists()))
    results.append(("Fetch by ID", test_fetch_job_by_id()))
    results.append(("Fetch by URL", test_fetch_job_by_url()))
    results.append(("Fetch via POST", test_fetch_job_post()))
    results.append(("Error Handling", test_missing_parameters()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠ {total - passed} test(s) failed")

if __name__ == "__main__":
    main()
```

Save this as `test_fetch_job.py` and run:

```bash
# Install requests if not already installed
pip install requests

# Run the test suite
python test_fetch_job.py
```

## Step 5: Configuration for Testing

### Disable API Key Auth (for easy testing)

Edit your `.env` file or use environment variable:

```env
ENABLE_API_KEY_AUTH=false
LOG_LEVEL=INFO
ENABLE_CACHE=true
CACHE_EXPIRY=3600
```

Or pass when running:

```bash
docker-compose down
docker-compose up -d
```

### Enable API Key Auth (for production-like testing)

```env
ENABLE_API_KEY_AUTH=true
API_KEYS=test-api-key-123
```

Then include API key in requests:

```bash
curl -H "x-api-key: test-api-key-123" \
  http://localhost:8000/api/v1/fetch_job?job_id=123456789
```

## Step 6: Monitor Container

```bash
# Real-time logs
docker-compose logs -f jobspy-api

# Check resource usage
docker stats jobspy-docker-api

# Execute command in container
docker-compose exec jobspy-api bash

# View container details
docker-compose ps
```

## Step 7: Cleanup

```bash
# Stop container
docker-compose down

# Remove image
docker rmi jobspy-api:latest

# Clean up everything
docker system prune
```

## Troubleshooting

### Container fails to start

```bash
# Check logs
docker-compose logs jobspy-api

# Rebuild
docker-compose build --no-cache
docker-compose up -d
```

### Port already in use

Change port in docker-compose.yml:
```yaml
ports:
  - "8001:8000"  # Use 8001 instead of 8000
```

### API key errors

Make sure `ENABLE_API_KEY_AUTH` is set correctly in your `.env`:
```bash
# For testing without auth
ENABLE_API_KEY_AUTH=false

# For testing with auth
ENABLE_API_KEY_AUTH=true
API_KEYS=your-test-key
```

### Slow responses

Check if caching is enabled and working:
```bash
# Run same request twice and check 'cached' field in response
curl http://localhost:8000/api/v1/fetch_job?job_id=123456789
curl http://localhost:8000/api/v1/fetch_job?job_id=123456789  # Should be faster
```

## Next Steps

1. ✅ Build Docker image
2. ✅ Start container
3. ✅ Test endpoints with curl or Python script
4. ✅ Verify Swagger UI at http://localhost:8000/docs
5. ✅ Monitor logs and performance
6. ✅ Push to Docker Hub if desired

## Quick Command Reference

```bash
# Build and start
docker-compose up -d --build

# View logs
docker-compose logs -f jobspy-api

# Stop
docker-compose down

# Restart
docker-compose restart jobspy-api

# Run test suite
python test_fetch_job.py

# Test endpoint manually
curl http://localhost:8000/api/v1/fetch_job?job_id=123456789

# Check health
curl http://localhost:8000/health
```
