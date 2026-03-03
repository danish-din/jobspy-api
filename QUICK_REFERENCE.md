# Quick Reference: Single Job Fetch Endpoint

## TL;DR

New endpoint: `/api/v1/fetch_job` (GET or POST)

**Search for ONE LinkedIn job by URL or ID**

## Quick Start

### Fetch by Job ID (Simplest)
```bash
curl -X GET 'http://localhost:8000/api/v1/fetch_job?job_id=123456789' \
  -H 'x-api-key: YOUR_API_KEY'
```

### Fetch by Full URL
```bash
curl -X GET 'http://localhost:8000/api/v1/fetch_job?job_url=https://www.linkedin.com/jobs/view/123456789' \
  -H 'x-api-key: YOUR_API_KEY'
```

### POST Method
```bash
curl -X POST 'http://localhost:8000/api/v1/fetch_job' \
  -H 'x-api-key: YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "job_id": "123456789",
    "fetch_description": true,
    "description_format": "markdown"
  }'
```

## Success Response
```json
{
  "success": true,
  "job": {
    "TITLE": "Software Engineer",
    "COMPANY": "Example Corp",
    "LOCATION": "San Francisco, CA",
    "SALARY_CURRENCY": "USD",
    "MIN_AMOUNT": 150000,
    "MAX_AMOUNT": 200000,
    "DESCRIPTION": "Full job description...",
    // ... many more fields
  },
  "cached": false
}
```

## Error Response
```json
{
  "success": false,
  "error": "Error message",
  "suggestion": "What to do about it"
}
```

## Parameters

| Param | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| job_url | string | No* | - | Full LinkedIn URL |
| job_id | string | No* | - | Job ID number only |
| fetch_description | bool | No | true | Get full job description |
| description_format | string | No | markdown | Format: `markdown` or `html` |
| verbose | int | No | 2 | Log level: 0=errors, 1=warnings, 2=all |

*Either `job_url` or `job_id` required

## Common Use Cases

### 1. Get Job Details for Display
```bash
curl 'http://localhost:8000/api/v1/fetch_job?job_id=123456789&fetch_description=true'
```

### 2. Get Job Without Full Description (Faster)
```bash
curl 'http://localhost:8000/api/v1/fetch_job?job_id=123456789&fetch_description=false'
```

### 3. Get HTML Formatted Description
```bash
curl 'http://localhost:8000/api/v1/fetch_job?job_id=123456789&description_format=html'
```

### 4. Quiet Mode (Fewer Logs)
```bash
curl 'http://localhost:8000/api/v1/fetch_job?job_id=123456789&verbose=0'
```

## Python Example
```python
import requests

response = requests.get(
    'http://localhost:8000/api/v1/fetch_job',
    params={'job_id': '123456789'},
    headers={'x-api-key': 'YOUR_API_KEY'}
)

if response.status_code == 200:
    data = response.json()
    if data['success']:
        job = data['job']
        print(f"{job['TITLE']} at {job['COMPANY']}")
        print(f"${job['MIN_AMOUNT']:,} - ${job['MAX_AMOUNT']:,}")
```

## JavaScript Example
```javascript
const response = await fetch('http://localhost:8000/api/v1/fetch_job?job_id=123456789', {
  headers: {'x-api-key': 'YOUR_API_KEY'}
});

const data = await response.json();
if (data.success) {
  console.log(`${data.job.TITLE} at ${data.job.COMPANY}`);
}
```

## Difference from /search_jobs

| Feature | /search_jobs | /fetch_job |
|---------|---|---|
| Find by keywords | ✓ | ✗ |
| Get single job | ✗ | ✓ |
| Need job ID/URL | ✗ | ✓ |
| Returns list | ✓ | ✗ (single) |
| Pagination | ✓ | ✗ |
| Response format | Same | Same |

## Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Job found and returned |
| 400 | Bad request | Missing job_id and job_url |
| 404 | Not found | Job doesn't exist |
| 500 | Server error | Network/scraping issue |

## Tips & Tricks

1. **Faster Response**: Set `fetch_description=false` if you don't need full description
2. **Caching**: Same request returns cached result (check `cached` field)
3. **Job ID from URL**: Just extract the number from LinkedIn URL: `linkedin.com/jobs/view/[THIS_NUMBER]`
4. **Error Handling**: Check `success` field before accessing `job`
5. **Debugging**: Use `verbose=2` to see all logs if something's wrong

## Endpoints Registered

✅ `GET /api/v1/fetch_job` - Query parameter version
✅ `POST /api/v1/fetch_job` - JSON body version

Both work identically, choose based on preference.

## Implementation Files

- **Models**: `app/models/job_models.py` (SingleJobRequest, SingleJobResponse)
- **Service**: `app/services/job_service.py` (fetch_single_job method)
- **Routes**: `app/routes/api.py` (GET and POST endpoints)
- **Docs**: `FETCH_JOB_ENDPOINT.md` (Full documentation)
- **Examples**: `examples/api_usage.py` (Code examples)
