#!/usr/bin/env python3
"""Create synced tables from Gold Delta tables to Lakebase Postgres using SDK."""

import sys
import time
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.database import (
    SyncedDatabaseTable,
    SyncedTableSpec,
    SyncedTableSchedulingPolicy,
)

PROFILE = "lakebase-terraform-ws"
PIPELINE_ID = "29bef5b3-96d9-44fa-aa63-6dae0db63df2"
CATALOG = "teaching_strategies"
LAKEBASE_CATALOG = "teaching_strategies_pg_new"

GOLD_TABLES = {
    "assessment_summary_by_classroom": ["classroom_id", "subject", "assessment_period"],
    "educator_performance_metrics": ["educator_id"],
    "school_performance_overview": ["school_id"],
}


def wait_for_pipeline(w, pipeline_id, timeout=600):
    """Wait for pipeline to complete."""
    print(f"Waiting for pipeline {pipeline_id} to complete...")
    start = time.time()
    while time.time() - start < timeout:
        pipeline = w.pipelines.get(pipeline_id=pipeline_id)
        state = pipeline.state
        print(f"  Pipeline state: {state}")
        if str(state) == "PipelineState.IDLE":
            # Check latest update
            latest = pipeline.latest_updates[0] if pipeline.latest_updates else None
            if latest:
                update = w.pipelines.get_update(pipeline_id=pipeline_id, update_id=latest.update_id)
                update_state = str(update.update.state)
                print(f"  Latest update state: {update_state}")
                if "COMPLETED" in update_state:
                    print("Pipeline completed successfully!")
                    return True
                elif "FAILED" in update_state:
                    print("Pipeline FAILED!")
                    return False
        time.sleep(15)
    print("Pipeline timed out!")
    return False


def create_synced_tables(w):
    """Create synced tables from Gold tables to Lakebase Postgres."""
    for table_name, pk_cols in GOLD_TABLES.items():
        source = f"{CATALOG}.gold.{table_name}"
        target = f"{LAKEBASE_CATALOG}.public.{table_name}_synced"

        print(f"\nCreating synced table: {target}")
        print(f"  Source: {source}")
        print(f"  Primary keys: {pk_cols}")

        try:
            result = w.database.create_synced_database_table(
                synced_table=SyncedDatabaseTable(
                    name=target,
                    logical_database_name="databricks_postgres",
                    spec=SyncedTableSpec(
                        source_table_full_name=source,
                        scheduling_policy=SyncedTableSchedulingPolicy.SNAPSHOT,
                        primary_key_columns=pk_cols,
                    ),
                )
            )
            print(f"  Created: {result.name}")
            print(f"  State: {result.unity_catalog_provisioning_state}")
        except Exception as e:
            print(f"  Error: {e}")


def main():
    w = WorkspaceClient(profile=PROFILE)

    # Step 1: Wait for pipeline
    if not wait_for_pipeline(w, PIPELINE_ID):
        print("\nPipeline did not complete. Fix pipeline errors before creating synced tables.")
        sys.exit(1)

    # Step 2: Create synced tables
    print("\n=== Creating Synced Tables ===")
    create_synced_tables(w)
    print("\nDone!")


if __name__ == "__main__":
    main()
