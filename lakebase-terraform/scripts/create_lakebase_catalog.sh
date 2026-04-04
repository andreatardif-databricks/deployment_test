#!/usr/bin/env bash
set -euo pipefail

# Creates a Lakebase Postgres catalog linked to an Autoscaling project.
# Usage: ./create_lakebase_catalog.sh <workspace_url> <catalog_name> <project_name> <branch> <database> <profile>
# Delete: ./create_lakebase_catalog.sh --delete <workspace_url> <catalog_name> <profile>

if [ "${1:-}" = "--delete" ]; then
    WORKSPACE_URL="$2"
    CATALOG_NAME="$3"
    PROFILE="$4"

    TOKEN=$(databricks auth token --profile "$PROFILE" --host "$WORKSPACE_URL" 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

    echo "Deleting catalog: $CATALOG_NAME"
    curl -s -X DELETE \
        "${WORKSPACE_URL}/api/2.1/unity-catalog/catalogs/${CATALOG_NAME}?force=true" \
        -H "Authorization: Bearer $TOKEN" | python3 -m json.tool || true
    exit 0
fi

WORKSPACE_URL="$1"
CATALOG_NAME="$2"
PROJECT_NAME="$3"
BRANCH="$4"
DATABASE="$5"
PROFILE="$6"

TOKEN=$(databricks auth token --profile "$PROFILE" --host "$WORKSPACE_URL" 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo "Creating Lakebase Postgres catalog: $CATALOG_NAME"
echo "  Project: $PROJECT_NAME, Branch: $BRANCH, Database: $DATABASE"

RESPONSE=$(curl -s -X POST \
    "${WORKSPACE_URL}/api/2.1/unity-catalog/catalogs" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"name\": \"${CATALOG_NAME}\",
        \"catalog_type\": \"LAKEBASE_CATALOG\",
        \"options\": {
            \"database_type\": \"AUTOSCALING\",
            \"project\": \"${PROJECT_NAME}\",
            \"branch\": \"${BRANCH}\",
            \"database\": \"${DATABASE}\"
        }
    }")

echo "$RESPONSE" | python3 -m json.tool
echo "Catalog created successfully."
