#!/usr/bin/env python3
"""
Load sample CSV data into the data lake as Parquet files
"""
import pandas as pd
import boto3
import sys
from datetime import datetime

def get_account_id():
    """Get AWS account ID"""
    sts = boto3.client('sts')
    return sts.get_caller_identity()['Account']

def load_assets(account_id):
    """Load assets.csv to S3 as Parquet"""
    print("Loading assets...")
    df = pd.read_csv('sample_data/assets.csv')

    # Add last_updated column
    df['last_updated'] = datetime.now()

    # Convert date column
    df['install_date'] = pd.to_datetime(df['install_date'])

    bucket = f"mobiltex-datalake-curated-{account_id}"
    key = "parquet/assets/assets.parquet"

    df.to_parquet(f"s3://{bucket}/{key}", index=False)
    print(f"✓ Uploaded {len(df)} assets to s3://{bucket}/{key}")

def load_sensors(account_id):
    """Load sensors.csv to S3 as Parquet"""
    print("Loading sensors...")
    df = pd.read_csv('sample_data/sensors.csv')

    # Convert date columns
    df['install_date'] = pd.to_datetime(df['install_date'])
    df['last_calibration'] = pd.to_datetime(df['last_calibration'])

    bucket = f"mobiltex-datalake-curated-{account_id}"
    key = "parquet/sensors/sensors.parquet"

    df.to_parquet(f"s3://{bucket}/{key}", index=False)
    print(f"✓ Uploaded {len(df)} sensors to s3://{bucket}/{key}")

def load_readings(account_id):
    """Load readings.csv to S3 as Parquet with partitioning"""
    print("Loading readings...")
    df = pd.read_csv('sample_data/readings.csv')

    # Convert timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Add partition columns
    df['year'] = df['timestamp'].dt.year
    df['month'] = df['timestamp'].dt.month

    bucket = f"mobiltex-datalake-curated-{account_id}"

    # Write partitioned by year/month
    for (year, month), group in df.groupby(['year', 'month']):
        # Drop partition columns from data (they're in the path)
        data = group.drop(['year', 'month'], axis=1)
        key = f"parquet/readings/year={year}/month={month}/readings.parquet"
        data.to_parquet(f"s3://{bucket}/{key}", index=False)
        print(f"✓ Uploaded {len(data)} readings to s3://{bucket}/{key}")

def main():
    try:
        account_id = get_account_id()
        print(f"AWS Account ID: {account_id}\n")

        load_assets(account_id)
        load_sensors(account_id)
        load_readings(account_id)

        print("\n✓ All sample data loaded successfully!")
        print("\nNext steps:")
        print("1. Run MSCK REPAIR TABLE in Athena for readings table:")
        print("   MSCK REPAIR TABLE mobiltex_datalake.readings;")
        print("2. Query your data:")
        print("   SELECT COUNT(*) FROM mobiltex_datalake.assets;")
        print("   SELECT COUNT(*) FROM mobiltex_datalake.sensors;")
        print("   SELECT COUNT(*) FROM mobiltex_datalake.readings;")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
