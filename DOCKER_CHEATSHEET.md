# 🐳 Docker Quick Commands Cheat Sheet

## Build & Start

```bash
# Build image
docker-compose build

# Start container
docker-compose up -d

# Build and start
docker-compose up -d --build

# Start in foreground (useful for debugging)
docker-compose up
```

## Status & Monitoring

```bash
# Check container status
docker-compose ps

# View logs (last 50 lines)
docker-compose logs --tail=50 jobspy-api

# Follow logs in real-time
docker-compose logs -f jobspy-api

# Monitor resource usage
docker stats jobspy-docker-api

# Inspect container details
docker inspect jobspy-docker-api
```

## Testing

```bash
# Run comprehensive test suite
python test_fetch_job.py

# Test health endpoint
curl http://localhost:8000/health

# Test new fetch_job endpoint (GET)
curl "http://localhost:8000/api/v1/fetch_job?job_id=3456789"

# Test with full URL
curl "http://localhost:8000/api/v1/fetch_job?job_url=https://www.linkedin.com/jobs/view/3456789"

# Test with POST
curl -X POST "http://localhost:8000/api/v1/fetch_job" \
  -H "Content-Type: application/json" \
  -d '{"job_id":"3456789"}'

# Access API documentation
open http://localhost:8000/docs  # macOS
start http://localhost:8000/docs  # Windows
xdg-open http://localhost:8000/docs  # Linux
```

## Container Management

```bash
# Stop container (can be restarted)
docker-compose stop

# Stop and remove container
docker-compose down

# Restart container
docker-compose restart jobspy-api

# Remove everything including images
docker-compose down --rmi all

# Execute command in container
docker-compose exec jobspy-api bash

# Run Python in container
docker-compose exec jobspy-api python --version

# Install package in container
docker-compose exec jobspy-api pip install package-name
```

## Cleanup

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Clean everything unused
docker system prune -a

# Remove specific image
docker rmi jobspy-api:latest
```

## Environment & Configuration

```bash
# View environment variables
docker-compose exec jobspy-api env

# Check specific variable
docker-compose exec jobspy-api echo $LOG_LEVEL

# View .env file
cat .env

# Edit environment and restart
# 1. Edit .env
# 2. docker-compose restart jobspy-api
```

## Networking

```bash
# List networks
docker network ls

# Inspect network
docker network inspect jobspy-api_default

# View container IP
docker-compose exec jobspy-api hostname -I

# Port mapping info
docker-compose ps
```

## Logs & Debugging

```bash
# Show all logs with timestamps
docker-compose logs --timestamps jobspy-api

# Show logs since 5 minutes ago
docker-compose logs --since 5m jobspy-api

# Show only error logs
docker-compose logs jobspy-api 2>&1 | grep -i error

# Export logs to file
docker-compose logs jobspy-api > logs.txt

# Watch logs in real-time
watch -n 1 "docker-compose logs --tail=20 jobspy-api"
```

## Performance

```bash
# Check resource limits
docker stats --no-stream jobspy-docker-api

# Continuous monitoring
docker stats jobspy-docker-api

# Check disk usage
docker system df
```

## Troubleshooting

```bash
# Check if port is in use
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000

# Kill process on port
# Windows
taskkill /PID <PID> /F

# Linux/Mac
kill -9 <PID>

# Rebuild without cache (if having issues)
docker-compose build --no-cache

# Full restart
docker-compose down && docker-compose up -d --build

# Check Docker daemon status
docker info

# Verify Docker installation
docker --version && docker-compose --version
```

## Health Checks

```bash
# Health endpoint
curl http://localhost:8000/health

# Swagger UI (API docs)
curl http://localhost:8000/docs

# OpenAPI spec
curl http://localhost:8000/openapi.json

# Verify endpoint is working
curl -w "\nStatus: %{http_code}\n" \
  "http://localhost:8000/api/v1/fetch_job?job_id=test"
```

## Common Workflows

### Fresh Start
```bash
docker-compose down -v  # Remove everything
docker-compose up -d --build  # Fresh build and start
docker-compose logs -f  # Watch logs
```

### Quick Restart
```bash
docker-compose restart jobspy-api
```

### Update Code & Restart
```bash
docker-compose down
docker-compose up -d --build
```

### Debug a Problem
```bash
docker-compose logs -f jobspy-api  # Watch logs
docker-compose exec jobspy-api bash  # Enter container
# Check files, run commands
exit  # Leave container
```

### Load Test
```bash
# Install apache bench: apt-get install apache2-utils
ab -n 100 -c 10 http://localhost:8000/health
```

### Production Deploy
```bash
# Build with version tag
docker build -t myregistry/jobspy-api:1.0.0 .

# Push to registry
docker push myregistry/jobspy-api:1.0.0

# Pull and run on production server
docker pull myregistry/jobspy-api:1.0.0
docker run -d -p 8000:8000 myregistry/jobspy-api:1.0.0
```

## Windows PowerShell Specific

```powershell
# Enable script execution (first time only)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run startup script
.\start-docker.ps1

# Run tests
python test_fetch_job.py

# View logs with color
docker-compose logs -f jobspy-api | Select-String "ERROR" -Highlight

# PowerShell equivalent of watch
while($true) { Clear-Host; docker-compose logs --tail=20 jobspy-api; Start-Sleep 2 }
```

## macOS Specific

```bash
# Start Docker daemon if not running
open /Applications/Docker.app

# Kill all containers
docker-compose down

# Clean up disk space
docker system prune -a

# View containers in Docker Desktop
# Menu Bar > Whale Icon > Containers
```

## Linux Specific

```bash
# Start Docker daemon
sudo systemctl start docker

# Enable on boot
sudo systemctl enable docker

# User permissions (avoid sudo)
sudo usermod -aG docker $USER

# Run as sudo if needed
sudo docker-compose ps

# View logs with journalctl
journalctl -u docker.service -f
```

## Environment Variables

```bash
# Set for single command
ENABLE_API_KEY_AUTH=false docker-compose up

# Set in .env file
ENABLE_API_KEY_AUTH=false
LOG_LEVEL=INFO
ENABLE_CACHE=true

# Export and use
export LOG_LEVEL=DEBUG
docker-compose up
```

## Docker Compose Overrides

```bash
# Use alternate compose file
docker-compose -f docker-compose.prod.yml up

# Multiple compose files
docker-compose -f docker-compose.yml -f docker-compose.override.yml up

# Set project name
docker-compose -p myproject up
```

## Quick Links

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health**: http://localhost:8000/health
- **Fetch Job**: http://localhost:8000/api/v1/fetch_job?job_id=123456789

## Need Help?

```bash
# View docker-compose help
docker-compose --help

# View specific command help
docker-compose up --help

# Check documentation
docker docs

# View application logs
docker-compose logs jobspy-api

# Run test suite
python test_fetch_job.py
```

---

**Last Updated**: March 3, 2026  
**For More Info**: See DOCKER_DEPLOY_GUIDE.md
