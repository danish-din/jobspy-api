# 🚀 Complete Manual Build & Test Instructions

Since Docker is not available in this terminal environment, follow these steps on your local machine.

## Prerequisites Check

Before starting, verify you have everything:

```bash
# Check Docker is installed
docker --version
# Expected: Docker version 20.10+

# Check Docker Compose is installed
docker-compose --version
# Expected: docker-compose version 1.29+

# Check Python is installed
python --version
# Expected: Python 3.7+

# Check Git is installed
git --version
# Expected: git version 2.30+
```

If any are missing, install them first.

---

## Step-by-Step Instructions

### Step 1: Navigate to Project Directory

```bash
cd c:\Users\danis\Documents\Github\jobspy-api
```

### Step 2: Verify Docker Installation

```bash
docker ps
# Should show "CONTAINER ID  IMAGE  COMMAND  CREATED  STATUS  PORTS  NAMES"
# with no errors
```

### Step 3: Build the Docker Image

This will create a Docker image from the Dockerfile (~5-10 minutes).

```bash
docker-compose build
```

**What happens:**
- Pulls Python 3.13 slim base image
- Installs system dependencies
- Installs Python packages (jobspy, fastapi, etc.)
- Copies application code
- Prepares the image for running

**Expected output:**
```
Building jobspy-api
Step 1/20 : FROM python:3.13-slim
...
Step 20/20 : CMD ["/bin/bash", "-c", "/app/scripts/confirm_env.sh && uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers"]
...
Successfully built abc123def456
Successfully tagged jobspy-docker-api:latest
```

### Step 4: Clean Up Old Containers (Optional)

```bash
# Stop any running containers
docker-compose down

# Or force remove
docker-compose down --remove-orphans
```

### Step 5: Start the Container

This starts the container in the background.

```bash
docker-compose up -d
```

**Expected output:**
```
Creating network "jobspy-api_default" with the default driver
Creating jobspy-docker-api ... done
```

### Step 6: Wait for Container to Start

Wait about 10-15 seconds for the container to initialize.

```bash
# Check status
docker-compose ps

# Expected output:
# NAME              IMAGE                      STATUS
# jobspy-docker-api jobspy-docker-api:latest   Up (health: starting)
```

Wait until status shows `Up (health: healthy)`.

### Step 7: Verify Container is Running

```bash
# Test health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy"}
```

### Step 8: Run the Test Suite

This will run comprehensive tests on the new endpoint.

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

... (more tests) ...

════════════════════════════════════════════════════════════════════
Test Summary
════════════════════════════════════════════════════════════════════
✓ PASS: Health Check
✓ PASS: Endpoint Exists
... (more results) ...

Total: 8/8 tests passed

🎉 All tests passed!
```

### Step 9: Access the API Documentation

Open in your browser:

```
http://localhost:8000/docs
```

You should see:
- Swagger UI with all endpoints
- The new `/api/v1/fetch_job` endpoint listed
- Full documentation for the new endpoint
- Ability to test endpoints directly in the browser

---

## Manual Testing (Without Test Script)

If you want to test manually using curl:

### Test 1: Missing Parameters (Should Error)

```bash
curl http://localhost:8000/api/v1/fetch_job

# Expected: 400 Bad Request with error message
```

### Test 2: Fetch by Job ID

```bash
curl "http://localhost:8000/api/v1/fetch_job?job_id=3456789&fetch_description=true"

# Expected: 200 OK with job data, or 404 if job doesn't exist
```

### Test 3: Fetch by URL

```bash
curl "http://localhost:8000/api/v1/fetch_job?job_url=https://www.linkedin.com/jobs/view/3456789"

# Expected: 200 OK with job data, or 404 if job doesn't exist
```

### Test 4: POST Request

```bash
curl -X POST "http://localhost:8000/api/v1/fetch_job" \
  -H "Content-Type: application/json" \
  -d '{"job_id":"3456789","fetch_description":true}'

# Expected: 200 OK with job data, or 404 if job doesn't exist
```

### Test 5: Health Check

```bash
curl http://localhost:8000/health

# Expected: {"status":"healthy"}
```

---

## View Logs

To see what's happening in the container:

```bash
# Real-time logs
docker-compose logs -f jobspy-api

# Last 50 lines
docker-compose logs --tail=50 jobspy-api

# Stop log streaming: Press Ctrl+C
```

---

## Troubleshooting

### Issue: docker: command not found

**Solution:** Docker is not installed or not in PATH
- Install Docker from https://www.docker.com/products/docker-desktop
- Make sure Docker Desktop is running
- Restart your terminal

### Issue: Cannot connect to Docker daemon

**Solution:** Docker daemon is not running
- Windows: Start Docker Desktop application
- Mac: Start Docker Desktop application  
- Linux: `sudo systemctl start docker`

### Issue: Port 8000 already in use

**Solution:** Kill the process using port 8000
```bash
# Windows (PowerShell as Admin)
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>
```

### Issue: Container fails to start

**Solution:** Check logs for errors
```bash
docker-compose logs jobspy-api
```

Then refer to DOCKER_DEPLOY_GUIDE.md for troubleshooting.

### Issue: Test script not found

**Solution:** Make sure you're in the correct directory
```bash
cd c:\Users\danis\Documents\Github\jobspy-api
python test_fetch_job.py
```

### Issue: Python requests module not found

**Solution:** Install it
```bash
pip install requests
```

---

## Stop & Cleanup

When you're done testing:

```bash
# Stop the container
docker-compose down

# Remove all containers and volumes
docker-compose down -v

# Remove the image
docker rmi jobspy-api:latest jobspy-docker-api:latest

# Clean up everything
docker system prune -a
```

---

## What Should Happen

### After `docker-compose build`:
✅ Image created successfully  
✅ All dependencies installed  
✅ No errors in build output  

### After `docker-compose up -d`:
✅ Container started in background  
✅ No error messages  
✅ Status shows "Up (healthy)"  

### After `python test_fetch_job.py`:
✅ All 8 tests pass  
✅ No connection errors  
✅ Endpoint responds correctly  

### After opening http://localhost:8000/docs:
✅ Swagger UI loads  
✅ All endpoints visible  
✅ New `/api/v1/fetch_job` endpoint listed with documentation  

---

## File Locations

Make sure these files exist in your project:

```
c:\Users\danis\Documents\Github\jobspy-api\
├── Dockerfile                    ✅
├── docker-compose.yml           ✅
├── .env                         (Create if needed)
├── test_fetch_job.py            ✅ NEW
├── start-docker.ps1             ✅ NEW
├── start-docker.sh              ✅ NEW
├── app/
│   ├── main.py
│   ├── routes/api.py           ✅ UPDATED
│   ├── services/job_service.py ✅ UPDATED
│   └── models/job_models.py    ✅ UPDATED
└── requirements.txt
```

---

## Quick Command Summary

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
python test_fetch_job.py

# Stop
docker-compose down

# Test endpoint manually
curl "http://localhost:8000/api/v1/fetch_job?job_id=3456789"

# View API docs
# Open: http://localhost:8000/docs
```

---

## Expected Timeline

| Step | Time | Action |
|------|------|--------|
| Build | 5-10 min | `docker-compose build` |
| Start | <1 min | `docker-compose up -d` |
| Wait | 10-15 sec | Container initialization |
| Test | 1-2 min | `python test_fetch_job.py` |
| **Total** | **6-13 min** | **Complete setup** |

---

## Success Indicators

✅ **Build succeeded** - No error messages  
✅ **Container running** - `docker-compose ps` shows "Up"  
✅ **Health check passes** - `curl http://localhost:8000/health` returns 200  
✅ **Tests pass** - `python test_fetch_job.py` shows 8/8 passed  
✅ **API docs load** - Browser shows Swagger UI at `/docs`  
✅ **New endpoint visible** - Swagger UI lists `/api/v1/fetch_job`  

---

## Next Steps After Success

1. **Explore the API** - Open http://localhost:8000/docs
2. **Try the endpoint** - Use Swagger UI or curl to test
3. **Configure settings** - Edit `.env` for production setup
4. **Review documentation** - Check DOCKER_DEPLOY_GUIDE.md
5. **Deploy to server** - Follow production deployment steps

---

## Additional Resources

- **Docker Docs**: https://docs.docker.com/
- **Docker Compose Docs**: https://docs.docker.com/compose/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **JobSpy Library**: https://github.com/cullenwatson/JobSpy

---

## Contact & Support

If you encounter issues:

1. Check the logs: `docker-compose logs jobspy-api`
2. Read troubleshooting: DOCKER_DEPLOY_GUIDE.md
3. Review Dockerfile: `cat Dockerfile`
4. Check docker-compose.yml: `cat docker-compose.yml`
5. Verify files exist: `ls -la` (Linux/Mac) or `dir` (Windows)

---

**You're all set! Follow the steps above and your Docker container will be built, running, and fully tested.** 🚀

Run this to get started:
```bash
docker-compose build && docker-compose up -d && sleep 15 && python test_fetch_job.py
```
