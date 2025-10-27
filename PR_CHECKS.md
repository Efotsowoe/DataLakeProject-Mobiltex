# Pull Request Checks Documentation

## Overview

The Mobiltex Data Lake project uses **automated PR checks** to ensure code quality, security, and compliance before merging to main branch.

---

## Workflow Trigger

### When PR Checks Run

```yaml
on:
  pull_request:
    branches:
      - main
      - develop
    types:
      - opened        # New PR created
      - synchronize   # New commits pushed
      - reopened      # Closed PR reopened
```

**Every time you:**
1. Open a new pull request to `main` or `develop`
2. Push new commits to an existing PR
3. Reopen a previously closed PR

---

## Check Jobs (6 Total)

### 1. Code Quality & Linting ✨

**Purpose:** Ensure code follows Python best practices

**Tools Used:**
- **flake8** - Python linting
- **black** - Code formatting
- **isort** - Import sorting
- **yamllint** - YAML linting

**Checks:**
```python
# Critical issues (will fail PR):
- Syntax errors
- Undefined names
- Import errors
- Unused imports

# Non-critical (warnings):
- Line length > 127 characters
- Complexity > 10
- Style violations
```

**Configuration Files:**
- `.flake8` - Flake8 settings
- `pyproject.toml` - Black & isort settings
- `.yamllint` - YAML linting rules

---

### 2. CDK Validation 🏗️

**Purpose:** Verify infrastructure code is valid

**Steps:**
1. **CDK Synth**
   - Generates CloudFormation template
   - Validates CDK code syntax
   - Checks resource definitions

2. **Template Upload**
   - Uploads generated CloudFormation templates as artifacts
   - Retained for 7 days

**What Gets Validated:**
```python
✅ CDK app structure
✅ Python syntax in CDK code
✅ Resource configurations
✅ Stack dependencies
✅ CloudFormation template generation
```

**Artifacts Generated:**
- `cloudformation-template` - All generated CFN templates

---

### 3. Security Scanning 🔒

**Purpose:** Detect security vulnerabilities and misconfigurations

**Tool:** Trivy (Aqua Security)

**Three Scans Performed:**

#### 3.1 Filesystem Scan
```bash
Scans: Entire codebase
Format: SARIF (uploaded to GitHub Security)
Severity: CRITICAL, HIGH, MEDIUM
```

#### 3.2 Configuration Scan
```bash
Scans: Infrastructure-as-Code files
Target: CDK code, YAML files
Checks: Security best practices, misconfigurations
```

#### 3.3 Dependency Scan
```bash
Scans: requirements.txt
Target: Python packages
Checks: Known CVEs in dependencies
```

**Results:**
- 📊 Summary in PR checks
- 🔒 Detailed report in GitHub Security tab
- 📦 Artifacts retained for 30 days

**Example Issues Detected:**
- Hardcoded secrets
- Overly permissive IAM policies
- Public S3 buckets
- Vulnerable package versions
- Insecure configurations

---

### 4. Dependency Check 📦

**Purpose:** Analyze and validate Python dependencies

**Checks Performed:**

#### 4.1 Outdated Packages
```bash
pip list --outdated
```
Shows packages with newer versions available

#### 4.2 Dependency Tree
```bash
pipdeptree
```
Visualizes dependency relationships

#### 4.3 Conflict Detection
```bash
pip check
```
Identifies incompatible package versions

#### 4.4 Known Vulnerabilities
```bash
safety check
```
Scans against Safety DB for known CVEs

**Output Example:**
```
Outdated Packages:
- boto3 (1.40.0 → 1.42.0)
- aws-cdk-lib (2.168.0 → 2.170.0)

Vulnerabilities:
- requests (2.28.0) - CVE-2023-XXXXX
```

---

### 5. Test Execution 🧪

**Purpose:** Run unit tests and generate coverage reports

**Framework:** pytest

**Steps:**

#### 5.1 Unit Tests
```bash
pytest tests/ -v --tb=short
```
- Runs all tests in `tests/` directory
- Verbose output with short tracebacks
- Fails if any test fails

#### 5.2 Coverage Report
```bash
pytest --cov=mobiltex_datalake_cdk --cov-report=html
```
- Measures code coverage
- Generates HTML report
- Uploads as artifact

**Coverage Goals:**
- **Minimum:** 70%
- **Target:** 85%
- **Ideal:** 95%+

**Artifacts:**
- `coverage-report` - HTML coverage report (7 days)

---

### 6. PR Summary 📋

**Purpose:** Aggregate all check results into single view

**What It Does:**

1. **Collects Results**
   - Status from all 5 previous jobs
   - Pass/Fail for each check

2. **Generates Summary Table**
   ```markdown
   | Check | Status |
   |-------|--------|
   | Code Quality | ✅ Passed |
   | CDK Validation | ✅ Passed |
   | Security Scanning | ✅ Passed |
   | Dependency Check | ✅ Passed |
   | Test Execution | ✅ Passed |
   ```

3. **Posts Comment on PR**
   - Automatically comments on PR with results
   - Updates comment on subsequent commits
   - Includes timestamp of last update

4. **Overall Status**
   - ✅ All checks passed → Ready to merge
   - ⚠️ Some checks failed → Needs fixes

---

## Viewing Results

### 1. GitHub Actions Tab
```
Repository → Actions → PR Checks → Latest Run
```

### 2. PR Conversation Tab
```
Pull Request → Conversation → Bot Comment
```

### 3. PR Checks Tab
```
Pull Request → Checks → Individual job details
```

### 4. Security Tab
```
Repository → Security → Code scanning alerts
```

---

## Fixing Failed Checks

### Code Quality Failures

**Issue:** Linting errors
```bash
# Local fix:
flake8 .
black .
isort .

# Then commit and push
git add .
git commit -m "fix: Apply code formatting"
git push
```

### CDK Validation Failures

**Issue:** CDK synth fails
```bash
# Local debugging:
cdk synth

# Common issues:
- Missing imports
- Invalid resource properties
- Circular dependencies
```

### Security Scan Failures

**Issue:** Vulnerabilities detected
```bash
# Update vulnerable package:
pip install --upgrade package-name

# Update requirements.txt:
pip freeze > requirements.txt

# Commit changes
git add requirements.txt
git commit -m "chore: Update vulnerable dependencies"
git push
```

### Dependency Check Failures

**Issue:** Conflicting dependencies
```bash
# Check conflicts:
pip check

# Resolve:
pip install package-name==version

# Update requirements:
pip freeze > requirements.txt
```

### Test Failures

**Issue:** Tests failing
```bash
# Run tests locally:
pytest tests/ -v

# Debug specific test:
pytest tests/test_file.py::test_function -v

# Fix code and rerun
```

---

## Configuration Files

### Code Quality

**`.flake8`**
```ini
[flake8]
max-line-length = 127
max-complexity = 10
exclude = .venv,cdk.out
```

**`pyproject.toml`**
```toml
[tool.black]
line-length = 127
target-version = ['py39']

[tool.isort]
profile = "black"
line_length = 127

[tool.pytest.ini_options]
testpaths = ["tests"]
```

**`.yamllint`**
```yaml
rules:
  line-length:
    max: 200
```

---

## Best Practices

### Before Creating PR

1. **Run checks locally:**
   ```bash
   # Linting
   flake8 .
   black --check .
   isort --check .

   # Tests
   pytest tests/

   # CDK
   cdk synth
   ```

2. **Fix all issues before pushing**

3. **Keep PRs small and focused**
   - Easier to review
   - Faster checks
   - Less likely to have conflicts

### During PR Review

1. **Watch for check failures**
   - GitHub will notify you

2. **Fix issues promptly**
   - Don't let checks stay red

3. **Update PR description**
   - Explain what changed
   - Why changes were made

### After Checks Pass

1. **Request review**
   - Don't merge without review

2. **Address review comments**
   - Make requested changes

3. **Merge using squash**
   - Keeps history clean

---

## Workflow Artifacts

### What Gets Saved

| Artifact | Retention | Size | Use Case |
|----------|-----------|------|----------|
| CloudFormation Templates | 7 days | ~500KB | Review generated templates |
| Trivy Security Results | 30 days | ~2MB | Security audit trail |
| Coverage Report | 7 days | ~1MB | View test coverage |

### Downloading Artifacts

```
GitHub Actions → Workflow Run → Artifacts section → Download
```

---

## Security Tab Integration

### GitHub Code Scanning

Trivy results are automatically uploaded to:
```
Repository → Security → Code scanning alerts
```

**Benefits:**
- ✅ Track security issues over time
- ✅ Get alerts for new vulnerabilities
- ✅ Integration with Dependabot
- ✅ Compliance reporting

**Alert Severity:**
- 🔴 **Critical** - Fix immediately
- 🟠 **High** - Fix before merge
- 🟡 **Medium** - Fix in follow-up PR
- 🟢 **Low** - Optional fix

---

## Performance Metrics

### Typical Execution Times

| Job | Duration | Parallelized |
|-----|----------|--------------|
| Code Quality | ~2 min | ✅ Yes |
| CDK Validation | ~3 min | ✅ Yes |
| Security Scan | ~4 min | ✅ Yes |
| Dependency Check | ~2 min | ✅ Yes |
| Test Execution | ~3 min | ✅ Yes |
| PR Summary | ~30 sec | ❌ Sequential |

**Total:** ~4-5 minutes (jobs run in parallel)

---

## Exemptions & Overrides

### Skip Checks (Not Recommended)

```yaml
# In commit message:
git commit -m "fix: Emergency hotfix [skip ci]"
```
⚠️ **Use only for emergencies!**

### Continue on Error

Some checks are set to `continue-on-error: true`:
- Code formatting (black)
- Import sorting (isort)
- YAML linting

**Why?**
- Won't block PR
- Still visible in summary
- Can be fixed later

---

## Troubleshooting

### Issue: Checks stuck "pending"

**Cause:** GitHub Actions runner queue
**Solution:** Wait or restart workflow

### Issue: Trivy scan fails

**Cause:** Trivy database update
**Solution:** Retry workflow

### Issue: Coverage upload fails

**Cause:** Test failures
**Solution:** Fix tests first, then rerun

### Issue: Permission denied on Security tab

**Cause:** Forked repository
**Solution:** Can't fix (GitHub limitation)

---

## Local Development Setup

### Install Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Run All Checks Locally

```bash
#!/bin/bash
# run-checks.sh

echo "🔍 Running code quality checks..."
flake8 .
black --check .
isort --check .

echo "🏗️ Validating CDK..."
cdk synth > /dev/null

echo "🔒 Running security scan..."
trivy fs --severity CRITICAL,HIGH .

echo "📦 Checking dependencies..."
pip check
safety check

echo "🧪 Running tests..."
pytest tests/ -v

echo "✅ All checks passed!"
```

---

## Related Documentation

- **Deployment:** [README.md](./README.md)
- **CI/CD Setup:** [CICD_SETUP.md](./CICD_SETUP.md)
- **Workflow Architecture:** [WORKFLOW_ARCHITECTURE.md](./WORKFLOW_ARCHITECTURE.md)
- **Dependabot:** [DEPENDABOT.md](./DEPENDABOT.md)

---

*Last Updated: 2025-10-26*
*Workflow File: `.github/workflows/pr-checks.yml`*
