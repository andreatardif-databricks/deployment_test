# Lakebase Terraform Project — Design Spec

**Date:** 2026-04-03
**Author:** Andrea Tardif + Claude Code
**Status:** Draft

---

## 1. Overview

Deploy a complete Databricks environment via Terraform, including a new serverless workspace, Unity Catalog structure, a Spark Declarative Pipeline (SDP) processing synthetic education data through Bronze/Silver/Gold layers, and a Lakebase Autoscaling Postgres backend with synced tables and role-based permissions.

**Target account:** `0d26daa6-5e44-4c97-a497-ef015f91254a`
**Metastore:** `metastore_aws_us_east_1` (`cc9be128-0493-426b-8d96-68d98d08517b`)
**Region:** `us-east-1`
**Auth:** OAuth via `one-env-account` CLI profile (account-level)

## 2. Tool Split

| Resource | Tool | Reason |
|----------|------|--------|
| Workspace (serverless) | Terraform `databricks_mws_workspaces` | Full TF support |
| Metastore assignment | Terraform `databricks_metastore_assignment` | Full TF support |
| Service principal | Terraform `databricks_service_principal` | Full TF support |
| UC catalog, schemas, volume | Terraform `databricks_catalog`, `databricks_schema`, `databricks_volume` | Full TF support |
| SDP pipeline + notebook | Terraform `databricks_pipeline`, `databricks_notebook` | Full TF support |
| Lakebase project | Terraform `databricks_postgres_project` | Full TF support |
| Lakebase branch | Terraform `databricks_postgres_branch` | Full TF support |
| Lakebase endpoint | Terraform `databricks_postgres_endpoint` | Full TF support |
| Lakebase Postgres catalog | REST API via `null_resource` | No TF support for Autoscaling catalogs |
| Synced tables | REST API via `null_resource` | No TF support for Autoscaling synced tables |
| UC grants | Terraform `databricks_grants` | Full TF support |
| Lakebase project permissions | REST API via `null_resource` | Project ACLs not in TF |
| Lakebase database roles | REST API via `null_resource` | Postgres roles not in TF |
| Synthetic data | Python script (Faker), run locally | Not infrastructure |

## 3. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Account: 0d26daa6-5e44-4c97-a497-ef015f91254a                 │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  New Serverless Workspace (us-east-1)                     │  │
│  │  Metastore: metastore_aws_us_east_1                       │  │
│  │                                                           │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  Unity Catalog: teaching_strategies                 │  │  │
│  │  │  ├── bronze (schema)                                │  │  │
│  │  │  │   ├── raw_data (volume) ← CSV upload             │  │  │
│  │  │  │   ├── students, educators, schools,              │  │  │
│  │  │  │   │   classrooms, assessments,                   │  │  │
│  │  │  │   │   learning_objectives (raw Delta)            │  │  │
│  │  │  ├── silver (schema)                                │  │  │
│  │  │  │   ├── cleaned/deduped versions of above          │  │  │
│  │  │  ├── gold (schema)                                  │  │  │
│  │  │  │   ├── assessment_summary_by_classroom            │  │  │
│  │  │  │   ├── educator_performance_metrics               │  │  │
│  │  │  │   └── school_performance_overview                │  │  │
│  │  │  └───────────────────────────────────────────────────│  │  │
│  │  │                                                     │  │  │
│  │  │  SDP Pipeline: teaching_strategies_pipeline         │  │  │
│  │  │  (Bronze → Silver → Gold)                           │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                                                           │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  Lakebase Autoscaling                               │  │  │
│  │  │  Project: teaching-strategies-project               │  │  │
│  │  │  ├── production (branch, protected)                 │  │  │
│  │  │  │   └── ep-primary (endpoint, 0.5-4 CU)           │  │  │
│  │  │  └── development (branch, 7-day TTL)               │  │  │
│  │  │       └── ep-primary (endpoint, 0.5-2 CU)          │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                                                           │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  Lakebase Postgres Catalog: teaching_strategies_pg  │  │  │
│  │  │  (synced from Gold Delta tables → Postgres)         │  │  │
│  │  │  ├── assessment_summary_by_classroom_synced         │  │  │
│  │  │  ├── educator_performance_metrics_synced            │  │  │
│  │  │  └── school_performance_overview_synced             │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 4. Data Flow

```
1. generate_data.py (Faker) → CSV files → data/ (local)
2. Terraform uploads CSVs → /Volumes/teaching_strategies/bronze/raw_data/
3. SDP Pipeline ingests CSVs:
   Bronze: raw ingestion + _ingested_at, _source_file metadata
   Silver: dedup on natural keys, cast types, null handling, + _processed_at
   Gold:   aggregate views (3 summary tables)
4. Synced tables replicate Gold → Lakebase Postgres (SNAPSHOT mode)
5. Lakebase Postgres catalog exposes synced tables via UC namespace
```

## 5. File Structure

```
lakebase-terraform/
├── providers.tf                    # Account + workspace aliased providers
├── variables.tf                    # Global variables
├── outputs.tf                      # Workspace URL, Lakebase endpoint, etc.
├── main.tf                         # Module orchestration
├── terraform.tfvars.example        # Example variable values
├── modules/
│   ├── workspace/
│   │   ├── main.tf                 # databricks_mws_workspaces (serverless)
│   │   │                           # databricks_metastore_assignment
│   │   │                           # databricks_service_principal
│   │   ├── variables.tf
│   │   └── outputs.tf              # workspace_url, workspace_id, sp_id
│   ├── unity-catalog/
│   │   ├── main.tf                 # databricks_catalog, 3x databricks_schema
│   │   │                           # databricks_volume
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── pipeline/
│   │   ├── main.tf                 # databricks_notebook (upload)
│   │   │                           # databricks_pipeline (SDP, serverless)
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── notebooks/
│   │       └── teaching_strategies_pipeline.py
│   ├── lakebase/
│   │   ├── main.tf                 # databricks_postgres_project
│   │   │                           # databricks_postgres_branch (production + dev)
│   │   │                           # databricks_postgres_endpoint (per branch)
│   │   │                           # null_resource for Lakebase Postgres catalog
│   │   ├── variables.tf
│   │   └── outputs.tf              # project_id, branch_ids, endpoint hosts
│   ├── sync/
│   │   ├── main.tf                 # null_resource for synced tables REST API
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── permissions/
│       ├── main.tf                 # databricks_grants for UC objects
│       │                           # null_resource for Lakebase project ACLs
│       │                           # null_resource for Postgres role grants
│       ├── variables.tf
│       └── outputs.tf
├── scripts/
│   ├── generate_data.py            # Faker-based synthetic data generation
│   ├── create_lakebase_catalog.sh  # REST API: create Lakebase Postgres catalog
│   ├── create_synced_tables.sh     # REST API: create synced tables
│   └── manage_lakebase_perms.sh    # REST API: project ACLs + Postgres roles
├── data/                           # Local copy of generated CSVs
│   └── .gitkeep
└── README.md
```

## 6. Terraform Providers

```hcl
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = ">= 1.65.0"
    }
  }
}

# Account-level provider (workspace creation, metastore assignment)
provider "databricks" {
  alias      = "account"
  host       = "https://accounts.cloud.databricks.com"
  account_id = var.account_id
  auth_type  = "databricks-cli"
  profile    = "one-env-account"
}

# Workspace-level provider (UC, pipeline, Lakebase, permissions)
# Dynamically configured from the new workspace
provider "databricks" {
  alias     = "workspace"
  host      = module.workspace.workspace_url
  auth_type = "databricks-cli"
  profile   = "one-env-account"
}
```

## 7. Synthetic Data Schema

Six entities, 1,000+ rows each, generated with Faker:

### students
| Column | Type | Description |
|--------|------|-------------|
| student_id | STRING | UUID primary key |
| first_name | STRING | Faker first name |
| last_name | STRING | Faker last name |
| date_of_birth | DATE | Random DOB (ages 3-12) |
| grade_level | STRING | PreK, K, 1-6 |
| school_id | STRING | FK to schools |
| classroom_id | STRING | FK to classrooms |
| enrollment_date | DATE | Within last 3 years |
| status | STRING | active, inactive, transferred |

### educators
| Column | Type | Description |
|--------|------|-------------|
| educator_id | STRING | UUID primary key |
| first_name | STRING | Faker first name |
| last_name | STRING | Faker last name |
| email | STRING | Faker email |
| role | STRING | lead_teacher, assistant, specialist, administrator |
| certification | STRING | early_childhood, elementary, special_ed, ESL |
| school_id | STRING | FK to schools |
| hire_date | DATE | Within last 10 years |
| status | STRING | active, on_leave, retired |

### schools
| Column | Type | Description |
|--------|------|-------------|
| school_id | STRING | UUID primary key |
| name | STRING | Faker school name |
| district | STRING | Faker city-based district |
| state | STRING | US state abbreviation |
| school_type | STRING | public, private, charter, head_start |
| grade_range | STRING | PreK-K, PreK-3, K-6 |
| student_capacity | INT | 50-500 |

### classrooms
| Column | Type | Description |
|--------|------|-------------|
| classroom_id | STRING | UUID primary key |
| name | STRING | e.g., "Room 101 - Butterflies" |
| grade_level | STRING | PreK, K, 1-6 |
| school_id | STRING | FK to schools |
| educator_id | STRING | FK to educators (lead teacher) |
| capacity | INT | 8-30 |
| program_type | STRING | general, montessori, bilingual, STEM |

### assessments
| Column | Type | Description |
|--------|------|-------------|
| assessment_id | STRING | UUID primary key |
| student_id | STRING | FK to students |
| educator_id | STRING | FK to educators (assessor) |
| subject | STRING | literacy, math, social_emotional, science, physical |
| domain | STRING | Subject-specific domain |
| score | DOUBLE | 1.0-9.0 scale (TS GOLD-like) |
| assessment_date | DATE | Within last 2 years |
| assessment_period | STRING | fall, winter, spring |
| learning_objective_id | STRING | FK to learning_objectives |
| notes | STRING | Optional observation notes |

### learning_objectives
| Column | Type | Description |
|--------|------|-------------|
| objective_id | STRING | UUID primary key |
| subject | STRING | literacy, math, social_emotional, science, physical |
| domain | STRING | Subject-specific domain |
| description | STRING | Learning objective text |
| grade_level | STRING | PreK, K, 1-6 |
| standard_code | STRING | e.g., "SE.1.2", "LIT.3.4" |

## 8. SDP Pipeline Transformations

### Bronze Layer
- Read CSVs from `/Volumes/teaching_strategies/bronze/raw_data/`
- Add metadata: `_ingested_at` (current_timestamp), `_source_file` (input_file_name)
- Write as Delta tables to `teaching_strategies.bronze.*`
- No schema enforcement — store as-is

### Silver Layer
- Read from Bronze Delta tables
- Dedup on natural keys (e.g., `student_id`, `assessment_id`)
- Cast types: strings → dates, strings → doubles where appropriate
- Drop rows with null primary keys
- Add `_processed_at` timestamp
- Write as Delta tables to `teaching_strategies.silver.*`

### Gold Layer

**`assessment_summary_by_classroom`**
```sql
SELECT
  c.classroom_id, c.name as classroom_name, c.grade_level,
  s.school_id, sc.name as school_name,
  a.subject, a.assessment_period,
  COUNT(DISTINCT a.student_id) as student_count,
  ROUND(AVG(a.score), 2) as avg_score,
  MIN(a.score) as min_score,
  MAX(a.score) as max_score,
  ROUND(STDDEV(a.score), 2) as stddev_score
FROM silver.assessments a
JOIN silver.students s ON a.student_id = s.student_id
JOIN silver.classrooms c ON s.classroom_id = c.classroom_id
JOIN silver.schools sc ON c.school_id = sc.school_id
GROUP BY 1,2,3,4,5,6,7
```

**`educator_performance_metrics`**
```sql
SELECT
  e.educator_id, e.first_name, e.last_name, e.role,
  sc.name as school_name,
  COUNT(DISTINCT s.student_id) as student_count,
  COUNT(DISTINCT a.assessment_id) as assessment_count,
  ROUND(AVG(a.score), 2) as avg_student_score,
  COUNT(DISTINCT c.classroom_id) as classroom_count
FROM silver.educators e
JOIN silver.classrooms c ON e.educator_id = c.educator_id
JOIN silver.students s ON s.classroom_id = c.classroom_id
JOIN silver.assessments a ON a.student_id = s.student_id
JOIN silver.schools sc ON e.school_id = sc.school_id
GROUP BY 1,2,3,4,5
```

**`school_performance_overview`**
```sql
SELECT
  sc.school_id, sc.name, sc.district, sc.state, sc.school_type,
  COUNT(DISTINCT s.student_id) as total_students,
  COUNT(DISTINCT e.educator_id) as total_educators,
  COUNT(DISTINCT c.classroom_id) as total_classrooms,
  ROUND(AVG(a.score), 2) as avg_assessment_score,
  COUNT(DISTINCT a.assessment_id) as total_assessments
FROM silver.schools sc
LEFT JOIN silver.classrooms c ON sc.school_id = c.school_id
LEFT JOIN silver.students s ON s.school_id = sc.school_id
LEFT JOIN silver.educators e ON e.school_id = sc.school_id
LEFT JOIN silver.assessments a ON a.student_id = s.student_id
GROUP BY 1,2,3,4,5
```

## 9. Lakebase Configuration

### Project
- **Project ID:** `teaching-strategies-project`
- **Display name:** "Teaching Strategies Lakebase"
- **Postgres version:** 17
- **Region:** us-east-1 (inherited from workspace)

### Branches
| Branch | Source | Protected | TTL | Compute (CU) |
|--------|--------|-----------|-----|---------------|
| `production` | (default) | Yes | None | 0.5 – 4.0 |
| `development` | production | No | 7 days | 0.5 – 2.0 |

### Lakebase Postgres Catalog
- **Catalog name:** `teaching_strategies_pg`
- **Type:** Lakebase Postgres (Autoscaling)
- **Project:** `teaching-strategies-project`
- **Branch:** `production`
- **Database:** `databricks_postgres`
- **Created via:** REST API (`POST /api/2.1/unity-catalog/catalogs`)

### Synced Tables (Gold → Postgres)
| Source (Delta) | Target (Postgres) | Sync Mode |
|---------------|-------------------|-----------|
| `teaching_strategies.gold.assessment_summary_by_classroom` | `teaching_strategies_pg.public.assessment_summary_by_classroom_synced` | SNAPSHOT |
| `teaching_strategies.gold.educator_performance_metrics` | `teaching_strategies_pg.public.educator_performance_metrics_synced` | SNAPSHOT |
| `teaching_strategies.gold.school_performance_overview` | `teaching_strategies_pg.public.school_performance_overview_synced` | SNAPSHOT |

Created via REST API: `POST /api/2.0/database/synced_tables`

## 10. Permissions

### Lakebase Project Permissions (ACLs)

| Identity | Production Branch | Development Branch |
|----------|------------------|-------------------|
| Service Principal (`lakebase-terraform-sp`) | CAN MANAGE | CAN MANAGE |
| `andrea.tardif@databricks.com` | CAN MANAGE | CAN MANAGE |
| Group `lakebase-users` | CAN USE | CAN USE |

Applied via Databricks workspace ACLs on the project resource.

### Lakebase Postgres Roles (branch-scoped)

Roles are branch-scoped. Child branches inherit from parent but can diverge.

**Production branch:**

| Identity | Role Membership | Attributes |
|----------|----------------|------------|
| Service Principal | `databricks_superuser` | CREATEDB, CREATEROLE |
| `andrea.tardif@databricks.com` | `databricks_superuser` | CREATEDB, CREATEROLE |
| Group `lakebase-users` | (standard role, no superuser) | — |

**Development branch:**

| Identity | Role Membership | Attributes |
|----------|----------------|------------|
| Service Principal | `databricks_superuser` | CREATEDB, CREATEROLE |
| `andrea.tardif@databricks.com` | `databricks_superuser` | CREATEDB, CREATEROLE |
| Group `lakebase-users` | `databricks_superuser` | CREATEDB, CREATEROLE |

### Unity Catalog Grants

| Object | Service Principal | andrea.tardif@ | lakebase-users |
|--------|------------------|----------------|----------------|
| Catalog `teaching_strategies` | ALL_PRIVILEGES | ALL_PRIVILEGES | USE_CATALOG |
| Schema `bronze` | ALL_PRIVILEGES | ALL_PRIVILEGES | USE_SCHEMA, SELECT |
| Schema `silver` | ALL_PRIVILEGES | ALL_PRIVILEGES | USE_SCHEMA, SELECT |
| Schema `gold` | ALL_PRIVILEGES | ALL_PRIVILEGES | USE_SCHEMA, SELECT |
| Volume `raw_data` | ALL_PRIVILEGES | ALL_PRIVILEGES | READ_VOLUME |
| Catalog `teaching_strategies_pg` | ALL_PRIVILEGES | ALL_PRIVILEGES | USE_CATALOG, SELECT |

## 11. Execution Order

Terraform handles dependency ordering. The phases map to module dependencies:

```
Phase 1: module.workspace (no dependencies)
Phase 2: module.unity_catalog (depends on workspace)
         → scripts/generate_data.py (run via null_resource after volume created)
Phase 3: module.pipeline (depends on unity_catalog + data upload)
Phase 4: module.lakebase (depends on workspace)
         → scripts/create_lakebase_catalog.sh (after project + branch ready)
Phase 5: module.sync (depends on pipeline + lakebase)
         → scripts/create_synced_tables.sh
Phase 6: module.permissions (depends on all above)
         → scripts/manage_lakebase_perms.sh
```

All phases execute in a single `terraform apply`. The `null_resource` blocks with `depends_on` enforce ordering for REST API calls.

## 12. Deployment

```bash
cd lakebase-terraform/

# Generate synthetic data locally
python scripts/generate_data.py

# Initialize and apply
terraform init
terraform plan -out=tfplan
terraform apply tfplan

# Verify
terraform output
```

## 13. Teardown

Reverse order to avoid dependency conflicts:

```bash
# Destroy in reverse
terraform destroy

# If synced tables need manual cleanup:
bash scripts/create_synced_tables.sh --delete

# If Lakebase catalog needs manual cleanup:
bash scripts/create_lakebase_catalog.sh --delete
```

## 14. Open Questions / Risks

1. **Workspace OAuth propagation** — After creating the workspace, it may take a few minutes before the workspace-level provider can authenticate. May need a `time_sleep` resource.
2. **Lakebase Postgres catalog API** — The exact API payload for creating a Lakebase Postgres catalog linked to an Autoscaling project needs verification at apply time. The REST API format may differ from the UI flow shown in the screenshot.
3. **Synced tables API** — Per memory notes, the REST endpoint uses bare IDs (no `projects/` prefix). Will use the known working format from `credit_acceptance_multi_agent_demo`.
4. **SDP serverless compute** — Pipeline will use serverless compute. If not available in the new workspace, may need to configure a cluster policy.
