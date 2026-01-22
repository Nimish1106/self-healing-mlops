#!/bin/bash
# Inject different types of drift for testing
# Usage: ./inject_drift.sh [drift_type] [count]
# Types: covariate, population, concept

set -e

DRIFT_TYPE="${1:-covariate}"
API_URL="${API_URL:-http://localhost:8000}"
COUNT="${2:-100}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}Injecting ${DRIFT_TYPE} drift (${COUNT} samples)...${NC}"

case $DRIFT_TYPE in
    covariate)
        echo "Covariate drift: Increasing income by 50%"
        for i in $(seq 1 $COUNT); do
            income=$((10000 + RANDOM % 10000))  # Higher income range
            age=$((40 + RANDOM % 30))           # Older population

            curl -s -X POST "${API_URL}/predict" \
                -H "Content-Type: application/json" \
                -d "{
                    \"RevolvingUtilizationOfUnsecuredLines\": 0.5,
                    \"age\": $age,
                    \"NumberOfTime30_59DaysPastDueNotWorse\": 1,
                    \"DebtRatio\": 0.6,
                    \"MonthlyIncome\": $income,
                    \"NumberOfOpenCreditLinesAndLoans\": 10,
                    \"NumberOfTimes90DaysLate\": 0,
                    \"NumberRealEstateLoansOrLines\": 5,
                    \"NumberOfTime60_89DaysPastDueNotWorse\": 0,
                    \"NumberOfDependents\": 1
                }" > /dev/null

            if [ $((i % 25)) -eq 0 ]; then
                echo -e "${GREEN}Progress: $i/${COUNT}${NC}"
            fi
            sleep 0.05
        done
        ;;

    population)
        echo "Population drift: Changing class balance"
        # Generate more high-risk profiles
        for i in $(seq 1 $COUNT); do
            curl -s -X POST "${API_URL}/predict" \
                -H "Content-Type: application/json" \
                -d '{
                    "RevolvingUtilizationOfUnsecuredLines": 0.95,
                    "age": 25,
                    "NumberOfTime30_59DaysPastDueNotWorse": 5,
                    "DebtRatio": 1.5,
                    "MonthlyIncome": 2000.0,
                    "NumberOfOpenCreditLinesAndLoans": 3,
                    "NumberOfTimes90DaysLate": 2,
                    "NumberRealEstateLoansOrLines": 0,
                    "NumberOfTime60_89DaysPastDueNotWorse": 3,
                    "NumberOfDependents": 3
                }' > /dev/null

            if [ $((i % 25)) -eq 0 ]; then
                echo -e "${GREEN}Progress: $i/${COUNT}${NC}"
            fi
            sleep 0.05
        done
        ;;

    concept)
        echo "Concept drift: Cannot be simulated with features only"
        echo "This would require changing the underlying Y relationship"
        echo "Skipping..."
        exit 0
        ;;

    *)
        echo -e "${RED}Unknown drift type: $DRIFT_TYPE${NC}"
        echo "Available types: covariate, population, concept"
        exit 1
        ;;
esac

echo -e "${GREEN}✓ Drift injection complete${NC}"
echo "Wait for next monitoring cycle to see drift detected"
