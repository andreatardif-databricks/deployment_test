#!/usr/bin/env bash
set -euo pipefail

# Manages Lakebase project ACLs and Postgres role grants.
# Usage: ./manage_lakebase_perms.sh <workspace_url> <project_name> <sp_app_id> <user_email> <group_name> <profile>

WORKSPACE_URL="$1"
PROJECT_NAME="$2"
SP_APP_ID="$3"
USER_EMAIL="$4"
GROUP_NAME="$5"
PROFILE="$6"

TOKEN=$(databricks auth token --profile "$PROFILE" --host "$WORKSPACE_URL" 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo "=== Setting Lakebase Project Permissions ==="

# Set CAN_MANAGE for SP and user, CAN_USE for group
# Using workspace object permissions API
echo "Setting project ACLs..."
curl -s -X PUT \
    "${WORKSPACE_URL}/api/2.0/permissions/postgres-projects/${PROJECT_NAME}" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"access_control_list\": [
            {
                \"service_principal_name\": \"${SP_APP_ID}\",
                \"permission_level\": \"CAN_MANAGE\"
            },
            {
                \"user_name\": \"${USER_EMAIL}\",
                \"permission_level\": \"CAN_MANAGE\"
            },
            {
                \"group_name\": \"${GROUP_NAME}\",
                \"permission_level\": \"CAN_USE\"
            }
        ]
    }" | python3 -m json.tool

echo
echo "=== Lakebase project permissions applied ==="
echo
echo "NOTE: Postgres database roles (databricks_superuser membership) must be"
echo "configured via SQL after connecting to the Lakebase endpoint."
echo "The project creator automatically inherits databricks_superuser."
echo "For the lakebase-users group on the dev branch, run:"
echo "  GRANT databricks_superuser TO <role_name>;"
