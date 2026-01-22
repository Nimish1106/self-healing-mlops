#!/bin/bash
# Generate test predictions for the API
# Usage: ./generate_test_predictions.sh [count]

set -e

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
COUNT="${1:-250}"
SAMPLE_FILE="tests/fixtures/sample_input.json"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Generating ${COUNT} test predictions...${NC}"

# Check if API is available
if ! curl -sf "${API_URL}/health" > /dev/null; then
    echo -e "${RED}Error: API not available at ${API_URL}${NC}"
    echo "Start the API with: make start"
    exit 1
fi

# Sample input data
SAMPLE_INPUT='{
  "RevolvingUtilizationOfUnsecuredLines": 0.766127,
  "age": 45,
  "NumberOfTime30_59DaysPastDueNotWorse": 2,
  "DebtRatio": 0.802982,
  "MonthlyIncome": 9120.0,
  "NumberOfOpenCreditLinesAndLoans": 13,
  "NumberOfTimes90DaysLate": 0,
  "NumberRealEstateLoansOrLines": 6,
  "NumberOfTime60_89DaysPastDueNotWorse": 0,
  "NumberOfDependents": 2
}'

# Generate predictions
success_count=0
fail_count=0

for i in $(seq 1 $COUNT); do
    # Add some randomness to the data
    age=$((25 + RANDOM % 50))
    income=$((5000 + RANDOM % 15000))

    # Create modified input
    modified_input=$(echo $SAMPLE_INPUT | \
        jq ".age = $age | .MonthlyIncome = $income")

    # Make prediction
    response=$(curl -s -X POST "${API_URL}/predict" \
        -H "Content-Type: application/json" \
        -d "$modified_input")

    if echo "$response" | jq -e '.prediction' > /dev/null 2>&1; then
        ((success_count++))
        # Progress indicator
        if [ $((i % 50)) -eq 0 ]; then
            echo -e "${GREEN}Progress: $i/${COUNT}${NC}"
        fi
    else
        ((fail_count++))
        echo -e "${RED}Failed at $i: $response${NC}"
    fi

    # Small delay to avoid overwhelming the API
    sleep 0.05
done

echo ""
echo -e "${GREEN}✓ Generation complete${NC}"
echo -e "  Success: ${GREEN}${success_count}${NC}"
echo -e "  Failed:  ${RED}${fail_count}${NC}"
echo ""
echo "Verify with: curl http://localhost:8000/monitoring/stats | jq"
