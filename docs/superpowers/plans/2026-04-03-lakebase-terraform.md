# Lakebase Terraform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy a complete Databricks environment via Terraform — serverless workspace, Unity Catalog with Bronze/Silver/Gold schemas, SDP pipeline, Lakebase Autoscaling Postgres, synced tables, and permissions.

**Architecture:** Terraform modules for ~80% of resources (workspace, UC, pipeline, Lakebase project/branch/endpoint, grants). REST API via `null_resource` + shell scripts for unsupported resources (Lakebase Postgres catalog, synced tables, database roles). Synthetic data generated locally with Faker.

**Tech Stack:** Terraform >= 1.5, Databricks provider >= 1.65.0, Python 3 + Faker, Databricks CLI, bash/curl for REST API calls.

**Spec:** `docs/superpowers/specs/2026-04-03-lakebase-terraform-design.md`

---

## File Map

```
lakebase-terraform/
├── providers.tf              # Account + workspace aliased providers
├── variables.tf              # All input variables
├── outputs.tf                # Key outputs
├── main.tf                   # Module orchestration
├── terraform.tfvars.example  # Example values
├── modules/
│   ├── workspace/
│   │   ├── main.tf           # mws_workspaces, metastore_assignment, service_principal
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── unity-catalog/
│   │   ├── main.tf           # catalog, 3x schema, volume, null_resource for data upload
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── pipeline/
│   │   ├── main.tf           # notebook upload, pipeline resource
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── notebooks/
│   │       └── teaching_strategies_pipeline.py
│   ├── lakebase/
│   │   ├── main.tf           # postgres_project, postgres_branch x2, postgres_endpoint x2
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── sync/
│   │   ├── main.tf           # null_resource for lakebase catalog + synced tables
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── permissions/
│       ├── main.tf           # databricks_grants for UC, null_resource for Lakebase perms
│       ├── variables.tf
│       └── outputs.tf
├── scripts/
│   ├── generate_data.py      # Faker synthetic data generator
│   ├── create_lakebase_catalog.sh
│   ├── create_synced_tables.sh
│   └── manage_lakebase_perms.sh
├── data/
│   └── .gitkeep
└── README.md
```

---

### Task 1: Scaffold Project Structure

**Files:**
- Create: `lakebase-terraform/providers.tf`
- Create: `lakebase-terraform/variables.tf`
- Create: `lakebase-terraform/outputs.tf`
- Create: `lakebase-terraform/main.tf`
- Create: `lakebase-terraform/terraform.tfvars.example`
- Create: `lakebase-terraform/data/.gitkeep`

- [ ] **Step 1: Create project directory and providers.tf**

```bash
mkdir -p lakebase-terraform
```

Write `lakebase-terraform/providers.tf`:

```hcl
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = ">= 1.65.0"
    }
    null = {
      source  = "hashicorp/null"
      version = ">= 3.0"
    }
    time = {
      source  = "hashicorp/time"
      version = ">= 0.9"
    }
  }
}

# Account-level provider (workspace creation, metastore assignment)
provider "databricks" {
  alias      = "account"
  host       = "https://accounts.cloud.databricks.com"
  account_id = var.account_id
  auth_type  = "databricks-cli"
  profile    = var.account_profile
}

# Workspace-level provider (UC, pipeline, Lakebase, permissions)
provider "databricks" {
  alias     = "workspace"
  host      = module.workspace.workspace_url
  auth_type = "databricks-cli"
  profile   = var.account_profile
}
```

- [ ] **Step 2: Create variables.tf**

Write `lakebase-terraform/variables.tf`:

```hcl
variable "account_id" {
  description = "Databricks account ID"
  type        = string
  default     = "0d26daa6-5e44-4c97-a497-ef015f91254a"
}

variable "account_profile" {
  description = "Databricks CLI profile for account-level OAuth"
  type        = string
  default     = "one-env-account"
}

variable "workspace_name" {
  description = "Name for the new serverless workspace"
  type        = string
  default     = "lakebase-terraform-ws"
}

variable "aws_region" {
  description = "AWS region for the workspace"
  type        = string
  default     = "us-east-1"
}

variable "metastore_id" {
  description = "ID of existing metastore to assign"
  type        = string
  default     = "cc9be128-0493-426b-8d96-68d98d08517b"
}

variable "catalog_name" {
  description = "Unity Catalog catalog name"
  type        = string
  default     = "teaching_strategies"
}

variable "lakebase_project_id" {
  description = "Lakebase Autoscaling project ID"
  type        = string
  default     = "teaching-strategies-project"
}

variable "lakebase_catalog_name" {
  description = "Name for the Lakebase Postgres UC catalog"
  type        = string
  default     = "teaching_strategies_pg"
}

variable "user_email" {
  description = "Primary user email for permissions"
  type        = string
  default     = "andrea.tardif@databricks.com"
}

variable "service_principal_name" {
  description = "Display name for the service principal"
  type        = string
  default     = "lakebase-terraform-sp"
}

variable "group_name" {
  description = "Group name for Lakebase users"
  type        = string
  default     = "lakebase-users"
}
```

- [ ] **Step 3: Create main.tf (module orchestration)**

Write `lakebase-terraform/main.tf`:

```hcl
# Phase 1: Workspace, metastore, service principal
module "workspace" {
  source = "./modules/workspace"

  providers = {
    databricks = databricks.account
  }

  account_id              = var.account_id
  workspace_name          = var.workspace_name
  aws_region              = var.aws_region
  metastore_id            = var.metastore_id
  service_principal_name  = var.service_principal_name
}

# Phase 2: Unity Catalog structure + data upload
module "unity_catalog" {
  source = "./modules/unity-catalog"

  providers = {
    databricks = databricks.workspace
  }

  catalog_name = var.catalog_name
  data_dir     = "${path.root}/data"

  depends_on = [module.workspace]
}

# Phase 3: SDP Pipeline
module "pipeline" {
  source = "./modules/pipeline"

  providers = {
    databricks = databricks.workspace
  }

  catalog_name = var.catalog_name

  depends_on = [module.unity_catalog]
}

# Phase 4: Lakebase Autoscaling
module "lakebase" {
  source = "./modules/lakebase"

  providers = {
    databricks = databricks.workspace
  }

  project_id = var.lakebase_project_id

  depends_on = [module.workspace]
}

# Phase 5: Synced tables (REST API)
module "sync" {
  source = "./modules/sync"

  providers = {
    databricks = databricks.workspace
  }

  workspace_url         = module.workspace.workspace_url
  catalog_name          = var.catalog_name
  lakebase_catalog_name = var.lakebase_catalog_name
  lakebase_project_name = module.lakebase.project_name
  lakebase_project_uid  = module.lakebase.project_uid
  lakebase_branch_id    = module.lakebase.production_branch_uid
  account_profile       = var.account_profile

  depends_on = [module.pipeline, module.lakebase]
}

# Phase 6: Permissions
module "permissions" {
  source = "./modules/permissions"

  providers = {
    databricks = databricks.workspace
  }

  catalog_name          = var.catalog_name
  lakebase_catalog_name = var.lakebase_catalog_name
  service_principal_id  = module.workspace.service_principal_app_id
  user_email            = var.user_email
  group_name            = var.group_name
  workspace_url         = module.workspace.workspace_url
  lakebase_project_name = module.lakebase.project_name
  account_profile       = var.account_profile

  depends_on = [module.sync]
}
```

- [ ] **Step 4: Create outputs.tf**

Write `lakebase-terraform/outputs.tf`:

```hcl
output "workspace_url" {
  description = "URL of the new serverless workspace"
  value       = module.workspace.workspace_url
}

output "workspace_id" {
  description = "ID of the new workspace"
  value       = module.workspace.workspace_id
}

output "service_principal_app_id" {
  description = "Application ID of the service principal"
  value       = module.workspace.service_principal_app_id
}

output "lakebase_project_name" {
  description = "Lakebase project resource name"
  value       = module.lakebase.project_name
}

output "lakebase_production_endpoint" {
  description = "Production branch endpoint host"
  value       = module.lakebase.production_endpoint_host
}

output "lakebase_dev_endpoint" {
  description = "Development branch endpoint host"
  value       = module.lakebase.dev_endpoint_host
}
```

- [ ] **Step 5: Create terraform.tfvars.example and data/.gitkeep**

Write `lakebase-terraform/terraform.tfvars.example`:

```hcl
account_id              = "0d26daa6-5e44-4c97-a497-ef015f91254a"
account_profile         = "one-env-account"
workspace_name          = "lakebase-terraform-ws"
aws_region              = "us-east-1"
metastore_id            = "cc9be128-0493-426b-8d96-68d98d08517b"
catalog_name            = "teaching_strategies"
lakebase_project_id     = "teaching-strategies-project"
lakebase_catalog_name   = "teaching_strategies_pg"
user_email              = "andrea.tardif@databricks.com"
service_principal_name  = "lakebase-terraform-sp"
group_name              = "lakebase-users"
```

Create `lakebase-terraform/data/.gitkeep` (empty file).

- [ ] **Step 6: Run terraform init to validate provider config**

```bash
cd lakebase-terraform && terraform init
```

Expected: Successful initialization, providers downloaded.

- [ ] **Step 7: Commit**

```bash
git add lakebase-terraform/providers.tf lakebase-terraform/variables.tf \
  lakebase-terraform/main.tf lakebase-terraform/outputs.tf \
  lakebase-terraform/terraform.tfvars.example lakebase-terraform/data/.gitkeep
git commit -m "feat: scaffold lakebase-terraform project structure"
```

---

### Task 2: Workspace Module (Phase 1)

**Files:**
- Create: `lakebase-terraform/modules/workspace/main.tf`
- Create: `lakebase-terraform/modules/workspace/variables.tf`
- Create: `lakebase-terraform/modules/workspace/outputs.tf`

- [ ] **Step 1: Create modules/workspace/variables.tf**

```hcl
variable "account_id" {
  description = "Databricks account ID"
  type        = string
}

variable "workspace_name" {
  description = "Name for the serverless workspace"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "metastore_id" {
  description = "Metastore ID to assign to the workspace"
  type        = string
}

variable "service_principal_name" {
  description = "Display name for the service principal"
  type        = string
}
```

- [ ] **Step 2: Create modules/workspace/main.tf**

```hcl
terraform {
  required_providers {
    databricks = {
      source = "databricks/databricks"
    }
  }
}

# Create serverless workspace
resource "databricks_mws_workspaces" "this" {
  account_id     = var.account_id
  workspace_name = var.workspace_name
  aws_region     = var.aws_region
  compute_mode   = "SERVERLESS"
}

# Wait for workspace to be ready
resource "time_sleep" "workspace_ready" {
  depends_on      = [databricks_mws_workspaces.this]
  create_duration = "120s"
}

# Assign metastore to the new workspace
resource "databricks_metastore_assignment" "this" {
  workspace_id = databricks_mws_workspaces.this.workspace_id
  metastore_id = var.metastore_id

  depends_on = [time_sleep.workspace_ready]
}

# Create service principal
resource "databricks_service_principal" "this" {
  display_name = var.service_principal_name
  active       = true

  depends_on = [time_sleep.workspace_ready]
}
```

- [ ] **Step 3: Create modules/workspace/outputs.tf**

```hcl
output "workspace_url" {
  description = "The URL of the created workspace"
  value       = databricks_mws_workspaces.this.workspace_url
}

output "workspace_id" {
  description = "The numeric ID of the workspace"
  value       = databricks_mws_workspaces.this.workspace_id
}

output "service_principal_app_id" {
  description = "Application ID of the service principal"
  value       = databricks_service_principal.this.application_id
}

output "service_principal_id" {
  description = "Internal ID of the service principal"
  value       = databricks_service_principal.this.id
}
```

- [ ] **Step 4: Run terraform validate**

```bash
cd lakebase-terraform && terraform validate
```

Expected: "Success! The configuration is valid."

- [ ] **Step 5: Commit**

```bash
git add lakebase-terraform/modules/workspace/
git commit -m "feat: add workspace module — serverless workspace, metastore, SP"
```

---

### Task 3: Unity Catalog Module (Phase 2)

**Files:**
- Create: `lakebase-terraform/modules/unity-catalog/main.tf`
- Create: `lakebase-terraform/modules/unity-catalog/variables.tf`
- Create: `lakebase-terraform/modules/unity-catalog/outputs.tf`

- [ ] **Step 1: Create modules/unity-catalog/variables.tf**

```hcl
variable "catalog_name" {
  description = "Name of the Unity Catalog catalog"
  type        = string
}

variable "data_dir" {
  description = "Local directory containing CSV data files"
  type        = string
}
```

- [ ] **Step 2: Create modules/unity-catalog/main.tf**

```hcl
terraform {
  required_providers {
    databricks = {
      source = "databricks/databricks"
    }
  }
}

# Catalog
resource "databricks_catalog" "this" {
  name    = var.catalog_name
  comment = "Teaching Strategies education domain data"
}

# Schemas
resource "databricks_schema" "bronze" {
  catalog_name = databricks_catalog.this.name
  name         = "bronze"
  comment      = "Raw ingestion layer"
}

resource "databricks_schema" "silver" {
  catalog_name = databricks_catalog.this.name
  name         = "silver"
  comment      = "Cleaned and deduplicated data"
}

resource "databricks_schema" "gold" {
  catalog_name = databricks_catalog.this.name
  name         = "gold"
  comment      = "Business-ready aggregations"
}

# Volume for raw data landing
resource "databricks_volume" "raw_data" {
  catalog_name = databricks_catalog.this.name
  schema_name  = databricks_schema.bronze.name
  name         = "raw_data"
  volume_type  = "MANAGED"
  comment      = "Raw CSV data landing zone"
}

# Upload CSVs to volume
resource "null_resource" "upload_data" {
  depends_on = [databricks_volume.raw_data]

  triggers = {
    data_dir = var.data_dir
  }

  provisioner "local-exec" {
    command = <<-EOT
      for csv_file in ${var.data_dir}/*.csv; do
        if [ -f "$csv_file" ]; then
          filename=$(basename "$csv_file")
          databricks fs cp "$csv_file" \
            "dbfs:/Volumes/${var.catalog_name}/bronze/raw_data/$filename" \
            --overwrite
        fi
      done
    EOT
  }
}
```

- [ ] **Step 3: Create modules/unity-catalog/outputs.tf**

```hcl
output "catalog_name" {
  value = databricks_catalog.this.name
}

output "bronze_schema" {
  value = databricks_schema.bronze.name
}

output "silver_schema" {
  value = databricks_schema.silver.name
}

output "gold_schema" {
  value = databricks_schema.gold.name
}

output "volume_path" {
  value = "/Volumes/${databricks_catalog.this.name}/${databricks_schema.bronze.name}/${databricks_volume.raw_data.name}"
}
```

- [ ] **Step 4: Run terraform validate**

```bash
cd lakebase-terraform && terraform validate
```

Expected: "Success! The configuration is valid."

- [ ] **Step 5: Commit**

```bash
git add lakebase-terraform/modules/unity-catalog/
git commit -m "feat: add unity-catalog module — catalog, schemas, volume, data upload"
```

---

### Task 4: Synthetic Data Generator (Phase 2)

**Files:**
- Create: `lakebase-terraform/scripts/generate_data.py`

- [ ] **Step 1: Create scripts/generate_data.py**

```python
#!/usr/bin/env python3
"""Generate synthetic Teaching Strategies education domain data using Faker."""

import csv
import os
import random
import uuid
from datetime import date, timedelta
from pathlib import Path

from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# --- Configuration ---
NUM_SCHOOLS = 50
NUM_EDUCATORS = 200
NUM_CLASSROOMS = 150
NUM_STUDENTS = 1500
NUM_LEARNING_OBJECTIVES = 100
NUM_ASSESSMENTS = 5000

GRADE_LEVELS = ["PreK", "K", "1", "2", "3", "4", "5", "6"]
SCHOOL_TYPES = ["public", "private", "charter", "head_start"]
GRADE_RANGES = ["PreK-K", "PreK-3", "K-6"]
EDUCATOR_ROLES = ["lead_teacher", "assistant", "specialist", "administrator"]
CERTIFICATIONS = ["early_childhood", "elementary", "special_ed", "ESL"]
PROGRAM_TYPES = ["general", "montessori", "bilingual", "STEM"]
SUBJECTS = ["literacy", "math", "social_emotional", "science", "physical"]
ASSESSMENT_PERIODS = ["fall", "winter", "spring"]
STUDENT_STATUSES = ["active", "inactive", "transferred"]
EDUCATOR_STATUSES = ["active", "on_leave", "retired"]

DOMAINS = {
    "literacy": ["reading", "writing", "phonics", "vocabulary", "comprehension"],
    "math": ["counting", "geometry", "measurement", "patterns", "operations"],
    "social_emotional": ["self_regulation", "relationships", "empathy", "cooperation", "conflict_resolution"],
    "science": ["observation", "inquiry", "life_science", "physical_science", "earth_science"],
    "physical": ["gross_motor", "fine_motor", "balance", "coordination", "health"],
}

CLASSROOM_NAMES = [
    "Butterflies", "Sunflowers", "Starfish", "Ladybugs", "Dolphins",
    "Pandas", "Owls", "Turtles", "Rainbows", "Fireflies",
    "Hummingbirds", "Acorns", "Dragonflies", "Penguins", "Cubs",
]


def write_csv(filename: str, rows: list[dict]) -> None:
    """Write rows to a CSV file in the data directory."""
    filepath = DATA_DIR / filename
    if not rows:
        return
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Generated {len(rows):,} rows → {filepath}")


def generate_schools() -> list[dict]:
    rows = []
    for _ in range(NUM_SCHOOLS):
        rows.append({
            "school_id": str(uuid.uuid4()),
            "name": f"{fake.last_name()} {random.choice(['Academy', 'Elementary', 'Learning Center', 'School', 'Prep'])}",
            "district": f"{fake.city()} Unified School District",
            "state": fake.state_abbr(),
            "school_type": random.choice(SCHOOL_TYPES),
            "grade_range": random.choice(GRADE_RANGES),
            "student_capacity": random.randint(50, 500),
        })
    return rows


def generate_educators(schools: list[dict]) -> list[dict]:
    rows = []
    for _ in range(NUM_EDUCATORS):
        hire_date = fake.date_between(start_date="-10y", end_date="today")
        rows.append({
            "educator_id": str(uuid.uuid4()),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.unique.email(),
            "role": random.choice(EDUCATOR_ROLES),
            "certification": random.choice(CERTIFICATIONS),
            "school_id": random.choice(schools)["school_id"],
            "hire_date": hire_date.isoformat(),
            "status": random.choices(EDUCATOR_STATUSES, weights=[85, 10, 5])[0],
        })
    return rows


def generate_classrooms(schools: list[dict], educators: list[dict]) -> list[dict]:
    lead_teachers = [e for e in educators if e["role"] == "lead_teacher"]
    rows = []
    for i in range(NUM_CLASSROOMS):
        school = random.choice(schools)
        teacher = random.choice(lead_teachers) if lead_teachers else random.choice(educators)
        room_num = random.randint(100, 399)
        name_suffix = CLASSROOM_NAMES[i % len(CLASSROOM_NAMES)]
        rows.append({
            "classroom_id": str(uuid.uuid4()),
            "name": f"Room {room_num} - {name_suffix}",
            "grade_level": random.choice(GRADE_LEVELS),
            "school_id": school["school_id"],
            "educator_id": teacher["educator_id"],
            "capacity": random.randint(8, 30),
            "program_type": random.choice(PROGRAM_TYPES),
        })
    return rows


def generate_students(schools: list[dict], classrooms: list[dict]) -> list[dict]:
    rows = []
    for _ in range(NUM_STUDENTS):
        classroom = random.choice(classrooms)
        age_years = random.randint(3, 12)
        dob = date.today() - timedelta(days=age_years * 365 + random.randint(0, 364))
        enrollment_date = fake.date_between(start_date="-3y", end_date="today")
        rows.append({
            "student_id": str(uuid.uuid4()),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "date_of_birth": dob.isoformat(),
            "grade_level": classroom["grade_level"],
            "school_id": classroom["school_id"],
            "classroom_id": classroom["classroom_id"],
            "enrollment_date": enrollment_date.isoformat(),
            "status": random.choices(STUDENT_STATUSES, weights=[85, 10, 5])[0],
        })
    return rows


def generate_learning_objectives() -> list[dict]:
    rows = []
    for _ in range(NUM_LEARNING_OBJECTIVES):
        subject = random.choice(SUBJECTS)
        domain = random.choice(DOMAINS[subject])
        grade = random.choice(GRADE_LEVELS)
        prefix = subject[:3].upper()
        code = f"{prefix}.{random.randint(1, 9)}.{random.randint(1, 9)}"
        rows.append({
            "objective_id": str(uuid.uuid4()),
            "subject": subject,
            "domain": domain,
            "description": f"Student demonstrates proficiency in {domain} within {subject} for grade {grade}",
            "grade_level": grade,
            "standard_code": code,
        })
    return rows


def generate_assessments(
    students: list[dict],
    educators: list[dict],
    learning_objectives: list[dict],
) -> list[dict]:
    rows = []
    for _ in range(NUM_ASSESSMENTS):
        student = random.choice(students)
        educator = random.choice(educators)
        objective = random.choice(learning_objectives)
        assessment_date = fake.date_between(start_date="-2y", end_date="today")
        month = assessment_date.month
        if month <= 3:
            period = "winter"
        elif month <= 7:
            period = "spring"
        else:
            period = "fall"
        rows.append({
            "assessment_id": str(uuid.uuid4()),
            "student_id": student["student_id"],
            "educator_id": educator["educator_id"],
            "subject": objective["subject"],
            "domain": objective["domain"],
            "score": round(random.uniform(1.0, 9.0), 1),
            "assessment_date": assessment_date.isoformat(),
            "assessment_period": period,
            "learning_objective_id": objective["objective_id"],
            "notes": fake.sentence() if random.random() < 0.3 else "",
        })
    return rows


def main():
    print("Generating synthetic Teaching Strategies data...")
    print()

    schools = generate_schools()
    write_csv("schools.csv", schools)

    educators = generate_educators(schools)
    write_csv("educators.csv", educators)

    classrooms = generate_classrooms(schools, educators)
    write_csv("classrooms.csv", classrooms)

    students = generate_students(schools, classrooms)
    write_csv("students.csv", students)

    learning_objectives = generate_learning_objectives()
    write_csv("learning_objectives.csv", learning_objectives)

    assessments = generate_assessments(students, educators, learning_objectives)
    write_csv("assessments.csv", assessments)

    print()
    print("Done! CSV files written to:", DATA_DIR)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the generator and verify output**

```bash
cd lakebase-terraform && pip install faker && python scripts/generate_data.py
```

Expected: 6 CSV files in `data/` with row counts printed.

- [ ] **Step 3: Verify CSV contents**

```bash
wc -l lakebase-terraform/data/*.csv
head -2 lakebase-terraform/data/students.csv
```

Expected: schools.csv ~51 lines (50 + header), students.csv ~1501, assessments.csv ~5001, etc.

- [ ] **Step 4: Commit**

```bash
git add lakebase-terraform/scripts/generate_data.py lakebase-terraform/data/
git commit -m "feat: add synthetic data generator — 6 education domain entities"
```

---

### Task 5: Pipeline Module (Phase 3)

**Files:**
- Create: `lakebase-terraform/modules/pipeline/main.tf`
- Create: `lakebase-terraform/modules/pipeline/variables.tf`
- Create: `lakebase-terraform/modules/pipeline/outputs.tf`
- Create: `lakebase-terraform/modules/pipeline/notebooks/teaching_strategies_pipeline.py`

- [ ] **Step 1: Create the SDP notebook**

Write `lakebase-terraform/modules/pipeline/notebooks/teaching_strategies_pipeline.py`:

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # Teaching Strategies — Bronze / Silver / Gold Pipeline
# MAGIC Spark Declarative Pipeline processing education domain data.

# COMMAND ----------

import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import DateType, DoubleType, IntegerType

VOLUME_PATH = "/Volumes/teaching_strategies/bronze/raw_data"

ENTITIES = ["schools", "students", "educators", "classrooms", "assessments", "learning_objectives"]

# ---------- BRONZE ----------

@dlt.table(
    name="bronze_schools",
    comment="Raw schools data",
    table_properties={"quality": "bronze"},
)
def bronze_schools():
    return (
        spark.read.format("csv")
        .option("header", "true")
        .option("inferSchema", "true")
        .load(f"{VOLUME_PATH}/schools.csv")
        .withColumn("_ingested_at", F.current_timestamp())
        .withColumn("_source_file", F.input_file_name())
    )


@dlt.table(
    name="bronze_educators",
    comment="Raw educators data",
    table_properties={"quality": "bronze"},
)
def bronze_educators():
    return (
        spark.read.format("csv")
        .option("header", "true")
        .option("inferSchema", "true")
        .load(f"{VOLUME_PATH}/educators.csv")
        .withColumn("_ingested_at", F.current_timestamp())
        .withColumn("_source_file", F.input_file_name())
    )


@dlt.table(
    name="bronze_classrooms",
    comment="Raw classrooms data",
    table_properties={"quality": "bronze"},
)
def bronze_classrooms():
    return (
        spark.read.format("csv")
        .option("header", "true")
        .option("inferSchema", "true")
        .load(f"{VOLUME_PATH}/classrooms.csv")
        .withColumn("_ingested_at", F.current_timestamp())
        .withColumn("_source_file", F.input_file_name())
    )


@dlt.table(
    name="bronze_students",
    comment="Raw students data",
    table_properties={"quality": "bronze"},
)
def bronze_students():
    return (
        spark.read.format("csv")
        .option("header", "true")
        .option("inferSchema", "true")
        .load(f"{VOLUME_PATH}/students.csv")
        .withColumn("_ingested_at", F.current_timestamp())
        .withColumn("_source_file", F.input_file_name())
    )


@dlt.table(
    name="bronze_assessments",
    comment="Raw assessments data",
    table_properties={"quality": "bronze"},
)
def bronze_assessments():
    return (
        spark.read.format("csv")
        .option("header", "true")
        .option("inferSchema", "true")
        .load(f"{VOLUME_PATH}/assessments.csv")
        .withColumn("_ingested_at", F.current_timestamp())
        .withColumn("_source_file", F.input_file_name())
    )


@dlt.table(
    name="bronze_learning_objectives",
    comment="Raw learning objectives data",
    table_properties={"quality": "bronze"},
)
def bronze_learning_objectives():
    return (
        spark.read.format("csv")
        .option("header", "true")
        .option("inferSchema", "true")
        .load(f"{VOLUME_PATH}/learning_objectives.csv")
        .withColumn("_ingested_at", F.current_timestamp())
        .withColumn("_source_file", F.input_file_name())
    )


# ---------- SILVER ----------

@dlt.table(
    name="silver_schools",
    comment="Cleaned schools",
    table_properties={"quality": "silver"},
)
@dlt.expect_or_drop("valid_school_id", "school_id IS NOT NULL")
def silver_schools():
    return (
        dlt.read("bronze_schools")
        .dropDuplicates(["school_id"])
        .withColumn("student_capacity", F.col("student_capacity").cast(IntegerType()))
        .withColumn("_processed_at", F.current_timestamp())
    )


@dlt.table(
    name="silver_educators",
    comment="Cleaned educators",
    table_properties={"quality": "silver"},
)
@dlt.expect_or_drop("valid_educator_id", "educator_id IS NOT NULL")
def silver_educators():
    return (
        dlt.read("bronze_educators")
        .dropDuplicates(["educator_id"])
        .withColumn("hire_date", F.col("hire_date").cast(DateType()))
        .withColumn("_processed_at", F.current_timestamp())
    )


@dlt.table(
    name="silver_classrooms",
    comment="Cleaned classrooms",
    table_properties={"quality": "silver"},
)
@dlt.expect_or_drop("valid_classroom_id", "classroom_id IS NOT NULL")
def silver_classrooms():
    return (
        dlt.read("bronze_classrooms")
        .dropDuplicates(["classroom_id"])
        .withColumn("capacity", F.col("capacity").cast(IntegerType()))
        .withColumn("_processed_at", F.current_timestamp())
    )


@dlt.table(
    name="silver_students",
    comment="Cleaned students",
    table_properties={"quality": "silver"},
)
@dlt.expect_or_drop("valid_student_id", "student_id IS NOT NULL")
def silver_students():
    return (
        dlt.read("bronze_students")
        .dropDuplicates(["student_id"])
        .withColumn("date_of_birth", F.col("date_of_birth").cast(DateType()))
        .withColumn("enrollment_date", F.col("enrollment_date").cast(DateType()))
        .withColumn("_processed_at", F.current_timestamp())
    )


@dlt.table(
    name="silver_assessments",
    comment="Cleaned assessments",
    table_properties={"quality": "silver"},
)
@dlt.expect_or_drop("valid_assessment_id", "assessment_id IS NOT NULL")
def silver_assessments():
    return (
        dlt.read("bronze_assessments")
        .dropDuplicates(["assessment_id"])
        .withColumn("score", F.col("score").cast(DoubleType()))
        .withColumn("assessment_date", F.col("assessment_date").cast(DateType()))
        .withColumn("_processed_at", F.current_timestamp())
    )


@dlt.table(
    name="silver_learning_objectives",
    comment="Cleaned learning objectives",
    table_properties={"quality": "silver"},
)
@dlt.expect_or_drop("valid_objective_id", "objective_id IS NOT NULL")
def silver_learning_objectives():
    return (
        dlt.read("bronze_learning_objectives")
        .dropDuplicates(["objective_id"])
        .withColumn("_processed_at", F.current_timestamp())
    )


# ---------- GOLD ----------

@dlt.table(
    name="assessment_summary_by_classroom",
    comment="Assessment scores aggregated by classroom, subject, and period",
    table_properties={"quality": "gold"},
)
def gold_assessment_summary():
    classrooms = dlt.read("silver_classrooms")
    students = dlt.read("silver_students")
    assessments = dlt.read("silver_assessments")
    schools = dlt.read("silver_schools")

    return (
        assessments.alias("a")
        .join(students.alias("s"), F.col("a.student_id") == F.col("s.student_id"))
        .join(classrooms.alias("c"), F.col("s.classroom_id") == F.col("c.classroom_id"))
        .join(schools.alias("sc"), F.col("c.school_id") == F.col("sc.school_id"))
        .groupBy(
            F.col("c.classroom_id"),
            F.col("c.name").alias("classroom_name"),
            F.col("c.grade_level"),
            F.col("sc.school_id"),
            F.col("sc.name").alias("school_name"),
            F.col("a.subject"),
            F.col("a.assessment_period"),
        )
        .agg(
            F.countDistinct("a.student_id").alias("student_count"),
            F.round(F.avg("a.score"), 2).alias("avg_score"),
            F.min("a.score").alias("min_score"),
            F.max("a.score").alias("max_score"),
            F.round(F.stddev("a.score"), 2).alias("stddev_score"),
        )
    )


@dlt.table(
    name="educator_performance_metrics",
    comment="Student count and avg scores per educator",
    table_properties={"quality": "gold"},
)
def gold_educator_metrics():
    educators = dlt.read("silver_educators")
    classrooms = dlt.read("silver_classrooms")
    students = dlt.read("silver_students")
    assessments = dlt.read("silver_assessments")
    schools = dlt.read("silver_schools")

    return (
        educators.alias("e")
        .join(classrooms.alias("c"), F.col("e.educator_id") == F.col("c.educator_id"))
        .join(students.alias("s"), F.col("s.classroom_id") == F.col("c.classroom_id"))
        .join(assessments.alias("a"), F.col("a.student_id") == F.col("s.student_id"))
        .join(schools.alias("sc"), F.col("e.school_id") == F.col("sc.school_id"))
        .groupBy(
            F.col("e.educator_id"),
            F.col("e.first_name"),
            F.col("e.last_name"),
            F.col("e.role"),
            F.col("sc.name").alias("school_name"),
        )
        .agg(
            F.countDistinct("s.student_id").alias("student_count"),
            F.countDistinct("a.assessment_id").alias("assessment_count"),
            F.round(F.avg("a.score"), 2).alias("avg_student_score"),
            F.countDistinct("c.classroom_id").alias("classroom_count"),
        )
    )


@dlt.table(
    name="school_performance_overview",
    comment="School-level performance rollup",
    table_properties={"quality": "gold"},
)
def gold_school_performance():
    schools = dlt.read("silver_schools")
    classrooms = dlt.read("silver_classrooms")
    students = dlt.read("silver_students")
    educators = dlt.read("silver_educators")
    assessments = dlt.read("silver_assessments")

    return (
        schools.alias("sc")
        .join(classrooms.alias("c"), F.col("sc.school_id") == F.col("c.school_id"), "left")
        .join(students.alias("s"), F.col("s.school_id") == F.col("sc.school_id"), "left")
        .join(educators.alias("e"), F.col("e.school_id") == F.col("sc.school_id"), "left")
        .join(assessments.alias("a"), F.col("a.student_id") == F.col("s.student_id"), "left")
        .groupBy(
            F.col("sc.school_id"),
            F.col("sc.name"),
            F.col("sc.district"),
            F.col("sc.state"),
            F.col("sc.school_type"),
        )
        .agg(
            F.countDistinct("s.student_id").alias("total_students"),
            F.countDistinct("e.educator_id").alias("total_educators"),
            F.countDistinct("c.classroom_id").alias("total_classrooms"),
            F.round(F.avg("a.score"), 2).alias("avg_assessment_score"),
            F.countDistinct("a.assessment_id").alias("total_assessments"),
        )
    )
```

- [ ] **Step 2: Create modules/pipeline/variables.tf**

```hcl
variable "catalog_name" {
  description = "Unity Catalog catalog name for the pipeline"
  type        = string
}
```

- [ ] **Step 3: Create modules/pipeline/main.tf**

```hcl
terraform {
  required_providers {
    databricks = {
      source = "databricks/databricks"
    }
  }
}

resource "databricks_notebook" "pipeline" {
  path     = "/Shared/teaching_strategies/teaching_strategies_pipeline"
  language = "PYTHON"
  source   = "${path.module}/notebooks/teaching_strategies_pipeline.py"
}

resource "databricks_pipeline" "this" {
  name       = "teaching_strategies_pipeline"
  serverless = true
  catalog    = var.catalog_name

  library {
    notebook {
      path = databricks_notebook.pipeline.id
    }
  }
}
```

- [ ] **Step 4: Create modules/pipeline/outputs.tf**

```hcl
output "pipeline_id" {
  description = "ID of the SDP pipeline"
  value       = databricks_pipeline.this.id
}

output "pipeline_name" {
  description = "Name of the SDP pipeline"
  value       = databricks_pipeline.this.name
}
```

- [ ] **Step 5: Run terraform validate**

```bash
cd lakebase-terraform && terraform validate
```

Expected: "Success! The configuration is valid."

- [ ] **Step 6: Commit**

```bash
git add lakebase-terraform/modules/pipeline/
git commit -m "feat: add pipeline module — SDP notebook + Bronze/Silver/Gold"
```

---

### Task 6: Lakebase Module (Phase 4)

**Files:**
- Create: `lakebase-terraform/modules/lakebase/main.tf`
- Create: `lakebase-terraform/modules/lakebase/variables.tf`
- Create: `lakebase-terraform/modules/lakebase/outputs.tf`

- [ ] **Step 1: Create modules/lakebase/variables.tf**

```hcl
variable "project_id" {
  description = "Lakebase Autoscaling project ID"
  type        = string
}
```

- [ ] **Step 2: Create modules/lakebase/main.tf**

```hcl
terraform {
  required_providers {
    databricks = {
      source = "databricks/databricks"
    }
  }
}

# Lakebase Autoscaling Project
resource "databricks_postgres_project" "this" {
  project_id = var.project_id
  spec = {
    pg_version   = 17
    display_name = "Teaching Strategies Lakebase"
    default_endpoint_settings = {
      autoscaling_limit_min_cu = 0.5
      autoscaling_limit_max_cu = 4.0
      suspend_timeout_duration = "300s"
    }
  }
}

# Production branch (default, created with project — import or manage explicitly)
# The default production branch + endpoint are auto-created with the project.
# We manage additional branches here.

# Development branch
resource "databricks_postgres_branch" "development" {
  branch_id = "development"
  parent    = databricks_postgres_project.this.name
  spec = {
    ttl = "604800s" # 7 days
  }
}

# Development endpoint
resource "databricks_postgres_endpoint" "dev_primary" {
  endpoint_id = "ep-dev-primary"
  parent      = databricks_postgres_branch.development.name
  spec = {
    endpoint_type = "ENDPOINT_TYPE_READ_WRITE"
  }
}

# Data sources to read auto-created production resources
data "databricks_postgres_endpoints" "production" {
  parent = "${databricks_postgres_project.this.name}/branches/production"
}
```

- [ ] **Step 3: Create modules/lakebase/outputs.tf**

```hcl
output "project_name" {
  description = "Full resource name of the project"
  value       = databricks_postgres_project.this.name
}

output "project_uid" {
  description = "Project UID (for REST API calls)"
  value       = databricks_postgres_project.this.id
}

output "production_branch_uid" {
  description = "Production branch UID"
  value       = try(data.databricks_postgres_endpoints.production.endpoints[0].name, "")
}

output "dev_branch_name" {
  description = "Development branch resource name"
  value       = databricks_postgres_branch.development.name
}

output "production_endpoint_host" {
  description = "Production endpoint host"
  value       = try(data.databricks_postgres_endpoints.production.endpoints[0].status.hosts.host, "pending")
}

output "dev_endpoint_host" {
  description = "Development endpoint host"
  value       = try(databricks_postgres_endpoint.dev_primary.status.hosts.host, "pending")
}
```

- [ ] **Step 4: Run terraform validate**

```bash
cd lakebase-terraform && terraform validate
```

Expected: "Success! The configuration is valid."

- [ ] **Step 5: Commit**

```bash
git add lakebase-terraform/modules/lakebase/
git commit -m "feat: add lakebase module — project, dev branch, endpoints"
```

---

### Task 7: Sync Module + Shell Scripts (Phase 5)

**Files:**
- Create: `lakebase-terraform/modules/sync/main.tf`
- Create: `lakebase-terraform/modules/sync/variables.tf`
- Create: `lakebase-terraform/modules/sync/outputs.tf`
- Create: `lakebase-terraform/scripts/create_lakebase_catalog.sh`
- Create: `lakebase-terraform/scripts/create_synced_tables.sh`

- [ ] **Step 1: Create scripts/create_lakebase_catalog.sh**

```bash
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
```

- [ ] **Step 2: Create scripts/create_synced_tables.sh**

```bash
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
```

- [ ] **Step 3: Create modules/sync/variables.tf**

```hcl
variable "workspace_url" {
  description = "Workspace URL for REST API calls"
  type        = string
}

variable "catalog_name" {
  description = "Source UC catalog with Gold tables"
  type        = string
}

variable "lakebase_catalog_name" {
  description = "Name for the Lakebase Postgres catalog"
  type        = string
}

variable "lakebase_project_name" {
  description = "Full resource name of the Lakebase project"
  type        = string
}

variable "lakebase_project_uid" {
  description = "Project UID (bare ID) for synced tables API"
  type        = string
}

variable "lakebase_branch_id" {
  description = "Production branch UID (bare ID) for synced tables API"
  type        = string
}

variable "account_profile" {
  description = "Databricks CLI profile for authentication"
  type        = string
}
```

- [ ] **Step 4: Create modules/sync/main.tf**

```hcl
terraform {
  required_providers {
    databricks = {
      source = "databricks/databricks"
    }
  }
}

# Create the Lakebase Postgres catalog via REST API
resource "null_resource" "lakebase_catalog" {
  triggers = {
    workspace_url = var.workspace_url
    catalog_name  = var.lakebase_catalog_name
    project_name  = var.lakebase_project_name
    profile       = var.account_profile
  }

  provisioner "local-exec" {
    command = "bash ${path.module}/../../scripts/create_lakebase_catalog.sh '${var.workspace_url}' '${var.lakebase_catalog_name}' '${var.lakebase_project_name}' 'production' 'databricks_postgres' '${var.account_profile}'"
  }

  provisioner "local-exec" {
    when    = destroy
    command = "bash ${path.module}/../../scripts/create_lakebase_catalog.sh --delete '${self.triggers.workspace_url}' '${self.triggers.catalog_name}' '${self.triggers.profile}'"
  }
}

# Create synced tables via REST API
resource "null_resource" "synced_tables" {
  depends_on = [null_resource.lakebase_catalog]

  triggers = {
    workspace_url    = var.workspace_url
    lakebase_catalog = var.lakebase_catalog_name
    profile          = var.account_profile
  }

  provisioner "local-exec" {
    command = "bash ${path.module}/../../scripts/create_synced_tables.sh '${var.workspace_url}' '${var.catalog_name}' '${var.lakebase_catalog_name}' '${var.lakebase_project_uid}' '${var.lakebase_branch_id}' '${var.account_profile}'"
  }

  provisioner "local-exec" {
    when    = destroy
    command = "bash ${path.module}/../../scripts/create_synced_tables.sh --delete '${self.triggers.workspace_url}' '${self.triggers.lakebase_catalog}' '${self.triggers.profile}'"
  }
}
```

- [ ] **Step 5: Create modules/sync/outputs.tf**

```hcl
output "lakebase_catalog_created" {
  description = "Whether the Lakebase catalog was created"
  value       = true
  depends_on  = [null_resource.lakebase_catalog]
}

output "synced_tables_created" {
  description = "Whether synced tables were created"
  value       = true
  depends_on  = [null_resource.synced_tables]
}
```

- [ ] **Step 6: Make scripts executable**

```bash
chmod +x lakebase-terraform/scripts/create_lakebase_catalog.sh
chmod +x lakebase-terraform/scripts/create_synced_tables.sh
```

- [ ] **Step 7: Run terraform validate**

```bash
cd lakebase-terraform && terraform validate
```

Expected: "Success! The configuration is valid."

- [ ] **Step 8: Commit**

```bash
git add lakebase-terraform/modules/sync/ lakebase-terraform/scripts/create_lakebase_catalog.sh \
  lakebase-terraform/scripts/create_synced_tables.sh
git commit -m "feat: add sync module — Lakebase catalog + synced tables via REST API"
```

---

### Task 8: Permissions Module (Phase 6)

**Files:**
- Create: `lakebase-terraform/modules/permissions/main.tf`
- Create: `lakebase-terraform/modules/permissions/variables.tf`
- Create: `lakebase-terraform/modules/permissions/outputs.tf`
- Create: `lakebase-terraform/scripts/manage_lakebase_perms.sh`

- [ ] **Step 1: Create scripts/manage_lakebase_perms.sh**

```bash
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
```

- [ ] **Step 2: Create modules/permissions/variables.tf**

```hcl
variable "catalog_name" {
  description = "Unity Catalog catalog name"
  type        = string
}

variable "lakebase_catalog_name" {
  description = "Lakebase Postgres catalog name"
  type        = string
}

variable "service_principal_id" {
  description = "Service principal application ID"
  type        = string
}

variable "user_email" {
  description = "User email for permissions"
  type        = string
}

variable "group_name" {
  description = "Group name for Lakebase users"
  type        = string
}

variable "workspace_url" {
  description = "Workspace URL for REST API calls"
  type        = string
}

variable "lakebase_project_name" {
  description = "Full resource name of the Lakebase project"
  type        = string
}

variable "account_profile" {
  description = "Databricks CLI profile"
  type        = string
}
```

- [ ] **Step 3: Create modules/permissions/main.tf**

```hcl
terraform {
  required_providers {
    databricks = {
      source = "databricks/databricks"
    }
  }
}

# Create the lakebase-users group
resource "databricks_group" "lakebase_users" {
  display_name = var.group_name
}

# --- Unity Catalog Grants ---

# Catalog: teaching_strategies
resource "databricks_grants" "catalog" {
  catalog = var.catalog_name

  grant {
    principal  = var.service_principal_id
    privileges = ["ALL_PRIVILEGES"]
  }
  grant {
    principal  = var.user_email
    privileges = ["ALL_PRIVILEGES"]
  }
  grant {
    principal  = databricks_group.lakebase_users.display_name
    privileges = ["USE_CATALOG"]
  }
}

# Schema: bronze
resource "databricks_grants" "bronze" {
  schema = "${var.catalog_name}.bronze"

  grant {
    principal  = var.service_principal_id
    privileges = ["ALL_PRIVILEGES"]
  }
  grant {
    principal  = var.user_email
    privileges = ["ALL_PRIVILEGES"]
  }
  grant {
    principal  = databricks_group.lakebase_users.display_name
    privileges = ["USE_SCHEMA", "SELECT"]
  }
}

# Schema: silver
resource "databricks_grants" "silver" {
  schema = "${var.catalog_name}.silver"

  grant {
    principal  = var.service_principal_id
    privileges = ["ALL_PRIVILEGES"]
  }
  grant {
    principal  = var.user_email
    privileges = ["ALL_PRIVILEGES"]
  }
  grant {
    principal  = databricks_group.lakebase_users.display_name
    privileges = ["USE_SCHEMA", "SELECT"]
  }
}

# Schema: gold
resource "databricks_grants" "gold" {
  schema = "${var.catalog_name}.gold"

  grant {
    principal  = var.service_principal_id
    privileges = ["ALL_PRIVILEGES"]
  }
  grant {
    principal  = var.user_email
    privileges = ["ALL_PRIVILEGES"]
  }
  grant {
    principal  = databricks_group.lakebase_users.display_name
    privileges = ["USE_SCHEMA", "SELECT"]
  }
}

# Volume: raw_data
resource "databricks_grants" "volume" {
  volume = "${var.catalog_name}.bronze.raw_data"

  grant {
    principal  = var.service_principal_id
    privileges = ["ALL_PRIVILEGES"]
  }
  grant {
    principal  = var.user_email
    privileges = ["ALL_PRIVILEGES"]
  }
  grant {
    principal  = databricks_group.lakebase_users.display_name
    privileges = ["READ_VOLUME"]
  }
}

# Catalog: teaching_strategies_pg (Lakebase Postgres)
resource "databricks_grants" "lakebase_catalog" {
  catalog = var.lakebase_catalog_name

  grant {
    principal  = var.service_principal_id
    privileges = ["ALL_PRIVILEGES"]
  }
  grant {
    principal  = var.user_email
    privileges = ["ALL_PRIVILEGES"]
  }
  grant {
    principal  = databricks_group.lakebase_users.display_name
    privileges = ["USE_CATALOG"]
  }
}

# --- Lakebase Project Permissions (REST API) ---

resource "null_resource" "lakebase_project_perms" {
  triggers = {
    workspace_url = var.workspace_url
    project_name  = var.lakebase_project_name
  }

  provisioner "local-exec" {
    command = "bash ${path.module}/../../scripts/manage_lakebase_perms.sh '${var.workspace_url}' '${var.lakebase_project_name}' '${var.service_principal_id}' '${var.user_email}' '${var.group_name}' '${var.account_profile}'"
  }
}
```

- [ ] **Step 4: Create modules/permissions/outputs.tf**

```hcl
output "group_id" {
  description = "ID of the lakebase-users group"
  value       = databricks_group.lakebase_users.id
}

output "permissions_applied" {
  description = "Whether all permissions were applied"
  value       = true
  depends_on  = [null_resource.lakebase_project_perms]
}
```

- [ ] **Step 5: Make script executable**

```bash
chmod +x lakebase-terraform/scripts/manage_lakebase_perms.sh
```

- [ ] **Step 6: Run terraform validate**

```bash
cd lakebase-terraform && terraform validate
```

Expected: "Success! The configuration is valid."

- [ ] **Step 7: Commit**

```bash
git add lakebase-terraform/modules/permissions/ lakebase-terraform/scripts/manage_lakebase_perms.sh
git commit -m "feat: add permissions module — UC grants + Lakebase project ACLs"
```

---

### Task 9: README Documentation (Phase 7)

**Files:**
- Create: `lakebase-terraform/README.md`

- [ ] **Step 1: Write README.md**

Write `lakebase-terraform/README.md` with the following content:

````markdown
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
- **Python 3** with `faker` package (for synthetic data generation)
- Account ID: `0d26daa6-5e44-4c97-a497-ef015f91254a`
- Metastore: `metastore_aws_us_east_1` must exist in us-east-1

## Quick Start

```bash
# 1. Generate synthetic data
pip install faker
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

Six entities generated with Faker (1,000+ rows each):

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
````

- [ ] **Step 2: Commit**

```bash
git add lakebase-terraform/README.md
git commit -m "docs: add comprehensive README for lakebase-terraform project"
```

---

### Task 10: End-to-End Validation

- [ ] **Step 1: Verify full terraform validate passes**

```bash
cd lakebase-terraform && terraform validate
```

Expected: "Success! The configuration is valid."

- [ ] **Step 2: Run terraform plan (dry run)**

```bash
cd lakebase-terraform && terraform plan
```

Expected: Plan shows resources to create. Review for correctness. No errors.

- [ ] **Step 3: If plan succeeds, apply**

```bash
cd lakebase-terraform && terraform apply -auto-approve
```

Monitor output. The workspace creation will take 2-5 minutes. The `time_sleep` resource adds a 2-minute buffer.

- [ ] **Step 4: Verify outputs**

```bash
cd lakebase-terraform && terraform output
```

Expected: workspace_url, workspace_id, lakebase endpoints all populated.

- [ ] **Step 5: Verify pipeline runs**

```bash
databricks pipelines get --pipeline-id $(terraform output -raw pipeline_id) --profile one-env-account
```

- [ ] **Step 6: Final commit**

```bash
git add -A lakebase-terraform/
git commit -m "feat: complete lakebase-terraform deployment — all phases verified"
```
