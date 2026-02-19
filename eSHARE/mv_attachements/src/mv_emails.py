import pyspark.sql.functions as F
from pyspark import pipelines as dp
from pyspark.sql.types import (
    BooleanType,
    DateType,
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)


mv_attachments_sits_schema = StructType(
    [
        StructField("attachment_id", StringType()),
        StructField("attachment_unique_id", StringType()),
        StructField("email_unique_id", StringType(), False),
        StructField("message_id", StringType()),
        StructField("user_email", StringType()),
        StructField("drive_item_unique_id", StringType()),
        StructField("attachment_name", StringType()),
        StructField("attachment_type", StringType()),
        StructField("reference_type", StringType()),
        StructField("share_type", StringType()),
        StructField("file_extension", StringType()),
        StructField("content_type", StringType()),
        StructField("mime_type", StringType()),
        StructField("size", LongType()),
        StructField("size_display", StringType()),
        StructField("is_inline", BooleanType()),
        StructField("last_modified_date_time", TimestampType()),
        StructField("drive_id", StringType()),
        StructField("site_id", StringType()),
        StructField("sensitivity_label_display_name", StringType()),
        StructField("sensitivity_label_id", StringType()),
        StructField("sensitivity_label_protection_enabled", BooleanType()),
        StructField("rls_org_key", StringType(), False),
        StructField("cloud_storage_organization_id", StringType()),
        StructField("sit_id", StringType()),
        StructField("sit_name", StringType()),
        StructField("hit_id", StringType()),
        StructField("hit_rank", IntegerType()),
        StructField("sit_summary", StringType()),
        StructField("classification_type", StringType()),
        StructField("classification_last_scan", TimestampType()),
    ]
)

mv_emails_schema = StructType(
    [
        StructField("unique_email_id", StringType(), False),
        StructField("email_id", StringType()),
        StructField("cloud_storage_organization_id", StringType()),
        StructField("rls_org_key", StringType(), False),
        StructField("user_email", StringType()),
        StructField("created_date_time", TimestampType()),
        StructField("created_date", DateType()),
        StructField("last_modified_date_time", TimestampType()),
        StructField("last_modified_date", DateType()),
        StructField("received_date_time", TimestampType()),
        StructField("received_date", DateType()),
        StructField("sent_date_time", TimestampType()),
        StructField("sent_date", DateType()),
        StructField("has_attachments", BooleanType()),
        StructField("internet_message_id", StringType()),
        StructField("subject", StringType()),
        StructField("importance", StringType()),
        StructField("parent_folder_id", StringType()),
        StructField("conversation_id", StringType()),
        StructField("is_read", BooleanType()),
        StructField("is_draft", BooleanType()),
        StructField("web_link", StringType()),
        StructField("inference_classification", StringType()),
        StructField("flag_status", StringType()),
        StructField("email_sensitivity_label_id", StringType()),
        StructField("email_sensitivity_label_name", StringType()),
        StructField("email_category", StringType()),
        StructField("email_category_label", StringType()),
        StructField("email_odata_type", StringType()),
        StructField("sender_name", StringType()),
        StructField("sender_address", StringType()),
        StructField("from_name", StringType()),
        StructField("from_address", StringType()),
        StructField("sender_address_domain", StringType()),
        StructField("sender_address_domain_is_external", BooleanType()),
        StructField("sender_address_domain_is_consumer", BooleanType()),
        StructField("from_address_domain", StringType()),
        StructField("from_address_domain_is_external", BooleanType()),
        StructField("from_address_domain_is_consumer", BooleanType()),
        StructField("recipient_count", LongType()),
        StructField("to_count", LongType()),
        StructField("cc_count", LongType()),
        StructField("bcc_count", LongType()),
        StructField("reply_to_count", LongType()),
        StructField("external_recipient_count", LongType()),
        StructField("has_external_recipient", BooleanType()),
        StructField("has_consumer_recipient", BooleanType()),
        StructField("attachment_count", LongType()),
        StructField("attachment_size", LongType()),
        StructField("attachment_size_display", StringType()),
    ]
)


organizations = ["eshareitar", "bancnow"]


for org in organizations:

    @dp.materialized_view(
        name=f"main.databricks_test.silver_{org}_mv_attachments_sits",
        comment="Aggregated view of tenant scan attachments-sits for Power BI reporting",
        table_properties={
            "quality": "silver",
            "pipelines.autoOptimize.managed": "true",
            "delta.enableChangeDataFeed": "true",
            "mv.owner": "analytics-team",
            "mv.domain": "tenant-scan",
            "mv.version": "1.0.0",
            "expectations": """
            {
              "valid_email_and_org": {
                "expression": "email_unique_id IS NOT NULL AND rls_org_key IS NOT NULL",
                "action": "drop"
              }
            }
            """,
        },
        cluster_by_auto=True,
        cluster_by=["email_unique_id", "rls_org_key"],
        schema=mv_attachments_sits_schema,
    )
    def aggragate_attachments_sits(org=org):
        """
        Join email attachments with SITs and compute derived columns.
        """
        email_attachments = spark.read.table("main.m365.email_attachments").repartition(
            "drive_item_unique_id"
        )
        sits = spark.read.table("main.m365.sits").repartition("drive_item_unique_id")

        attachment_sits_df = (
            email_attachments.alias("a")
            .join(
                sits.alias("s"),
                F.col("a.drive_item_unique_id") == F.col("s.drive_item_unique_id"),
                "left",
            )
            .select(
                F.col("a.attachment_id"),
                F.col("a.attachment_unique_id"),
                F.col("a.email_unique_id"),
                F.col("a.message_id"),
                F.col("a.user_email"),
                F.col("a.drive_item_unique_id"),
                F.col("a.attachment_name"),
                F.col("a.attachment_type"),
                F.col("a.reference_type"),
                F.when(F.col("a.attachment_type").isin("file", "item"), "Attachment")
                .when(
                    (F.col("a.attachment_type") == "reference")
                    & (F.col("a.reference_type") == "file"),
                    "M365 File Link",
                )
                .when(
                    (F.col("a.attachment_type") == "reference")
                    & (F.col("a.reference_type") == "folder"),
                    "M365 Folder Link",
                )
                .alias("share_type"),
                F.col("a.file_extension"),
                F.col("a.content_type"),
                F.col("a.mime_type"),
                F.col("a.size"),
                F.when((F.col("a.size").isNull()) | (F.col("a.size") == 0), "-")
                .when(
                    F.col("a.size") >= 1073741824,
                    F.concat(F.round(F.col("a.size") / 1073741824.0, 2), F.lit(" GB")),
                )
                .when(
                    F.col("a.size") >= 1048576,
                    F.concat(F.round(F.col("a.size") / 1048576.0, 2), F.lit(" MB")),
                )
                .when(
                    F.col("a.size") >= 1024,
                    F.concat(F.round(F.col("a.size") / 1024.0, 2), F.lit(" KB")),
                )
                .otherwise(F.concat(F.col("a.size"), F.lit(" B")))
                .alias("size_display"),
                F.col("a.is_inline"),
                F.col("a.last_modified_date_time"),
                F.col("a.drive_id"),
                F.col("a.site_id"),
                F.col("a.sensitivity_label_display_name"),
                F.col("a.sensitivity_label_id"),
                F.col("a.sensitivity_label_protection_enabled"),
                F.col("a.rls_org_key"),
                F.col("a.cloud_storage_organization_id"),
                F.col("s.sit_id"),
                F.col("s.sit_name"),
                F.col("s.hit_id"),
                F.col("s.hit_rank"),
                F.col("s.summary").alias("sit_summary"),
                F.col("s.classification_type"),
                F.col("s.classification_last_scan"),
            )
        )
        return attachment_sits_df

    @dp.materialized_view(
        name=f"main.databricks_test.gold_{org}_mv_emails",
        comment="Aggregated view of tenant scan emails for Power BI reporting",
        table_properties={
            "quality": "gold",
            "pipelines.autoOptimize.managed": "true",
            "delta.enableChangeDataFeed": "true",
            "mv.owner": "analytics-team",
            "mv.domain": "tenant-scan",
            "mv.version": "1.0.0",
            "expectations": """
            {
              "valid_email_and_org": {
                "expression": "unique_email_id IS NOT NULL AND rls_org_key IS NOT NULL",
                "action": "drop"
              }
            }
            """,
        },
        cluster_by_auto=True,
        cluster_by=["unique_email_id", "rls_org_key"],
        schema=mv_emails_schema,
    )
    def aggregate_emails(org=org):
        emails = spark.read.table("main.m365.emails").alias("e")
        attachment_sits = spark.read.table(
            f"main.databricks_test.silver_{org}_mv_attachments_sits"
        )

        attachment_aggregates = (
            attachment_sits.groupBy("email_unique_id", "attachment_unique_id", "rls_org_key")
            .agg(F.max("size").alias("max_size"))
            .groupBy("email_unique_id", "rls_org_key")
            .agg(
                F.countDistinct("attachment_unique_id").alias("attachment_count"),
                F.coalesce(F.sum("max_size"), F.lit(0)).alias("attachment_size"),
            )
            .alias("a")
        )

        is_recipient = F.col("recipient_type").isin("to", "cc", "bcc")
        is_external = F.col("recipient_address_domain_is_external") == True
        is_consumer = F.col("recipient_address_domain_is_consumer") == True

        emails_agg = (
            emails.join(
                F.broadcast(attachment_aggregates),
                (F.col("e.unique_email_id") == F.col("a.email_unique_id"))
                & (F.col("e.rls_org_key") == F.col("a.rls_org_key")),
                "left",
            )
            .drop("a.email_unique_id")
            .drop("a.rls_org_key")
            .groupBy("e.unique_email_id", "e.rls_org_key")
            .agg(
                F.first("email_id", True).alias("email_id"),
                F.first("cloud_storage_organization_id", True).alias(
                    "cloud_storage_organization_id"
                ),
                F.first("user_email", True).alias("user_email"),
                F.first("created_date_time", True).alias("created_date_time"),
                F.first("last_modified_date_time", True).alias("last_modified_date_time"),
                F.first("received_date_time", True).alias("received_date_time"),
                F.first("sent_date_time", True).alias("sent_date_time"),
                F.first("has_attachments", True).alias("has_attachments"),
                F.first("internet_message_id", True).alias("internet_message_id"),
                F.first("subject", True).alias("subject"),
                F.first("importance", True).alias("importance"),
                F.first("parent_folder_id", True).alias("parent_folder_id"),
                F.first("conversation_id", True).alias("conversation_id"),
                F.first("is_read", True).alias("is_read"),
                F.first("is_draft", True).alias("is_draft"),
                F.first("web_link", True).alias("web_link"),
                F.first("inference_classification", True).alias("inference_classification"),
                F.first("flag_status", True).alias("flag_status"),
                F.first("email_sensitivity_label_id", True).alias("email_sensitivity_label_id"),
                F.first("email_sensitivity_label_name", True).alias(
                    "email_sensitivity_label_name"
                ),
                F.first("email_category", True).alias("email_category"),
                F.first("email_odata_type", True).alias("email_odata_type"),

                F.first("sender_name", True).alias("sender_name"),
                F.first("sender_address", True).alias("sender_address"),
                F.first("from_name", True).alias("from_name"),
                F.first("from_address", True).alias("from_address"),
                F.first("sender_address_domain", True).alias("sender_address_domain"),
                F.first("sender_address_domain_is_external", True).alias(
                    "sender_address_domain_is_external"
                ),
                F.first("sender_address_domain_is_consumer", True).alias(
                    "sender_address_domain_is_consumer"
                ),
                F.first("from_address_domain", True).alias("from_address_domain"),
                F.first("from_address_domain_is_external", True).alias(
                    "from_address_domain_is_external"
                ),
                F.first("from_address_domain_is_consumer", True).alias(
                    "from_address_domain_is_consumer"
                ),

                F.sum(F.when(is_recipient, 1).otherwise(0)).alias("recipient_count"),
                F.sum(F.when(F.col("recipient_type") == "to", 1).otherwise(0)).alias(
                    "to_count"
                ),
                F.sum(F.when(F.col("recipient_type") == "cc", 1).otherwise(0)).alias(
                    "cc_count"
                ),
                F.sum(F.when(F.col("recipient_type") == "bcc", 1).otherwise(0)).alias(
                    "bcc_count"
                ),
                F.sum(F.when(F.col("recipient_type") == "reply_to", 1).otherwise(0)).alias(
                    "reply_to_count"
                ),
                F.sum(F.when(is_recipient & is_external, 1).otherwise(0)).alias(
                    "external_recipient_count"
                ),
                F.max(F.when(is_recipient & is_external, 1).otherwise(0))
                .cast("boolean")
                .alias("has_external_recipient"),
                F.max(F.when(is_recipient & is_consumer, 1).otherwise(0))
                .cast("boolean")
                .alias("has_consumer_recipient"),

                F.coalesce(F.first("attachment_count", True), F.lit(0)).alias(
                    "attachment_count"
                ),
                F.coalesce(F.first("attachment_size", True), F.lit(0)).alias(
                    "attachment_size"
                ),
            )
        )


        mv_emails = (
            emails_agg.withColumn("created_date", F.to_date("created_date_time"))
            .withColumn("last_modified_date", F.to_date("last_modified_date_time"))
            .withColumn("received_date", F.to_date("received_date_time"))
            .withColumn("sent_date", F.to_date("sent_date_time"))
            .withColumn(
                "email_category_label",
                F.when(F.col("email_category") == "standard", "Standard Email")
                .when(F.col("email_category") == "event", "Event (Cal Invites)")
                .otherwise(F.col("email_category")),
            )
            .withColumn(
                "attachment_size_display",
                F.when(F.col("attachment_size") == 0, "-")
                .when(
                    F.col("attachment_size") >= 1073741824,
                    F.concat(
                        F.round(F.col("attachment_size") / 1073741824.0, 2),
                        F.lit(" GB"),
                    ),
                )
                .when(
                    F.col("attachment_size") >= 1048576,
                    F.concat(
                        F.round(F.col("attachment_size") / 1048576.0, 2), F.lit(" MB")
                    ),
                )
                .when(
                    F.col("attachment_size") >= 1024,
                    F.concat(
                        F.round(F.col("attachment_size") / 1024.0, 2), F.lit(" KB")
                    ),
                )
                .otherwise(F.concat(F.col("attachment_size"), F.lit(" B"))),
            )
        )

        return mv_emails
