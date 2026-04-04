#!/usr/bin/env bash
set -euo pipefail

# Creates synced tables from Gold Delta tables to Lakebase Postgres.
# Usage: ./create_synced_tables.sh <workspace_url> <catalog> <lakebase_catalog> <project_uid> <branch_id> <profile>
# Delete: ./create_synced_tables.sh --delete <workspace_url> <lakebase_catalog> <profile>

GOLD_TABLES=("assessment_summary_by_classroom" "educator_performance_metrics" "school_performance_overview")

if [ "${1:-}" = "--delete" ]; then
    WORKSPACE_URL="$2"
    LAKEBASE_CATALOG="$3"
    PROFILE="$4"

    TOKEN=$(databricks auth token --profile "$PROFILE" --host "$WORKSPACE_URL" 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

    for table in "${GOLD_TABLES[@]}"; do
        echo "Deleting synced table: ${LAKEBASE_CATALOG}.public.${table}_synced"
        curl -s -X DELETE \
            "${WORKSPACE_URL}/api/2.0/database/synced_tables" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "{\"name\": \"${LAKEBASE_CATALOG}.public.${table}_synced\"}" || true
    done
    exit 0
fi

WORKSPACE_URL="$1"
CATALOG="$2"
LAKEBASE_CATALOG="$3"
PROJECT_UID="$4"
BRANCH_ID="$5"
PROFILE="$6"

TOKEN=$(databricks auth token --profile "$PROFILE" --host "$WORKSPACE_URL" 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

for table in "${GOLD_TABLES[@]}"; do
    echo "Creating synced table: ${LAKEBASE_CATALOG}.public.${table}_synced"
    echo "  Source: ${CATALOG}.gold.${table}"

    RESPONSE=$(curl -s -X POST \
        "${WORKSPACE_URL}/api/2.0/database/synced_tables" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"name\": \"${LAKEBASE_CATALOG}.public.${table}_synced\",
            \"database_project_id\": \"${PROJECT_UID}\",
            \"database_branch_id\": \"${BRANCH_ID}\",
            \"logical_database_name\": \"databricks_postgres\",
            \"spec\": {
                \"source_table\": \"${CATALOG}.gold.${table}\",
                \"sync_mode\": \"SNAPSHOT\"
            }
        }")

    echo "$RESPONSE" | python3 -m json.tool
    echo
done

echo "All synced tables created."
