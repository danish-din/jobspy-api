# Single Job Fetch Endpoint Documentation

## Overview

The new `/api/v1/fetch_job` endpoint allows you to scrape and retrieve details for a **single LinkedIn job** by providing either:
1. A full LinkedIn job URL
2. A LinkedIn job ID

The returned job data is in the same format as the search results from the `/api/v1/search_jobs` endpoint.

## Endpoints

### GET /api/v1/fetch_job

Fetch a single LinkedIn job using URL query parameters.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| job_url | string | No* | Full URL to the LinkedIn job (e.g., `https://www.linkedin.com/jobs/view/123456789`) |
| job_id | string | No* | LinkedIn job ID (e.g., `123456789`) |
| fetch_description | boolean | No | Fetch full job description (default: true) |
| description_format | string | No | Format of description: `markdown` or `html` (default: `markdown`) |
| verbose | integer | No | Verbosity level: 0 (errors), 1 (warnings), 2 (all logs) (default: 2) |

*Either `job_url` or `job_id` must be provided.

**Example Requests:**

```bash
# Using job ID
curl -X 'GET' \
  'http://localhost:8000/api/v1/fetch_job?job_id=123456789' \
  -H 'x-api-key: your-api-key'

# Using full URL
curl -X 'GET' \
  'http://localhost:8000/api/v1/fetch_job?job_url=https://www.linkedin.com/jobs/view/123456789' \
  -H 'x-api-key: your-api-key'

# With custom settings
curl -X 'GET' \
  'http://localhost:8000/api/v1/fetch_job?job_id=123456789&fetch_description=true&description_format=html&verbose=1' \
  -H 'x-api-key: your-api-key'
```

### POST /api/v1/fetch_job

Fetch a single LinkedIn job using a JSON request body.

**Request Body:**
```json
{
  "job_url": "https://www.linkedin.com/jobs/view/123456789",
  "job_id": "123456789",
  "fetch_description": true,
  "description_format": "markdown",
  "verbose": 2
}
```

**Note:** Either `job_url` or `job_id` must be provided in the request body.

**Example Request:**

```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/fetch_job' \
  -H 'x-api-key: your-api-key' \
  -H 'Content-Type: application/json' \
  -d '{
    "job_id": "123456789",
    "fetch_description": true,
    "description_format": "markdown"
  }'
```

## Response Format

**Success Response (HTTP 200):**
```json
{
  "success": true,
  "job": {
    "SITE": "linkedin",
    "TITLE": "Software Engineer",
    "COMPANY": "Example Corp",
    "LOCATION": "San Francisco, CA",
    "COUNTRY": "USA",
    "LINK": "https://www.linkedin.com/jobs/view/123456789",
    "DESCRIPTION": "Job description text in markdown or HTML format...",
    "JOB_TYPE": "fulltime",
    "SALARY_CURRENCY": "USD",
    "MIN_AMOUNT": 150000,
    "MAX_AMOUNT": 200000,
    "INTERVAL": "yearly",
    "DATE_POSTED": "2024-01-15",
    "EMAIL_REQUIRED": false,
    "JOB_LEVEL": "mid-level",
    "COMPANY_INDUSTRY": "Technology",
    ...other fields...
  },
  "cached": false
}
```

**Error Response (HTTP 400):**
```json
{
  "error": "Missing required parameter",
  "message": "Either 'job_url' or 'job_id' must be provided",
  "suggestion": "Provide either a full LinkedIn job URL or just the job ID number"
}
```

**Not Found Response (HTTP 404):**
```json
{
  "error": "Job not found",
  "message": "Could not find the LinkedIn job with the provided URL or ID",
  "suggestion": "Verify that the job URL or ID is correct and the job still exists on LinkedIn"
}
```

**Server Error Response (HTTP 500):**
```json
{
  "error": "Error fetching job",
  "message": "Detailed error message...",
  "suggestion": "Helpful suggestion based on the error type"
}
```

## Response Fields

The `job` object contains the following fields (from the JobSpy library):

### Standard Fields (All Jobs)
| Field | Type | Description |
|-------|------|-------------|
| SITE | string | Job board source (linkedin) |
| TITLE | string | Job title |
| COMPANY | string | Company name |
| LOCATION | string | Job location |
| COUNTRY | string | Country code |
| LINK | string | Direct URL to the job posting |
| DESCRIPTION | string | Full job description |
| JOB_TYPE | string | Employment type (fulltime, parttime, contract, internship) |
| DATE_POSTED | string | Date when the job was posted |
| SALARY_CURRENCY | string | Currency code (USD, EUR, GBP, etc.) |
| MIN_AMOUNT | number | Minimum salary |
| MAX_AMOUNT | number | Maximum salary |
| INTERVAL | string | Salary interval (yearly, monthly, hourly) |
| EMAIL_REQUIRED | boolean | Whether email is required to apply |

### LinkedIn-Specific Fields
| Field | Type | Description |
|-------|------|-------------|
| JOB_LEVEL | string | Job level (entry-level, mid-level, senior, director, executive) |
| COMPANY_INDUSTRY | string | Industry classification |
| COMPANY_URL | string | Company website URL |
| IS_REMOTE | boolean | Whether the job is remote |
| JOB_FUNCTION | string | Job function/category |
| COMPANY_ID | string | LinkedIn company ID |

## Usage Examples

### Python with Requests Library

```python
import requests
import json

BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key"

# Fetch by job ID
def fetch_job_by_id(job_id):
    params = {
        "job_id": job_id,
        "fetch_description": True,
        "description_format": "markdown"
    }
    
    response = requests.get(
        f"{BASE_URL}/api/v1/fetch_job",
        params=params,
        headers={"x-api-key": API_KEY}
    )
    
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            job = data['job']
            print(f"Title: {job['TITLE']}")
            print(f"Company: {job['COMPANY']}")
            print(f"Location: {job['LOCATION']}")
            print(f"Cached: {data['cached']}")
            return job
        else:
            print(f"Error: {data['error']}")
    else:
        print(f"HTTP Error {response.status_code}: {response.text}")
    
    return None

# Fetch by URL
def fetch_job_by_url(job_url):
    params = {
        "job_url": job_url,
        "fetch_description": True
    }
    
    response = requests.get(
        f"{BASE_URL}/api/v1/fetch_job",
        params=params,
        headers={"x-api-key": API_KEY}
    )
    
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            return data['job']
    
    return None

# POST method
def fetch_job_post(job_id):
    payload = {
        "job_id": job_id,
        "fetch_description": True,
        "description_format": "markdown",
        "verbose": 2
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/fetch_job",
        json=payload,
        headers={"x-api-key": API_KEY}
    )
    
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            return data['job']
    
    return None

# Usage
if __name__ == "__main__":
    job = fetch_job_by_id("123456789")
    if job:
        print(json.dumps(job, indent=2, default=str))
```

### JavaScript/Node.js

```javascript
const API_KEY = "your-api-key";
const BASE_URL = "http://localhost:8000";

// Fetch by job ID
async function fetchJobById(jobId) {
    const params = new URLSearchParams({
        job_id: jobId,
        fetch_description: true,
        description_format: "markdown"
    });
    
    try {
        const response = await fetch(
            `${BASE_URL}/api/v1/fetch_job?${params}`,
            {
                method: 'GET',
                headers: {
                    'x-api-key': API_KEY
                }
            }
        );
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                return data.job;
            } else {
                console.error(`Error: ${data.error}`);
            }
        } else {
            console.error(`HTTP Error: ${response.status}`);
        }
    } catch (error) {
        console.error("Network error:", error);
    }
    
    return null;
}

// Fetch by URL
async function fetchJobByUrl(jobUrl) {
    const params = new URLSearchParams({
        job_url: jobUrl,
        fetch_description: true
    });
    
    const response = await fetch(
        `${BASE_URL}/api/v1/fetch_job?${params}`,
        {
            method: 'GET',
            headers: {
                'x-api-key': API_KEY
            }
        }
    );
    
    if (response.ok) {
        const data = await response.json();
        return data.success ? data.job : null;
    }
    
    return null;
}

// Usage
(async () => {
    const job = await fetchJobById("123456789");
    if (job) {
        console.log(JSON.stringify(job, null, 2));
    }
})();
```

## Caching

The endpoint supports response caching. The `cached` field in the response indicates whether the result was served from cache:
- `"cached": false` - Fresh data from LinkedIn
- `"cached": true` - Data retrieved from cache (faster response)

Cache expiry can be configured via the `CACHE_EXPIRY` environment variable (default: 3600 seconds).

## Error Handling

### Common Error Scenarios

**Missing Required Parameter:**
```json
{
  "error": "Missing required parameter",
  "message": "Either 'job_url' or 'job_id' must be provided",
  "suggestion": "Provide either a full LinkedIn job URL or just the job ID number"
}
```

**Invalid Job URL/ID:**
```json
{
  "error": "Job not found",
  "message": "Could not find the LinkedIn job with the provided URL or ID",
  "suggestion": "Verify that the job URL or ID is correct and the job still exists on LinkedIn"
}
```

**Proxy/Network Issues:**
```json
{
  "error": "Error fetching job",
  "message": "Connection error...",
  "suggestion": "Check your proxy configuration or try without a proxy"
}
```

**CAPTCHA Encountered:**
```json
{
  "error": "Error fetching job",
  "message": "CAPTCHA encountered...",
  "suggestion": "A CAPTCHA was encountered. Try using a different proxy or wait before retrying"
}
```

## Rate Limiting

The endpoint is subject to the same rate limiting as other API endpoints. If you exceed the rate limit, you'll receive a 429 (Too Many Requests) response.

## Comparison with Search Endpoint

| Feature | `/search_jobs` | `/fetch_job` |
|---------|---|---|
| Multiple jobs | ✓ | ✗ (single job only) |
| Search by keywords | ✓ | ✗ |
| Filter by location | ✓ | ✗ |
| Requires job ID/URL | ✗ | ✓ |
| Faster response | ✗ (searches all jobs) | ✓ (targets specific job) |
| Pagination | ✓ | ✗ |
| Same response format | ✓ | ✓ |

## Implementation Details

The endpoint:
1. Accepts either a LinkedIn job URL or job ID
2. Extracts the job ID from the URL if provided
3. Constructs the LinkedIn job URL
4. Checks the cache for existing results
5. If not cached, scrapes the job details from LinkedIn using the JobSpy library
6. Returns the job data in the same format as the search results
7. Caches the result for future requests

## Limitations

- Only works with LinkedIn jobs (LinkedIn site support)
- Job must still exist and be publicly accessible on LinkedIn
- May encounter CAPTCHA challenges if LinkedIn detects unusual activity
- Requires a valid LinkedIn job ID or URL format

## Future Enhancements

Potential improvements for future versions:
- Support for other job boards (Indeed, Glassdoor, etc.)
- Batch fetching of multiple jobs in a single request
- Advanced filtering on the single job results
- Job comparison endpoints
