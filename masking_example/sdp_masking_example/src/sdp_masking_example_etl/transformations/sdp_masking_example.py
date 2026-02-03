from pyspark import pipelines as dp
from pyspark.sql.functions import col, sum, max as max_

@dp.materialized_view(
  name="emails_masked_mv",
  comment="Masked emails materialized view with row filtering and aggregation",
  cluster_by_auto = True,
  schema="""
    email_id BIGINT,
    customer_id INT,
    subject STRING,
    content STRING MASK andrea_tardif.bronze.mask_content,
    sentiment DOUBLE,
    received_date DATE,
    requested_amount DOUBLE,
    processed STRING
  """,
  row_filter="ROW FILTER andrea_tardif.bronze.unprocessed_filter ON (processed)")

def emails_masked_mv():
    emails = spark.read.table("andrea_tardif.bronze.emails")
    emails_grouped = emails.groupBy(
        "email_id", "customer_id", "subject", "content", "sentiment", "received_date", "processed"
    ).agg(
        sum(col("requested_amount")).alias("requested_amount")
    )
    return emails_grouped

@dp.table(
  name="emails_masked_table",
  comment="Masked emails table with row filtering",
  schema="""
    email_id BIGINT,
    customer_id INT,
    subject STRING,
    content STRING MASK andrea_tardif.bronze.mask_content,
    sentiment DOUBLE,
    received_date DATE,
    requested_amount DOUBLE,
    processed STRING
  """,
  row_filter="ROW FILTER andrea_tardif.bronze.unprocessed_filter ON (processed)")

def emails_masked_table():
    return spark.read.table("andrea_tardif.bronze.emails")