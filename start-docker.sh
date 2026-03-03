#!/bin/bash
# Quick startup script for Docker container with optional testing

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          JobSpy API - Docker Build & Start Script                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════╝${NC}"

# Change to script directory
cd "$(dirname "$0")" || exit 1

# Step 1: Build image
echo -e "\n${BLUE}Step 1: Building Docker image...${NC}"
docker-compose build

# Step 2: Start container
echo -e "\n${BLUE}Step 2: Starting container...${NC}"
docker-compose down --remove-orphans 2>/dev/null || true
docker-compose up -d

# Step 3: Wait for container to be healthy
echo -e "\n${BLUE}Step 3: Waiting for container to be healthy...${NC}"
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker-compose exec -T jobspy-api curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Container is healthy${NC}"
        break
    fi
    echo -n "."
    sleep 1
    attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${YELLOW}⚠ Container may not be ready yet${NC}"
fi

# Step 4: Show container info
echo -e "\n${BLUE}Step 4: Container Status${NC}"
docker-compose ps

# Step 5: Show access information
echo -e "\n${BLUE}Step 5: Access Information${NC}"
echo -e "${GREEN}✓ API running at: http://localhost:8000${NC}"
echo -e "${GREEN}✓ Swagger UI at: http://localhost:8000/docs${NC}"
echo -e "${GREEN}✓ ReDoc at: http://localhost:8000/redoc${NC}"

# Step 6: Show logs
echo -e "\n${BLUE}Step 6: Container Logs${NC}"
docker-compose logs --tail=20 jobspy-api

# Step 7: Optional testing
echo -e "\n${BLUE}Step 7: Available Options${NC}"
echo -e "${GREEN}To run tests:${NC}"
echo "  python test_fetch_job.py"
echo ""
echo -e "${GREEN}To view logs:${NC}"
echo "  docker-compose logs -f jobspy-api"
echo ""
echo -e "${GREEN}To stop container:${NC}"
echo "  docker-compose down"
echo ""
echo -e "${GREEN}To test the new endpoint:${NC}"
echo '  curl "http://localhost:8000/api/v1/fetch_job?job_id=3456789"'
echo ""

echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    Ready to use!                                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════╝${NC}"
