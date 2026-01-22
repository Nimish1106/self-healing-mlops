#!/bin/bash
# Verify that the project is set up correctly

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "================================"
echo "Setup Verification"
echo "================================"
echo ""

error_count=0

# Check directories
echo "Checking directories..."
for dir in data models monitoring mlflow; do
    if [ -d "$dir" ]; then
        echo -e "  $dir: ${GREEN}✓${NC}"
    else
        echo -e "  $dir: ${RED}✗ Missing${NC}"
        ((error_count++))
    fi
done
echo ""

# Check dataset
echo "Checking dataset..."
if [ -f "data/cs-training.csv" ]; then
    echo -e "  cs-training.csv: ${GREEN}✓${NC}"
else
    echo -e "  cs-training.csv: ${RED}✗ Missing${NC}"
    echo -e "  ${YELLOW}Download from: https://www.kaggle.com/c/GiveMeSomeCredit/data${NC}"
    ((error_count++))
fi
echo ""

# Check Docker
echo "Checking Docker..."
if command -v docker &> /dev/null; then
    echo -e "  Docker: ${GREEN}✓${NC} ($(docker --version))"
else
    echo -e "  Docker: ${RED}✗ Not installed${NC}"
    ((error_count++))
fi

if command -v docker-compose &> /dev/null; then
    echo -e "  Docker Compose: ${GREEN}✓${NC} ($(docker-compose --version))"
else
    echo -e "  Docker Compose: ${RED}✗ Not installed${NC}"
    ((error_count++))
fi
echo ""

# Check Python
echo "Checking Python..."
if command -v python &> /dev/null; then
    echo -e "  Python: ${GREEN}✓${NC} ($(python --version))"
else
    echo -e "  Python: ${RED}✗ Not installed${NC}"
    ((error_count++))
fi
echo ""

# Summary
echo "================================"
if [ $error_count -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. make bootstrap  # Create reference data"
    echo "  2. make train      # Train initial model"
    echo "  3. make start      # Start all services"
else
    echo -e "${RED}✗ ${error_count} checks failed${NC}"
    echo ""
    echo "Fix the issues above and run again."
fi
echo "================================"

exit $error_count
