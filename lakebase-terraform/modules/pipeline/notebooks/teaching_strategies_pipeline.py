# Databricks notebook source
# MAGIC %md
# MAGIC # Teaching Strategies — Bronze / Silver / Gold Pipeline
# MAGIC Spark Declarative Pipeline processing education domain data.

# COMMAND ----------

import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import DateType, DoubleType, IntegerType

VOLUME_PATH = "/Volumes/teaching_strategies/bronze/raw_data"

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
        .withColumn("_source_file", F.lit(VOLUME_PATH))
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
        .withColumn("_source_file", F.lit(VOLUME_PATH))
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
        .withColumn("_source_file", F.lit(VOLUME_PATH))
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
        .withColumn("_source_file", F.lit(VOLUME_PATH))
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
        .withColumn("_source_file", F.lit(VOLUME_PATH))
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
        .withColumn("_source_file", F.lit(VOLUME_PATH))
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
