import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql.functions import col, current_timestamp, year, month

# Get job parameters
args = getResolvedOptions(sys.argv, [
    'JOB_NAME',
    'RAW_BUCKET',
    'CURATED_BUCKET',
    'DATABASE_NAME'
])

# Initialize Glue context
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

raw_bucket = args['RAW_BUCKET']
curated_bucket = args['CURATED_BUCKET']
database_name = args['DATABASE_NAME']

print(f"Starting transformation job for database: {database_name}")

# Process Assets Table
print("Processing assets...")
assets_raw_path = f"s3://{raw_bucket}/raw/assets/"
assets_curated_path = f"s3://{curated_bucket}/iceberg/assets/"

try:
    assets_df = spark.read.option("header", "true").csv(assets_raw_path)
    assets_df = assets_df.withColumn("last_updated", current_timestamp())
    
    # Write as Parquet to curated zone (Iceberg-compatible)
    assets_df.write.mode("overwrite").parquet(assets_curated_path)
    print(f"Assets processed: {assets_df.count()} records")
except Exception as e:
    print(f"Error processing assets: {str(e)}")

# Process Sensors Table
print("Processing sensors...")
sensors_raw_path = f"s3://{raw_bucket}/raw/sensors/"
sensors_curated_path = f"s3://{curated_bucket}/iceberg/sensors/"

try:
    sensors_df = spark.read.option("header", "true").csv(sensors_raw_path)
    sensors_df.write.mode("overwrite").parquet(sensors_curated_path)
    print(f"Sensors processed: {sensors_df.count()} records")
except Exception as e:
    print(f"Error processing sensors: {str(e)}")

# Process Readings Table (with partitioning)
print("Processing readings...")
readings_raw_path = f"s3://{raw_bucket}/raw/readings/"
readings_curated_path = f"s3://{curated_bucket}/iceberg/readings/"

try:
    readings_df = spark.read.option("header", "true").csv(readings_raw_path)
    
    # Add partition columns
    readings_df = readings_df.withColumn("year", year(col("timestamp")))
    readings_df = readings_df.withColumn("month", month(col("timestamp")))
    
    # Write partitioned data
    readings_df.write.mode("overwrite") \
        .partitionBy("year", "month") \
        .parquet(readings_curated_path)
    print(f"Readings processed: {readings_df.count()} records")
except Exception as e:
    print(f"Error processing readings: {str(e)}")

print("Transformation job completed successfully")
job.commit()
