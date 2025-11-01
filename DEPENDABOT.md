# Dependabot Configuration Guide

This project uses GitHub Dependabot to automatically keep dependencies up-to-date by creating pull requests when new versions are available.

---

## 📋 What is Dependabot?

Dependabot is a GitHub-native tool that:
- ✅ Automatically scans your dependencies for updates
- ✅ Creates pull requests to update outdated packages
- ✅ Groups related updates together
- ✅ Provides changelogs and release notes
- ✅ Helps maintain security by updating vulnerable packages

---

## 🔧 Current Configuration

### Monitored Package Ecosystems

Our Dependabot setup monitors **three package ecosystems**:

#### 1. **GitHub Actions** (`github-actions`)
- **Checks:** Weekly (Mondays at 9:00 AM)
- **Files:** `.github/workflows/*.yml`
- **Max PRs:** 5 concurrent
- **Example:** Updates to `actions/checkout@v4` → `actions/checkout@v5`

#### 2. **Python/pip** (`pip`)
- **Checks:** Weekly (Mondays at 9:00 AM)
- **Files:** `requirements.txt`, `requirements-dev.txt`
- **Max PRs:** 10 concurrent
- **Grouped Updates:**
  - **aws-cdk:** AWS CDK packages (`aws-cdk*`, `constructs`)
  - **aws-sdk:** AWS SDK packages (`boto3`, `botocore`)
  - **data-processing:** Data tools (`pandas`, `pyarrow`, `s3fs`)

#### 3. **NPM** (`npm`)
- **Checks:** Weekly (Mondays at 9:00 AM)
- **Files:** `package.json`, `package-lock.json`
- **Max PRs:** 5 concurrent
- **Example:** Updates to `aws-cdk` CLI

---

## 📅 Update Schedule

```
Every Monday at 9:00 AM:
├─ Scan GitHub Actions versions
├─ Scan Python packages in requirements.txt
└─ Scan NPM packages in package.json
```

If updates are found, Dependabot will:
1. Create a branch like `dependabot/pip/aws-cdk-2.170.0`
2. Update the dependency files
3. Run any configured tests (if CI is set up)
4. Open a pull request to `main` branch
5. Assign the PR to `johnsonnuviadenu`

---

## 🏷️ PR Labels

All Dependabot PRs are automatically labeled:
- `dependencies` - Indicates a dependency update
- `github-actions` / `python` / `npm` - Ecosystem type
- `automated` - Indicates automated PR

Filter PRs by label:
```
https://github.com/YOUR-USERNAME/mobiltex-datalake-cdk/pulls?q=is%3Apr+label%3Adependencies
```

---

## 📦 Dependency Groups

To reduce PR noise, related dependencies are grouped together:

### Python Groups

**aws-cdk** (AWS CDK packages)
```python
aws-cdk-lib==2.168.0 → 2.170.0
constructs==10.3.0   → 10.3.5
```
*Result:* 1 PR instead of 2

**aws-sdk** (AWS SDK packages)
```python
boto3==1.40.59     → 1.42.0
botocore==1.40.49  → 1.42.0
```
*Result:* 1 PR instead of 2

**data-processing** (Data tools)
```python
pandas==2.2.0   → 2.2.3
pyarrow==22.0.0 → 23.0.0
s3fs==2025.9.0  → 2025.10.0
```
*Result:* 1 PR instead of 3

---

## 🔄 How to Handle Dependabot PRs

### Automatic PRs will appear like this:

```
Title: chore(deps): Bump aws-cdk-lib from 2.168.0 to 2.170.0
Label: dependencies, python, automated
Assignee: johnsonnuviadenu
```

### Review Process:

1. **Check the Changelog**
   - Click on the PR
   - Review "Release notes" and "Changelog" sections
   - Look for breaking changes

2. **Review the Changes**
   - Check the "Files changed" tab
   - Verify only dependency files are modified

3. **Run Tests Locally (Optional)**
   ```bash
   # Checkout the PR branch
   gh pr checkout <PR-NUMBER>

   # Install dependencies
   pip install -r requirements.txt

   # Test deployment
   cdk synth

   # Or run full deployment to dev environment
   cdk deploy
   ```

4. **Merge the PR**
   - If tests pass and no breaking changes: Click "Merge pull request"
   - If issues found: Request changes or close the PR

---

## 🚨 Security Updates

Dependabot also creates **security alerts** for vulnerable dependencies:

### Priority Levels:
- 🔴 **Critical:** Merge immediately
- 🟠 **High:** Merge within 24 hours
- 🟡 **Medium:** Merge within 1 week
- 🟢 **Low:** Merge with next batch

### Security PR Example:
```
⚠️ chore(deps): Bump boto3 from 1.40.0 to 1.40.59 (security)
Label: dependencies, python, security
```

**Always prioritize security updates!**

---

## ⚙️ Configuration File

Location: `.github/dependabot.yml`

```yaml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    labels:
      - "dependencies"
      - "github-actions"

  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    groups:
      aws-cdk:
        patterns: ["aws-cdk*", "constructs"]

  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
```

---

## 🛠️ Customization Options

### Change Update Frequency

```yaml
schedule:
  interval: "daily"    # Check daily
  interval: "weekly"   # Check weekly (current)
  interval: "monthly"  # Check monthly
```

### Limit Open PRs

```yaml
open-pull-requests-limit: 5  # Max 5 concurrent PRs
```

### Ignore Specific Dependencies

Add to the ecosystem configuration:

```yaml
ignore:
  - dependency-name: "aws-cdk-lib"
    versions: ["2.170.x"]  # Ignore 2.170.x versions
```

### Custom Commit Messages

```yaml
commit-message:
  prefix: "build"        # Use "build" instead of "chore"
  prefix-development: "dev"  # For dev dependencies
```

---

## 📊 Monitoring Dependabot

### View All Dependency PRs

```bash
# Using GitHub CLI
gh pr list --label "dependencies"

# Or in browser
https://github.com/YOUR-USERNAME/mobiltex-datalake-cdk/pulls?q=is%3Apr+label%3Adependencies
```

### Check Dependabot Status

Navigate to:
- **Repository** → **Insights** → **Dependency graph** → **Dependabot**

Here you can see:
- ✅ Last update check
- ✅ Open update PRs
- ✅ Dismissed alerts
- ✅ Security advisories

---

## 🔐 Security Best Practices

1. **Never ignore security updates**
   ```yaml
   # ❌ DON'T DO THIS
   ignore:
     - dependency-name: "boto3"
       update-types: ["version-update:semver-patch"]
   ```

2. **Review grouped updates carefully**
   - Breaking changes can hide in groups
   - Check all changelogs

3. **Test before merging to main**
   - Use branch protection rules
   - Require status checks to pass

4. **Keep Dependabot enabled**
   - Don't disable or pause Dependabot
   - Even if PRs pile up, security updates are critical

---

## 🧪 Testing Dependabot PRs

### Manual Testing:

```bash
# 1. Checkout the Dependabot branch
gh pr checkout 123

# 2. Install updated dependencies
pip install -r requirements.txt

# 3. Run CDK synth
cdk synth

# 4. Deploy to dev (optional)
cdk deploy

# 5. Run verification
./verify_deployment.sh

# 6. If successful, merge the PR
gh pr merge 123 --squash
```

### Automated Testing (with CI/CD):

If you have GitHub Actions CI enabled, Dependabot PRs will automatically trigger:
- ✅ Linting checks
- ✅ Unit tests
- ✅ CDK synth validation
- ✅ Security scans

---

## 📝 Example Workflow

### Week 1: Normal Update
```
Monday 9:00 AM:
└─ Dependabot scans dependencies

Monday 9:15 AM:
├─ PR #45: chore(deps): Bump pandas from 2.2.0 to 2.2.3
└─ PR #46: chore(deps): Bump actions/checkout from v4 to v5

Monday 10:00 AM (You):
├─ Review PR #45 changelog → Looks good
├─ Merge PR #45
├─ Review PR #46 changelog → Breaking changes
└─ Close PR #46 (not ready for v5 yet)
```

### Week 2: Security Alert
```
Wednesday 2:00 PM:
└─ 🚨 Security alert: boto3 has critical vulnerability

Wednesday 2:01 PM (Dependabot):
└─ PR #47: ⚠️ chore(deps): Bump boto3 from 1.40.0 to 1.40.59 (security)

Wednesday 2:15 PM (You):
├─ Review security advisory
├─ Quick test: cdk synth
└─ Merge immediately
```

---

## 🎯 Benefits for This Project

✅ **Always up-to-date AWS CDK** - Get latest features and bug fixes
✅ **Security patches** - Automatic updates for vulnerabilities
✅ **Reduced manual work** - No need to manually check for updates
✅ **Grouped updates** - Related packages updated together
✅ **Audit trail** - All updates tracked in Git history

---

## 📚 Additional Resources

- [Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)
- [Configuration Options](https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/configuration-options-for-the-dependabot.yml-file)
- [Dependabot on Private Registries](https://docs.github.com/en/code-security/dependabot/working-with-dependabot/guidance-for-the-configuration-of-private-registries-for-dependabot)

---

## 📞 Support

For questions about Dependabot configuration:
- 📖 Check [GitHub Docs](https://docs.github.com/en/code-security/dependabot)
- 💬 GitHub Community Discussions

---

*Last Updated: 2025-10-26*
*Dependabot Version: 2*
