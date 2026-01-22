#!/bin/bash
# Comprehensive health check for the system

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "================================"
echo "System Health Check"
echo "================================"
echo ""

# Function to check service
check_service() {
    local name=$1
    local url=$2

    echo -n "Checking $name... "
    if curl -sf "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

# Check Docker
echo "Docker Services:"
docker-compose ps
echo ""

# Check MLflow
echo "API Services:"
check_service "MLflow   " "http://localhost:5000/health"
check_service "FastAPI  " "http://localhost:8000/health"
echo ""

# Check data
echo "Data Status:"
if [ -f "monitoring/reference/reference_data.csv" ]; then
    echo -e "Reference data: ${GREEN}✓${NC}"
else
    echo -e "Reference data: ${RED}✗ Missing${NC}"
fi

if [ -f "monitoring/predictions/predictions.csv" ]; then
    pred_count=$(wc -l < monitoring/predictions/predictions.csv)
    echo -e "Predictions: ${GREEN}$pred_count lines${NC}"
else
    echo -e "Predictions: ${YELLOW}No data yet${NC}"
fi
echo ""

# Check model
echo "Model Status:"
response=$(curl -s http://localhost:8000/model/info 2>/dev/null)
if [ $? -eq 0 ]; then
    version=$(echo $response | jq -r '.model_version')
    echo -e "Model version: ${GREEN}$version${NC}"
else
    echo -e "${RED}Model not loaded${NC}"
fi
echo ""

# Summary
echo "================================"
echo "Health check complete"
echo "================================"
