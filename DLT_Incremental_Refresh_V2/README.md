# Pipeline Events Analyzer

A tool to analyze Databricks pipeline events and store them in Unity Catalog tables.

## Features

- Fetches all pipelines from your Databricks workspace
- Retrieves pipeline events with planning information
- Stores events in a Unity Catalog table using Delta format
- Partitions data by pipeline_id for efficient querying
- Includes timestamps and detailed event information

## Installation

### Using pip

```bash
pip install -r requirements.txt
```

### Using setup.py

```bash
pip install .
```

## Configuration

Before running the script, update the following constants in `scratch/pipeline_events_analysis.py`:

```python
CATALOG_NAME = "your_catalog_name"  # Change this to your catalog name
SCHEMA_NAME = "your_schema_name"    # Change this to your schema name
TABLE_NAME = "pipeline_events"      # You can keep this as is or change it
```

## Usage

1. Ensure you have proper Databricks authentication set up (either through environment variables or a credentials file)

2. Run the script:
```bash
python scratch/pipeline_events_analysis.py
```

3. Query the results using SQL:
```sql
SELECT * FROM your_catalog_name.your_schema_name.pipeline_events
WHERE pipeline_id = 'your_pipeline_id'
ORDER BY event_timestamp DESC;
```

## Table Schema

The pipeline events table has the following schema:

- `pipeline_id` (STRING, NOT NULL) - Partitioned column
- `pipeline_name` (STRING, NOT NULL)
- `event_timestamp` (TIMESTAMP, NOT NULL)
- `event_message` (STRING)
- `planning_details` (MAP<STRING, STRING>)
- `processed_timestamp` (TIMESTAMP, NOT NULL)

## Requirements

- Python 3.8 or higher
- Databricks workspace access
- Unity Catalog enabled
- Required Python packages (see requirements.txt)

## License

MIT License
