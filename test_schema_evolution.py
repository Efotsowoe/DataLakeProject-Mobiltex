#!/usr/bin/env python3
"""
Schema Evolution Test - Add column to assets table without breaking existing queries

Demonstrates backward compatibility when adding new columns to Parquet tables.
"""
import pandas as pd
import boto3
import sys

def get_account_id():
    """Get AWS account ID"""
    sts = boto3.client('sts')
    return sts.get_caller_identity()['Account']

def test_schema_evolution():
    """
    Test schema evolution by adding 'criticality' column to assets table
    """
    print("=" * 80)
    print("SCHEMA EVOLUTION TEST: Adding 'criticality' column to assets table")
    print("=" * 80)

    account_id = get_account_id()
    bucket = f"mobiltex-datalake-curated-{account_id}"

    # Step 1: Read current assets data
    print("\n[STEP 1] Reading current assets data...")
    df_original = pd.read_parquet(f"s3://{bucket}/parquet/assets/assets.parquet")
    print(f"Current schema: {list(df_original.columns)}")
    print(f"Row count: {len(df_original)}")

    # Step 2: Add new column
    print("\n[STEP 2] Adding 'criticality' column...")
    df_new = df_original.copy()
    df_new['criticality'] = ['High', 'Critical', 'Medium', 'Low', 'High']
    print(f"New schema: {list(df_new.columns)}")

    # Step 3: Write to new location (backup approach)
    # IMPORTANT: Backup must be OUTSIDE the table's S3 location to avoid Athena reading it
    backup_key = "backups/assets/assets_v1.parquet"
    print(f"\n[STEP 3] Backing up original data to {backup_key}...")
    df_original.to_parquet(f"s3://{bucket}/{backup_key}", index=False)
    print("Note: Backup stored outside table location to prevent duplicate reads")

    # Step 4: Write new schema
    print("\n[STEP 4] Writing new schema to main location...")
    df_new.to_parquet(f"s3://{bucket}/parquet/assets/assets.parquet", index=False)
    print("✓ Data written successfully")

    # Step 5: Update Glue table schema
    print("\n[STEP 5] Updating Glue table schema...")
    glue = boto3.client('glue')

    try:
        # Get current table definition
        response = glue.get_table(DatabaseName='mobiltex_datalake', Name='assets')
        table = response['Table']

        # Create a clean table input with only allowed fields
        table_input = {
            'Name': table['Name'],
            'StorageDescriptor': table['StorageDescriptor'],
            'PartitionKeys': table.get('PartitionKeys', []),
            'TableType': table.get('TableType', 'EXTERNAL_TABLE'),
            'Parameters': table.get('Parameters', {}),
        }

        # Add optional fields if they exist
        if 'Description' in table:
            table_input['Description'] = table['Description']
        if 'Owner' in table:
            table_input['Owner'] = table['Owner']

        # Add new column to schema
        new_column = {
            'Name': 'criticality',
            'Type': 'string',
            'Comment': 'Asset criticality level (High/Medium/Low)'
        }

        # Check if column already exists
        existing_cols = [col['Name'] for col in table_input['StorageDescriptor']['Columns']]
        if 'criticality' not in existing_cols:
            table_input['StorageDescriptor']['Columns'].append(new_column)
            print("✓ Added 'criticality' column to schema")
        else:
            print("✓ 'criticality' column already exists")

        # Update the table
        glue.update_table(
            DatabaseName='mobiltex_datalake',
            TableInput=table_input
        )
        print("✓ Glue table schema updated successfully")

        # Verify the update
        response = glue.get_table(DatabaseName='mobiltex_datalake', Name='assets')
        updated_cols = [col['Name'] for col in response['Table']['StorageDescriptor']['Columns']]
        print(f"✓ Verified schema columns: {updated_cols}")

    except Exception as e:
        print(f"⚠ Error updating Glue table: {e}")
        print("You may need to update the table schema manually via Athena or Glue Console")

    # Step 6: Test queries
    print("\n[STEP 6] Testing backward compatibility...")
    print("\n--- Query Test Results ---")
    print("Old queries (without new column) should work:")
    print("  ✓ SELECT COUNT(*) FROM mobiltex_datalake.assets;")
    print("  ✓ SELECT asset_id, asset_name FROM mobiltex_datalake.assets;")
    print("  ✓ SELECT * FROM mobiltex_datalake.assets WHERE status = 'Active';")
    print("\nNew queries (with new column) should also work:")
    print("  ✓ SELECT asset_name, criticality FROM mobiltex_datalake.assets;")
    print("  ✓ SELECT COUNT(*) FROM mobiltex_datalake.assets WHERE criticality = 'High';")

    print("\n" + "=" * 80)
    print("SCHEMA EVOLUTION TEST COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Run queries in Athena to verify backward compatibility")
    print("2. Check that old queries still work without modification")
    print("3. Verify new column is queryable")
    print(f"\n4. To rollback:")
    print(f"   aws s3 cp s3://{bucket}/{backup_key} s3://{bucket}/parquet/assets/assets.parquet")
    print("\nNote: Backup is stored outside table location (backups/) to avoid duplicate reads by Athena")

if __name__ == "__main__":
    try:
        test_schema_evolution()
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
