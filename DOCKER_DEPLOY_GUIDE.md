# 🚀 Docker Build, Deploy & Test Guide

## Quick Start (TL;DR)

### Windows (PowerShell)
```powershell
# Make script executable (first time only)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Build and start
.\start-docker.ps1

# Test in another terminal
python test_fetch_job.py
```

### Linux/Mac (Bash)
```bash
# Build and start
chmod +x start-docker.sh
./start-docker.sh

# Test in another terminal
python test_fetch_job.py
```

### Manual Docker Commands
```bash
# Build
docker-compose build

# Start
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f jobspy-api

# Test
curl "http://localhost:8000/api/v1/fetch_job?job_id=3456789"

# Stop
docker-compose down
```

---

## Detailed Step-by-Step Guide

### Prerequisites

✅ Docker installed and running  
✅ Docker Compose installed  
✅ Python 3.7+ (for test script)  
✅ requests library: `pip install requests`

### Step 1: Build Docker Image

The Dockerfile will:
- Use Python 3.13 slim image
- Install system dependencies
- Install Python packages from requirements.txt
- Copy application code
- Expose port 8000
- Configure health checks

```bash
# Build the image
docker-compose build

# Or rebuild without cache
docker-compose build --no-cache
```

**Expected output:**
```
Building jobspy-api
Step 1/20 : FROM python:3.13-slim
...
Successfully built abc123def456
Successfully tagged jobspy-docker-api:latest
```

### Step 2: Start the Container

```bash
# Start in background
docker-compose up -d

# Or start in foreground (useful for debugging)
docker-compose up
```

**Check if running:**
```bash
docker-compose ps

# Expected output:
# NAME              COMMAND                  STATUS
# jobspy-docker-api "uvicorn app.main..."   Up (healthy)
```

### Step 3: Verify Container Health

```bash
# Health check endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy"}
```

### Step 4: Test the New Fetch Job Endpoint

#### Option A: Using cURL (Quick Test)

```bash
# Test 1: Invalid parameters (should return 400)
curl -X GET "http://localhost:8000/api/v1/fetch_job"

# Test 2: Fetch with job ID
curl -X GET "http://localhost:8000/api/v1/fetch_job?job_id=3456789&fetch_description=true"

# Test 3: Fetch with URL
curl -X GET "http://localhost:8000/api/v1/fetch_job?job_url=https://www.linkedin.com/jobs/view/3456789"

# Test 4: POST method
curl -X POST "http://localhost:8000/api/v1/fetch_job" \
  -H "Content-Type: application/json" \
  -d '{"job_id":"3456789","fetch_description":true}'

# Test 5: Swagger UI
open http://localhost:8000/docs  # macOS
start http://localhost:8000/docs  # Windows
xdg-open http://localhost:8000/docs  # Linux
```

#### Option B: Using Python Test Script (Comprehensive)

```bash
python test_fetch_job.py
```

**Expected output:**
```
════════════════════════════════════════════════════════════════════
JobSpy API - Fetch Job Endpoint Test Suite
════════════════════════════════════════════════════════════════════

=== Health Check ===
✓ Health check passed: {'status': 'healthy'}

=== Endpoint Existence ===
✓ Endpoint responds with status 404

=== Error Handling - Missing Parameters ===
✓ Correctly returned 400 Bad Request
ℹ Error: Missing required parameter
ℹ Message: Either 'job_url' or 'job_id' must be provided
ℹ Suggestion: Provide either a full LinkedIn job URL or just the job ID number

... (more tests)

════════════════════════════════════════════════════════════════════
Test Summary
════════════════════════════════════════════════════════════════════
✓ PASS: Health Check
✓ PASS: Endpoint Exists
✓ PASS: Missing Parameters
✓ PASS: Invalid Format
... (more results)

Total: 8/8 tests passed

🎉 All tests passed!
```

---

## Configuration

### For Testing (Disable Auth)

Create `.env` file:
```env
ENABLE_API_KEY_AUTH=false
LOG_LEVEL=INFO
ENABLE_CACHE=true
CACHE_EXPIRY=3600
```

Then:
```bash
docker-compose down
docker-compose up -d
```

### For Production (Enable Auth)

```env
ENABLE_API_KEY_AUTH=true
API_KEYS=your-api-key-1,your-api-key-2
LOG_LEVEL=WARN
ENABLE_CACHE=true
CACHE_EXPIRY=7200
```

Include API key in requests:
```bash
curl -H "x-api-key: your-api-key-1" \
  "http://localhost:8000/api/v1/fetch_job?job_id=3456789"
```

### Other Useful Settings

```env
# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Cache
ENABLE_CACHE=true
CACHE_EXPIRY=3600  # seconds

# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_TIMEFRAME=3600

# API Documentation
ENABLE_SWAGGER_UI=true
ENABLE_REDOC=true

# CORS
CORS_ORIGINS=*  # or specify domain: http://example.com

# Proxies
DEFAULT_PROXIES=user:pass@proxy.com:8080

# Job defaults
DEFAULT_COUNTRY_INDEED=USA
DEFAULT_RESULTS_WANTED=20
DEFAULT_DISTANCE=50
```

---

## Monitoring & Debugging

### View Logs

```bash
# Last 50 lines
docker-compose logs --tail=50 jobspy-api

# Follow logs in real-time
docker-compose logs -f jobspy-api

# Show logs with timestamps
docker-compose logs --timestamps jobspy-api

# Show only errors
docker-compose logs jobspy-api | grep ERROR
```

### Monitor Resources

```bash
# CPU and memory usage
docker stats jobspy-docker-api

# Container details
docker inspect jobspy-docker-api

# Network info
docker network ls
```

### Execute Commands in Container

```bash
# Get shell access
docker-compose exec jobspy-api bash

# Run Python commands
docker-compose exec jobspy-api python -c "import sys; print(sys.version)"

# Check installed packages
docker-compose exec jobspy-api pip list
```

### Check API Status

```bash
# Health endpoint
curl http://localhost:8000/health

# API info (if available)
curl http://localhost:8000/

# Swagger spec
curl http://localhost:8000/openapi.json
```

---

## Troubleshooting

### Issue: Port 8000 Already in Use

**Solution 1:** Use a different port
```yaml
# In docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead
```

**Solution 2:** Kill the process using port 8000
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>
```

### Issue: Container Fails to Start

```bash
# Check logs for errors
docker-compose logs jobspy-api

# Rebuild without cache
docker-compose build --no-cache

# Start with verbose output
docker-compose up --verbose
```

### Issue: Slow Responses

Check if caching is enabled:
```env
ENABLE_CACHE=true
```

Monitor performance:
```bash
docker stats jobspy-docker-api
```

### Issue: "Cannot connect to Docker daemon"

```bash
# Start Docker daemon
# Windows: Start Docker Desktop
# Linux: sudo systemctl start docker
# Mac: open /Applications/Docker.app
```

### Issue: API Key Authentication Errors

```bash
# Check current auth setting
docker-compose exec jobspy-api echo $ENABLE_API_KEY_AUTH

# If auth enabled, include API key
curl -H "x-api-key: your-key" http://localhost:8000/api/v1/fetch_job?job_id=123

# Or disable for testing
# Edit .env: ENABLE_API_KEY_AUTH=false
# Restart: docker-compose restart
```

---

## Performance Testing

### Load Testing

```bash
# Install apache bench
# Ubuntu/Debian: sudo apt-get install apache2-utils
# macOS: brew install httpd

# Simple load test (100 requests, 10 concurrent)
ab -n 100 -c 10 http://localhost:8000/health

# Load test with data
ab -n 100 -c 10 \
  -H "Content-Type: application/json" \
  -d '{"job_id":"123"}' \
  -p data.json \
  -T application/json \
  http://localhost:8000/api/v1/fetch_job
```

### Cache Effectiveness

```bash
# Request same job twice
time curl "http://localhost:8000/api/v1/fetch_job?job_id=123456789"
time curl "http://localhost:8000/api/v1/fetch_job?job_id=123456789"

# Second request should be much faster (cached)
```

---

## Cleanup

### Stop Container

```bash
# Stop (can be restarted)
docker-compose stop

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Stop and remove everything including images
docker-compose down --rmi all
```

### Clean Up Docker System

```bash
# Remove unused containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Clean everything
docker system prune -a
```

---

## Production Deployment

### Docker Hub Push

```bash
# Login to Docker Hub
docker login

# Tag image
docker tag jobspy-docker-api:latest username/jobspy-api:1.0.0
docker tag jobspy-docker-api:latest username/jobspy-api:latest

# Push
docker push username/jobspy-api:1.0.0
docker push username/jobspy-api:latest
```

### Environment Variables for Production

```env
# Security
ENABLE_API_KEY_AUTH=true
API_KEYS=your-production-key

# Performance
ENABLE_CACHE=true
CACHE_EXPIRY=7200
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_TIMEFRAME=3600

# Logging
LOG_LEVEL=INFO
ENVIRONMENT=production

# Documentation
ENABLE_SWAGGER_UI=false  # Hide in production
ENABLE_REDOC=false

# Proxies
DEFAULT_PROXIES=your-proxy:8080
CA_CERT_PATH=/app/certs/ca.pem
```

### Docker Compose for Production

```yaml
version: '3'
services:
  jobspy-api:
    image: your-registry/jobspy-api:1.0.0
    container_name: jobspy-api-prod
    restart: always  # Auto-restart on failure
    ports:
      - "8000:8000"
    environment:
      - ENABLE_API_KEY_AUTH=true
      - API_KEYS=${API_KEYS}
      - LOG_LEVEL=INFO
      - ENABLE_CACHE=true
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

---

## Scripts Provided

### 1. `start-docker.sh` (Linux/Mac)
Automated build and start script with logging and health checks.

```bash
chmod +x start-docker.sh
./start-docker.sh
```

### 2. `start-docker.ps1` (Windows PowerShell)
Automated build and start script with logging and health checks.

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\start-docker.ps1
```

### 3. `test_fetch_job.py` (Python)
Comprehensive test suite for the new endpoint.

```bash
python test_fetch_job.py
```

---

## Quick Reference Commands

```bash
# Build and start
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f jobspy-api

# Test health
curl http://localhost:8000/health

# Test endpoint
curl "http://localhost:8000/api/v1/fetch_job?job_id=123456789"

# Stop
docker-compose down

# Clean up
docker system prune -a

# Execute in container
docker-compose exec jobspy-api bash

# View resource usage
docker stats jobspy-docker-api
```

---

## Getting Help

**Logs:** `docker-compose logs jobspy-api`  
**Swagger UI:** http://localhost:8000/docs  
**Documentation:** See `FETCH_JOB_ENDPOINT.md`  
**Tests:** Run `python test_fetch_job.py`

---

## Next Steps

✅ Build Docker image  
✅ Start container  
✅ Run tests  
✅ Access Swagger UI at http://localhost:8000/docs  
✅ Integrate into your workflow  
✅ Deploy to production  

**Congratulations!** Your Docker container is ready to use! 🎉
