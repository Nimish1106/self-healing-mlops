#!/bin/bash

echo "Migrating to corrected schema..."

# Drop old database
docker-compose exec postgres-mlops psql -U mlops -d mlops -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Recreate with corrected schema
docker-compose exec api python scripts/db/init_database.py

echo "✅ Migration complete. Corrected schema deployed."