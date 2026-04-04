# Lakebase Terraform Project

Deploys a complete Databricks environment with a Lakebase Autoscaling Postgres backend for a synthetic education domain (Teaching Strategies).

## Architecture

```
Account (0d26daa6-...)
└── Serverless Workspace (us-east-1)
    ├── Metastore: metastore_aws_us_east_1
    ├── Unity Catalog: teaching_strategies
    │   ├── bronze (raw CSVs → Delta)
    │   ├── silver (cleaned, deduped)
    │   └── gold (aggregated summaries)
    ├── SDP Pipeline: Bronze → Silver → Gold
    ├── Lakebase Autoscaling Project
    │   ├── production branch (0.5-4 CU)
    │   └── development branch (0.5-2 CU, 7-day TTL)
    ├── Lakebase Postgres Catalog (synced from Gold)
    │   ├── assessment_summary_by_classroom_synced
    │   ├── educator_performance_metrics_synced
    │   └── school_performance_overview_synced
    └── Permissions (UC grants + Lakebase ACLs + Postgres roles)
```

## Prerequisites

- **Terraform** >= 1.5.0
- **Databricks provider** >= 1.65.0
- **Databricks CLI** authenticated with an account-level OAuth profile (`one-env-account`)
- **Python 3** (for synthetic data generation — no external dependencies)
- Account ID: `0d26daa6-5e44-4c97-a497-ef015f91254a`
- Metastore: `metastore_aws_us_east_1` must exist in us-east-1

## Quick Start

```bash
# 1. Generate synthetic data
python scripts/generate_data.py

# 2. Copy and edit variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars as needed

# 3. Deploy
terraform init
terraform plan -out=tfplan
terraform apply tfplan

# 4. Verify
terraform output
```

## Modules

| Module | Phase | Resources |
|--------|-------|-----------|
| `workspace/` | 1 | Serverless workspace, metastore assignment, service principal |
| `unity-catalog/` | 2 | Catalog, 3 schemas (bronze/silver/gold), managed volume, CSV upload |
| `pipeline/` | 3 | SDP notebook + pipeline (serverless, Bronze→Silver→Gold) |
| `lakebase/` | 4 | Postgres project, production + dev branches, endpoints |
| `sync/` | 5 | Lakebase Postgres catalog (REST API), 3 synced tables (REST API) |
| `permissions/` | 6 | UC grants, lakebase-users group, project ACLs (REST API) |

## Synthetic Data

Six entities generated with Python stdlib (1,000+ rows each):

| Entity | Rows | Key Columns |
|--------|------|-------------|
| schools | 50 | school_id, name, district, state, school_type |
| educators | 200 | educator_id, name, role, certification, school_id |
| classrooms | 150 | classroom_id, name, grade_level, school_id, educator_id |
| students | 1,500 | student_id, name, dob, grade_level, classroom_id |
| learning_objectives | 100 | objective_id, subject, domain, standard_code |
| assessments | 5,000 | assessment_id, student_id, score (1-9), subject, period |

## Pipeline: Bronze → Silver → Gold

- **Bronze**: Raw CSV ingestion with `_ingested_at` and `_source_file` metadata
- **Silver**: Dedup on natural keys, type casting, null filtering, `_processed_at`
- **Gold**: Three aggregate tables:
  - `assessment_summary_by_classroom` — scores by classroom + subject + period
  - `educator_performance_metrics` — student count and avg scores per educator
  - `school_performance_overview` — school-level rollups

## Lakebase Configuration

- **Project**: `teaching-strategies-project` (Postgres 17)
- **Production**: Protected branch, 0.5–4.0 CU autoscaling, 5-min suspend timeout
- **Development**: 7-day TTL, 0.5–2.0 CU autoscaling
- **Synced tables**: Gold → Postgres via SNAPSHOT mode

## Permissions

### UC Grants

| Object | Service Principal | andrea.tardif@ | lakebase-users |
|--------|------------------|----------------|----------------|
| Catalog | ALL_PRIVILEGES | ALL_PRIVILEGES | USE_CATALOG |
| Schemas | ALL_PRIVILEGES | ALL_PRIVILEGES | USE_SCHEMA, SELECT |
| Volume | ALL_PRIVILEGES | ALL_PRIVILEGES | READ_VOLUME |

### Lakebase Project ACLs

| Identity | Permission |
|----------|-----------|
| Service Principal | CAN MANAGE |
| andrea.tardif@ | CAN MANAGE |
| lakebase-users | CAN USE |

### Postgres Roles (branch-scoped)

| Identity | Production | Development |
|----------|-----------|-------------|
| SP + andrea.tardif@ | databricks_superuser | databricks_superuser |
| lakebase-users | standard role | databricks_superuser |

## Teardown

```bash
terraform destroy

# Manual cleanup if needed:
bash scripts/create_synced_tables.sh --delete <workspace_url> teaching_strategies_pg one-env-account
bash scripts/create_lakebase_catalog.sh --delete <workspace_url> teaching_strategies_pg one-env-account
```

## Tool Split

~80% Terraform, ~20% REST API (via shell scripts in `scripts/`):

- **Terraform**: workspace, metastore, SP, catalog, schemas, volume, pipeline, Lakebase project/branch/endpoint, UC grants
- **REST API**: Lakebase Postgres catalog, synced tables, project ACLs, Postgres role grants

REST API fallback is needed because the Terraform provider doesn't yet support Lakebase Autoscaling catalogs or synced tables.
