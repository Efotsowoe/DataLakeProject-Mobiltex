from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_glue as glue,
    aws_athena as athena,
    aws_iam as iam,
    aws_kms as kms,
    aws_logs as logs,
    RemovalPolicy,
    Duration,
    CfnOutput
)
from constructs import Construct
import aws_cdk as cdk

class DataLakeStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # KMS Key for encryption
        kms_key = kms.Key(
            self, "DataLakeKMSKey",
            description="KMS key for Data Lake encryption",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.DESTROY  # For demo only
        )

        # S3 Bucket - Raw Zone
        raw_bucket = s3.Bucket(
            self, "DataLakeRawBucket",
            bucket_name=f"mobiltex-datalake-raw-{self.account}",
            encryption=s3.BucketEncryption.KMS,
            encryption_key=kms_key,
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,  # For demo only
            auto_delete_objects=True,  # For demo only
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldRawData",
                    expiration=Duration.days(90)
                )
            ]
        )

        # S3 Bucket - Curated Zone
        curated_bucket = s3.Bucket(
            self, "DataLakeCuratedBucket",
            bucket_name=f"mobiltex-datalake-curated-{self.account}",
            encryption=s3.BucketEncryption.KMS,
            encryption_key=kms_key,
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # Glue Database
        glue_database = glue.CfnDatabase(
            self, "GlueDatabase",
            catalog_id=self.account,
            database_input=glue.CfnDatabase.DatabaseInputProperty(
                name="mobiltex_datalake",
                description="Mobiltex Data Lake - IoT sensor and asset management"
            )
        )

        # IAM Role for Glue Jobs
        glue_job_role = iam.Role(
            self, "GlueJobRole",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSGlueServiceRole")
            ]
        )

        # Grant S3 permissions to Glue
        raw_bucket.grant_read(glue_job_role)
        curated_bucket.grant_read_write(glue_job_role)
        kms_key.grant_encrypt_decrypt(glue_job_role)

        # CloudWatch Log Group for Glue
        glue_log_group = logs.LogGroup(
            self, "GlueJobLogGroup",
            log_group_name="/aws-glue/jobs/mobiltex-transform",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Glue Job for transformation (raw → curated)
        glue_job = glue.CfnJob(
            self, "TransformJob",
            name="mobiltex-raw-to-curated",
            role=glue_job_role.role_arn,
            command=glue.CfnJob.JobCommandProperty(
                name="glueetl",
                python_version="3",
                script_location=f"s3://{raw_bucket.bucket_name}/scripts/transform_job.py"
            ),
            default_arguments={
                "--job-language": "python",
                "--enable-metrics": "true",
                "--enable-continuous-cloudwatch-log": "true",
                "--enable-glue-datacatalog": "true",
                "--RAW_BUCKET": raw_bucket.bucket_name,
                "--CURATED_BUCKET": curated_bucket.bucket_name,
                "--DATABASE_NAME": glue_database.ref,
                "--enable-job-insights": "true"
            },
            glue_version="4.0",
            max_retries=1,
            timeout=60,
            number_of_workers=2,
            worker_type="G.1X"
        )
        glue_job.node.add_dependency(glue_database)

        # Create Glue Tables for curated zone - Using Iceberg format
        # Table 1: Assets
        assets_table = glue.CfnTable(
            self, "AssetsTable",
            catalog_id=self.account,
            database_name=glue_database.ref,
            table_input=glue.CfnTable.TableInputProperty(
                name="assets",
                description="Static asset registry - pipeline segments and stations",
                table_type="EXTERNAL_TABLE",
                parameters={
                    "classification": "parquet"
                },
                storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                    location=f"s3://{curated_bucket.bucket_name}/parquet/assets/",
                    input_format="org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
                    output_format="org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat",
                    serde_info=glue.CfnTable.SerdeInfoProperty(
                        serialization_library="org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
                    ),
                    columns=[
                        glue.CfnTable.ColumnProperty(name="asset_id", type="string"),
                        glue.CfnTable.ColumnProperty(name="asset_name", type="string"),
                        glue.CfnTable.ColumnProperty(name="asset_type", type="string"),
                        glue.CfnTable.ColumnProperty(name="location", type="string"),
                        glue.CfnTable.ColumnProperty(name="install_date", type="timestamp"),
                        glue.CfnTable.ColumnProperty(name="status", type="string"),
                        glue.CfnTable.ColumnProperty(name="last_updated", type="timestamp")
                    ]
                )
            )
        )
        assets_table.node.add_dependency(glue_database)

        # Table 2: Sensors
        sensors_table = glue.CfnTable(
            self, "SensorsTable",
            catalog_id=self.account,
            database_name=glue_database.ref,
            table_input=glue.CfnTable.TableInputProperty(
                name="sensors",
                description="Registered corrosion/pressure sensors",
                table_type="EXTERNAL_TABLE",
                parameters={
                    "classification": "parquet"
                },
                storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                    location=f"s3://{curated_bucket.bucket_name}/parquet/sensors/",
                    input_format="org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
                    output_format="org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat",
                    serde_info=glue.CfnTable.SerdeInfoProperty(
                        serialization_library="org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
                    ),
                    columns=[
                        glue.CfnTable.ColumnProperty(name="sensor_id", type="string"),
                        glue.CfnTable.ColumnProperty(name="asset_id", type="string"),
                        glue.CfnTable.ColumnProperty(name="sensor_model", type="string"),
                        glue.CfnTable.ColumnProperty(name="sensor_type", type="string"),
                        glue.CfnTable.ColumnProperty(name="install_date", type="timestamp"),
                        glue.CfnTable.ColumnProperty(name="status", type="string"),
                        glue.CfnTable.ColumnProperty(name="last_calibration", type="timestamp")
                    ]
                )
            )
        )
        sensors_table.node.add_dependency(glue_database)

        # Table 3: Readings (Time-series with partitioning)
        readings_table = glue.CfnTable(
            self, "ReadingsTable",
            catalog_id=self.account,
            database_name=glue_database.ref,
            table_input=glue.CfnTable.TableInputProperty(
                name="readings",
                description="Time-series telemetry data - high volume",
                table_type="EXTERNAL_TABLE",
                parameters={
                    "classification": "parquet"
                },
                partition_keys=[
                    glue.CfnTable.ColumnProperty(name="year", type="int"),
                    glue.CfnTable.ColumnProperty(name="month", type="int")
                ],
                storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                    location=f"s3://{curated_bucket.bucket_name}/parquet/readings/",
                    input_format="org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
                    output_format="org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat",
                    serde_info=glue.CfnTable.SerdeInfoProperty(
                        serialization_library="org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
                    ),
                    columns=[
                        glue.CfnTable.ColumnProperty(name="reading_id", type="string"),
                        glue.CfnTable.ColumnProperty(name="sensor_id", type="string"),
                        glue.CfnTable.ColumnProperty(name="timestamp", type="timestamp"),
                        glue.CfnTable.ColumnProperty(name="value", type="double"),
                        glue.CfnTable.ColumnProperty(name="unit", type="string"),
                        glue.CfnTable.ColumnProperty(name="quality", type="string")
                    ]
                )
            )
        )
        readings_table.node.add_dependency(glue_database)

        # Athena Workgroup
        athena_bucket = s3.Bucket(
            self, "AthenaResultsBucket",
            bucket_name=f"mobiltex-athena-results-{self.account}",
            encryption=s3.BucketEncryption.KMS,
            encryption_key=kms_key,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldQueryResults",
                    expiration=Duration.days(7)
                )
            ]
        )

        athena_workgroup = athena.CfnWorkGroup(
            self, "AthenaWorkgroup",
            name="mobiltex-analytics",
            description="Workgroup for querying curated data lake tables",
            recursive_delete_option=True,  # Allow deletion even if WorkGroup contains queries
            work_group_configuration=athena.CfnWorkGroup.WorkGroupConfigurationProperty(
                enforce_work_group_configuration=True,
                publish_cloud_watch_metrics_enabled=True,
                result_configuration=athena.CfnWorkGroup.ResultConfigurationProperty(
                    output_location=f"s3://{athena_bucket.bucket_name}/query-results/",
                    encryption_configuration=athena.CfnWorkGroup.EncryptionConfigurationProperty(
                        encryption_option="SSE_KMS",
                        kms_key=kms_key.key_arn
                    )
                )
            )
        )

        # Outputs
        CfnOutput(self, "RawBucketName", value=raw_bucket.bucket_name)
        CfnOutput(self, "CuratedBucketName", value=curated_bucket.bucket_name)
        CfnOutput(self, "GlueDatabaseName", value=glue_database.ref)
        CfnOutput(self, "AthenaWorkgroupName", value=athena_workgroup.name)
        CfnOutput(self, "KMSKeyId", value=kms_key.key_id)