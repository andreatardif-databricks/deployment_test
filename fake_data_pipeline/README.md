# Fake Data Pipeline (Bronze → Silver → Gold)

Databricks Asset Bundle project: generates fake customer order data, runs a bronze/silver/gold pipeline in Unity Catalog, and sends HTML email notifications—separate emails for success vs failure based on a condition task.

## Project structure

```
fake_data_pipeline/
├── databricks.yml              # Bundle root config (workspace, variables, targets)
├── resources/
│   └── jobs.yml                # Job: run_pipeline → check_status → success or failure notification
├── src/
│   ├── fake_data_pipeline.ipynb      # Bronze → Silver → Gold; sets job_status for branching
│   ├── notification_webhook_success.ipynb  # Email on success (metrics, task summary)
│   ├── notification_webhook_failure.ipynb   # Email on failure (error, task summary)
│   └── notification_webhook.ipynb   # Legacy single-path notification (optional)
└── README.md
```

## Features

- **Serverless compute** — no cluster to manage
- **Bronze**: raw fake orders (Faker) → `{catalog}.bronze.orders`
- **Silver**: cleaned, deduplicated, no cancelled → `{catalog}.silver.orders_clean`
- **Gold**: revenue by category/state/date + `pipeline_run_metrics` for run history
- **Conditional notifications**: pipeline sets `job_status` via `dbutils.jobs.taskValues.set`; a condition task branches to **success** or **failure** notification; each sends an HTML email (run URL, task summary; success includes metrics vs previous run)

## Job flow

1. **run_pipeline** — Runs `fake_data_pipeline.ipynb`; on success, last cell sets `dbutils.jobs.taskValues.set("job_status", "success")`.
2. **check_status** — Condition task: `job_status == "success"` (EQUAL_TO).
3. **send_notification_success** — Runs when condition is true; sends success email.
4. **send_notification_failure** — Runs when condition is false (pipeline failed or did not set status); sends failure email.

## Prerequisites

- Databricks CLI (`pip install databricks-cli` or `brew install databricks/tap/databricks`)
- Authenticate: `databricks configure --token`
- Unity Catalog enabled; default catalog in the job is `andrea_tardif` (edit in `resources/jobs.yml` if needed)
- A Databricks **secret scope** with SMTP credentials (see below)

## Variables (databricks.yml)

Set these when deploying or in your environment:

| Variable           | Description                          |
|--------------------|--------------------------------------|
| `workspace_host`   | Databricks workspace URL (required)  |
| `alert_recipient`  | Email address for alerts (optional; also via env `ALERT_RECIPIENT`) |

## Email: SMTP and secret scope

Notifications use **plain SMTP**. Sensitive values are read from a **Databricks secret scope** (no SMTP credentials in code or env).

### Secret scope (required)

Create a secret scope and store SMTP settings. The notebooks default to scope name **`smtp`** (override with env `SECRET_SCOPE` if you use another name).

| Secret key     | Description                    |
|----------------|--------------------------------|
| `SMTP_HOST`    | e.g. `smtp.gmail.com`          |
| `SMTP_PORT`    | e.g. `587`                     |
| `SMTP_PASSWORD`| App password or SMTP password  |

```bash
# Create scope (e.g. name "smtp")
databricks secrets create-scope --scope smtp

# Store SMTP values (you'll be prompted for the secret value)
databricks secrets put --scope smtp --key SMTP_HOST
databricks secrets put --scope smtp --key SMTP_PORT
databricks secrets put --scope smtp --key SMTP_PASSWORD
```

Ensure the job run (or the serverless environment) has **read permission** on the scope.

### Environment (optional)

| Env var          | Description |
|------------------|-------------|
| `SMTP_USER`      | Sender email (default in notebook if unset) |
| `ALERT_RECIPIENT`| Recipient for notification emails |
| `SECRET_SCOPE`   | Secret scope name if not `smtp` |
| `CATALOG`        | Unity Catalog catalog name (e.g. for metrics table) |

## Deploy and run

```bash
# From repo root
cd fake_data_pipeline

# Validate bundle
databricks bundle validate

# Deploy to dev (set workspace_host)
databricks bundle deploy --target dev

# Run job once
databricks bundle run fake_data_pipeline_job --target dev

# Deploy to prod
databricks bundle deploy --target prod
```

## Tags

- `team`: data-engineering  
- `owner`: andrea_tardif  
