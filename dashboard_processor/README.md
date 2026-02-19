# Dashboard Processor Bundle

This Databricks Asset Bundle (DAB) processes Lakeview dashboards by fetching active dashboard information in parallel and merging it with dashboard actions data.

## Overview

The bundle contains a job that:
1. Reads dashboard IDs from a `dashboards_actions` table
2. Uses ThreadPoolExecutor to fetch dashboard details in parallel (16 workers)
3. Filters for ACTIVE dashboards only
4. Merges the results with the original dashboard actions data
5. Saves the merged data to a Unity Catalog table

## Structure

```
dashboard_processor/
├── databricks.yml              # Main bundle configuration
├── resources/
│   └── dashboard_processing_job.yml  # Job definition
├── src/
│   └── process_dashboards.ipynb      # Main processing notebook
├── fixtures/                   # Test fixtures
└── tests/                      # Tests
```

## Prerequisites

1. A `dashboards_actions` table must exist in your catalog/schema with at least a `dashboard_id` column
2. Appropriate permissions to access Lakeview dashboards via the Databricks SDK
3. Unity Catalog catalog and schema created

## Configuration

The bundle uses the following variables (defined in `databricks.yml`):

- `catalog`: Unity Catalog catalog name (default: `andrea_tardif`)
- `schema`: Schema name (default: `bronze`)
- `table_name`: Output table name (default: `dashboards_merged`)
- `warehouse_id`: SQL warehouse ID for queries
- `env`: Environment name (dev/test/prod)

## Usage

### Validate the bundle

```bash
databricks bundle validate
```

### Deploy the bundle

For development:
```bash
databricks bundle deploy -t dev
```

For production:
```bash
databricks bundle deploy -t prod
```

### Run the job

```bash
databricks bundle run dashboard_processing_job -t dev
```

### Run with custom parameters

```bash
databricks bundle run dashboard_processing_job -t dev \
  --var catalog=my_catalog \
  --var schema=my_schema \
  --var table_name=my_table
```

## Job Parameters

The job accepts the following parameters:

- `catalog`: Target catalog for output table
- `schema`: Target schema for output table
- `table_name`: Name of the output table
- `env`: Environment identifier

These parameters are passed from the bundle configuration to the notebook and can be overridden at runtime.

## Output

The job creates a Delta table at `{catalog}.{schema}.{table_name}` with the following columns:
- All columns from `dashboards_actions`
- `display_name`: Dashboard display name (from Lakeview API)

The table is written with:
- Format: Delta
- Mode: Overwrite
- Schema evolution: Enabled

## Targets

### dev
- Mode: development
- Schedule: Daily at 8 AM (PAUSED by default)
- Output: `andrea_tardif.bronze.dashboards_merged`

### test
- Mode: production
- Schedule: Daily at 6 AM (PAUSED by default)
- Output: `andrea_tardif.silver.dashboards_merged`

### prod
- Mode: production
- Schedule: Daily at 4 AM (ACTIVE by default)
- Output: `andrea_tardif.silver.dashboards_merged`

## Cluster Configuration

The job uses a new cluster with:
- Spark version: 15.4.x-scala2.12
- Node type: i3.xlarge
- Workers: 2
- Timeout: 1 hour
- Max retries: 2

## Monitoring

The job sends email notifications to the current user on:
- Job failure
- Job success

## Troubleshooting

### Common Issues

1. **Table not found**: Ensure `dashboards_actions` table exists in the specified catalog/schema
2. **Permission errors**: Verify you have access to read dashboards via the Lakeview API
3. **Timeout errors**: Increase `timeout_seconds` in the job configuration if processing many dashboards

### Logs

Check job logs in the Databricks workspace:
- Navigate to Workflows > Jobs > dashboard_processing_job
- Click on a run to see detailed logs

## Development

To modify the processing logic:
1. Edit `src/process_dashboards.ipynb`
2. Deploy the updated bundle: `databricks bundle deploy -t dev`
3. Run the job to test: `databricks bundle run dashboard_processing_job -t dev`

## License

Internal use only
