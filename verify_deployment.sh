#!/bin/bash
# Deployment Verification Script
# Run this after cdk deploy and load_sample_data.py to verify everything works

set -e

echo "=========================================="
echo "Mobiltex Data Lake - Deployment Verification"
echo "=========================================="

# Get account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "AWS Account ID: $ACCOUNT_ID"

# Verify S3 buckets exist
echo ""
echo "[1/6] Verifying S3 buckets..."
RAW_BUCKET="mobiltex-datalake-raw-${ACCOUNT_ID}"
CURATED_BUCKET="mobiltex-datalake-curated-${ACCOUNT_ID}"
ATHENA_BUCKET="mobiltex-athena-results-${ACCOUNT_ID}"

aws s3 ls "s3://${RAW_BUCKET}/" > /dev/null && echo "  ✓ Raw bucket exists: ${RAW_BUCKET}"
aws s3 ls "s3://${CURATED_BUCKET}/" > /dev/null && echo "  ✓ Curated bucket exists: ${CURATED_BUCKET}"
aws s3 ls "s3://${ATHENA_BUCKET}/" > /dev/null && echo "  ✓ Athena results bucket exists: ${ATHENA_BUCKET}"

# Verify Glue database
echo ""
echo "[2/6] Verifying Glue database..."
aws glue get-database --name mobiltex_datalake > /dev/null && echo "  ✓ Database 'mobiltex_datalake' exists"

# Verify Glue tables
echo ""
echo "[3/6] Verifying Glue tables..."
aws glue get-table --database-name mobiltex_datalake --name assets > /dev/null && echo "  ✓ Table 'assets' exists"
aws glue get-table --database-name mobiltex_datalake --name sensors > /dev/null && echo "  ✓ Table 'sensors' exists"
aws glue get-table --database-name mobiltex_datalake --name readings > /dev/null && echo "  ✓ Table 'readings' exists"

# Verify data files in curated zone
echo ""
echo "[4/6] Verifying data files..."
FILE_COUNT=$(aws s3 ls "s3://${CURATED_BUCKET}/parquet/" --recursive | wc -l)
if [ "$FILE_COUNT" -ge 3 ]; then
    echo "  ✓ Found $FILE_COUNT data files in curated zone"
    aws s3 ls "s3://${CURATED_BUCKET}/parquet/" --recursive | sed 's/^/    /'
else
    echo "  ⚠ Warning: Only $FILE_COUNT files found. Run 'python3 load_sample_data.py' to load data."
fi

# Verify Athena workgroup
echo ""
echo "[5/6] Verifying Athena workgroup..."
aws athena get-work-group --work-group mobiltex-analytics > /dev/null && echo "  ✓ Workgroup 'mobiltex-analytics' exists"

# Check partition discovery for readings table
echo ""
echo "[6/6] Checking partitions for readings table..."
PARTITION_COUNT=$(aws glue get-partitions --database-name mobiltex_datalake --table-name readings --output json | jq '.Partitions | length')
if [ "$PARTITION_COUNT" -eq "0" ]; then
    echo "  ⚠ No partitions found. Running MSCK REPAIR TABLE..."

    # Run MSCK REPAIR TABLE
    QUERY_ID=$(aws athena start-query-execution \
        --query-string "MSCK REPAIR TABLE mobiltex_datalake.readings;" \
        --result-configuration "OutputLocation=s3://${ATHENA_BUCKET}/query-results/" \
        --work-group mobiltex-analytics \
        --query QueryExecutionId --output text)

    echo "  ⏳ Waiting for partition discovery (Query ID: $QUERY_ID)..."
    sleep 5

    # Check again
    PARTITION_COUNT=$(aws glue get-partitions --database-name mobiltex_datalake --table-name readings --output json | jq '.Partitions | length')
    echo "  ✓ Discovered $PARTITION_COUNT partition(s)"
else
    echo "  ✓ Found $PARTITION_COUNT partition(s)"
fi

# Summary
echo ""
echo "=========================================="
echo "Verification Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Open AWS Console → Athena → Query Editor"
echo "2. Select workgroup: mobiltex-analytics"
echo "3. Run test queries:"
echo ""
echo "   SELECT COUNT(*) FROM mobiltex_datalake.assets;    -- Expected: 5"
echo "   SELECT COUNT(*) FROM mobiltex_datalake.sensors;   -- Expected: 6"
echo "   SELECT COUNT(*) FROM mobiltex_datalake.readings;  -- Expected: 10"
echo ""
echo "4. Test schema evolution:"
echo "   python3 test_schema_evolution.py"
echo ""
