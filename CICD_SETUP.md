# GitHub Actions CI/CD Setup Guide

This guide walks you through setting up GitHub Actions for automated deployment of the Mobiltex Data Lake using OIDC authentication.

## Overview

The CI/CD pipeline uses **OpenID Connect (OIDC)** to authenticate with AWS, eliminating the need to store long-lived AWS credentials in GitHub Secrets. This is the recommended security best practice.

---

## Prerequisites

- AWS Account with administrator access
- GitHub repository for this project
- AWS CLI configured locally

---

## Step 1: Create OIDC Identity Provider in AWS

### 1.1 Via AWS Console

1. Navigate to **IAM** → **Identity providers** → **Add provider**
2. Configure the provider:
   - **Provider type**: OpenID Connect
   - **Provider URL**: `https://token.actions.githubusercontent.com`
   - **Audience**: `sts.amazonaws.com`
3. Click **Add provider**

### 1.2 Via AWS CLI

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

---

## Step 2: Create IAM Role for GitHub Actions

### 2.1 Create Trust Policy Document

Create a file named `github-actions-trust-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR-ACCOUNT-ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR-GITHUB-USERNAME/mobiltex-datalake-cdk:*"
        }
      }
    }
  ]
}
```

**Replace:**
- `YOUR-ACCOUNT-ID` with your AWS account ID (e.g., `123456789012`)
- `YOUR-GITHUB-USERNAME` with your GitHub username (e.g., `johnsonnuviadenu`)

### 2.2 Create the IAM Role

```bash
# Get your AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Update the trust policy file
sed -i "s/YOUR-ACCOUNT-ID/${ACCOUNT_ID}/g" github-actions-trust-policy.json
sed -i "s/YOUR-GITHUB-USERNAME/johnsonnuviadenu/g" github-actions-trust-policy.json

# Create the role
aws iam create-role \
  --role-name GithubActions \
  --assume-role-policy-document file://github-actions-trust-policy.json \
  --description "Role for GitHub Actions to deploy Mobiltex Data Lake"
```

### 2.3 Attach Permissions Policy

**Option A: Administrator Access (Development)**
```bash
aws iam attach-role-policy \
  --role-name GithubActions \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
```

**Option B: Least Privilege (Production)**

Create `github-actions-permissions-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:*",
        "s3:*",
        "glue:*",
        "athena:*",
        "iam:GetRole",
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PassRole",
        "kms:*",
        "logs:*",
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}
```

```bash
aws iam create-policy \
  --policy-name MobiltexDataLakeCDKPolicy \
  --policy-document file://github-actions-permissions-policy.json

aws iam attach-role-policy \
  --role-name GithubActions \
  --policy-arn arn:aws:iam::${ACCOUNT_ID}:policy/MobiltexDataLakeCDKPolicy
```

---

## Step 3: Configure GitHub Repository

### 3.1 Add Repository Secret

1. Navigate to your GitHub repository
2. Go to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add secret:
   - **Name**: `AWS_ACCOUNT`
   - **Value**: Your AWS account ID (e.g., `123456789012`)

### 3.2 Verify Workflow File Exists

Ensure `.github/workflows/deploy.yml` exists in your repository:

```bash
ls -la .github/workflows/deploy.yml
```

If not, commit and push the workflow file:

```bash
git add .github/workflows/deploy.yml
git commit -m "Add GitHub Actions CI/CD workflow"
git push origin main
```

---

## Step 4: Test the Deployment

### 4.1 Trigger Workflow

1. Navigate to your GitHub repository
2. Click **Actions** tab
3. Select **Deploy Mobiltex Data Lake** workflow
4. Click **Run workflow**
5. Select:
   - **Branch**: `main`
   - **CDK Action**: `deploy`
   - **Environment**: `dev`
6. Click **Run workflow**

### 4.2 Monitor Execution

Watch the workflow progress:
- ✅ Checkout code
- ✅ Configure AWS credentials (OIDC)
- ✅ Install dependencies
- ✅ CDK Bootstrap
- ✅ CDK Deploy
- ✅ Load sample data
- ✅ Repair partitions
- ✅ Verify deployment

### 4.3 View Deployment Summary

After successful deployment, check the workflow summary for:
- AWS Account ID
- Region
- Resources created
- Next steps with Athena queries

---

## Step 5: Verify Resources in AWS

```bash
# Get your account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# List S3 buckets
aws s3 ls | grep mobiltex

# List Glue tables
aws glue get-tables --database-name mobiltex_datalake --query 'TableList[*].Name'

# Check Athena workgroup
aws athena get-work-group --work-group mobiltex-analytics
```

---

## Step 6: Test Athena Queries

1. Open AWS Console → Athena
2. Select workgroup: `mobiltex-analytics`
3. Run queries:

```sql
SELECT COUNT(*) FROM mobiltex_datalake.assets;    -- Expected: 5
SELECT COUNT(*) FROM mobiltex_datalake.sensors;   -- Expected: 6
SELECT COUNT(*) FROM mobiltex_datalake.readings;  -- Expected: 10
```

---

## Step 7: Cleanup (Optional)

### 7.1 Via GitHub Actions

1. Go to Actions → Deploy Mobiltex Data Lake
2. Run workflow with action: `destroy`
3. Monitor destruction progress

**What happens during destroy:**
1. ✅ Empties all S3 buckets (raw, curated, athena-results)
2. ✅ Deletes all object versions (since versioning is enabled)
3. ✅ Removes all delete markers
4. ✅ Runs `cdk destroy --force --all`
5. ✅ Verifies buckets are deleted
6. ✅ Generates destruction summary

### 7.2 Via CLI

```bash
# Destroy the stack
cdk destroy --force

# Delete IAM role
aws iam detach-role-policy \
  --role-name GithubActions \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

aws iam delete-role --role-name GithubActions

# Delete OIDC provider
OIDC_ARN=$(aws iam list-open-id-connect-providers --query "OpenIDConnectProviderList[?contains(Arn, 'token.actions.githubusercontent.com')].Arn" --output text)
aws iam delete-open-id-connect-provider --open-id-connect-provider-arn $OIDC_ARN
```

---

## Troubleshooting

### Issue: "Error: Credentials could not be loaded"

**Cause**: OIDC trust policy mismatch or incorrect secret

**Solution**:
1. Verify `AWS_ACCOUNT` secret is set correctly
2. Check trust policy has correct GitHub repo path
3. Ensure OIDC provider exists in IAM

### Issue: "User is not authorized to perform: cloudformation:CreateStack"

**Cause**: IAM role lacks necessary permissions

**Solution**:
1. Attach `AdministratorAccess` policy for development
2. Or create custom policy with required permissions

### Issue: Workflow shows "Waiting for deployment"

**Cause**: CDK bootstrap may not be complete

**Solution**:
1. Check CloudFormation console for CDK bootstrap stack
2. Wait for bootstrap to complete
3. Re-run workflow

---

## Security Best Practices

✅ **Use OIDC instead of long-lived credentials**
- Temporary credentials via AssumeRoleWithWebIdentity
- Automatic credential rotation
- Reduced attack surface

✅ **Restrict GitHub repository access**
- Limit trust policy to specific repository: `repo:username/repo:*`
- Use branch restrictions if needed: `repo:username/repo:ref:refs/heads/main`

✅ **Implement least privilege**
- Use custom IAM policy instead of AdministratorAccess in production
- Scope permissions to only required services

✅ **Enable AWS CloudTrail**
- Monitor all API calls from GitHub Actions
- Set up alerts for suspicious activity

✅ **Use GitHub Environments**
- Require manual approval for production deployments
- Add environment protection rules

---

## Advanced Configuration

### Multi-Environment Deployment

Modify workflow to support multiple environments:

```yaml
on:
  workflow_dispatch:
    inputs:
      environment:
        type: choice
        options:
          - dev
          - staging
          - production
```

Update trust policy to restrict by branch:

```json
"Condition": {
  "StringEquals": {
    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
  },
  "StringLike": {
    "token.actions.githubusercontent.com:sub": [
      "repo:username/repo:ref:refs/heads/main",
      "repo:username/repo:ref:refs/heads/develop"
    ]
  }
}
```

---

## Support & Resources

- **GitHub OIDC Documentation**: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services
- **AWS CDK Documentation**: https://docs.aws.amazon.com/cdk/
- **Project README**: [README.md](./README.md)
- **Compliance Checklist**: [COMPLIANCE_CHECKLIST.md](./COMPLIANCE_CHECKLIST.md)

---

*Last Updated: 2025-10-26*
