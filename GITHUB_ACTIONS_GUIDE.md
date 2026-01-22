# 🚀 GitHub Actions CI/CD Pipeline - Complete Guide

**No Makefile Needed - Everything Through GitHub Actions & Command Line**

---

## 📋 Overview

This project uses **GitHub Actions** for automated testing, quality checks, and deployment. No Makefile required!

### Pipeline Stages (Automatic)

```
┌─────────────────────────────────────────────────────────────┐
│  GitHub Actions CI/CD Pipeline                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Data Validation          ──┐                            │
│     (Pandera schemas)         │                            │
│                                ├─→ 3. Unit Tests           │
│  2. Code Quality              │      (pytest)              │
│     (Black, Flake8, MyPy)    ──┤                           │
│                                ├─→ 4. Integration Tests    │
│                                │      (FastAPI, workflows) │
│                                ├─→ 5. Train & Validate    │
│                                │      (Model training)     │
│                                │                            │
│                                ├─→ 6. Docker Build         │
│                                │      (Image creation)     │
│                                │                            │
│                                └─→ 7. Deploy               │
│                                      (main branch only)     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Triggers

Pipeline runs automatically when:
- ✅ You push to `main` branch
- ✅ You push to `develop` branch
- ✅ You create Pull Request to `main`

---

## 🔧 Local Development (Before Pushing)

### Prerequisites
```powershell
# Install
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Run Tests Locally
```powershell
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# With coverage
pip install pytest-cov
pytest tests/ -v --cov=src --cov-report=html
```

### Code Quality Checks
```powershell
# Format code (auto-fix)
black src/ tests/

# Check formatting
black --check src/ tests/

# Lint code
flake8 src/ tests/ --max-line-length=100

# Type check
mypy src/ --ignore-missing-imports
```

### Validate Before Pushing
```powershell
# Run all local checks that GitHub Actions will run
pytest tests/ -v
black --check src/ tests/
flake8 src/ tests/
mypy src/ --ignore-missing-imports
```

**Only push when all pass locally!**

---

## 🌐 GitHub Actions Workflow Stages

### Stage 1: Data Validation

**When:** Always runs first
**What:** Validates CSV data against Pandera schemas
**Command:** `pytest tests/unit/test_data_validation.py -v`

```yaml
Run locally:
pytest tests/unit/test_data_validation.py -v
```

**Passes if:** CSV files match expected schema (columns, types, ranges)

---

### Stage 2: Code Quality

**When:** Runs in parallel with data validation
**What:** Checks formatting, linting, type hints
**Commands:**
- Black: `black --check src/ tests/`
- Flake8: `flake8 src/ tests/ --max-line-length=100`
- MyPy: `mypy src/ --ignore-missing-imports`

```powershell
Run locally:
black --check src/ tests/
flake8 src/ tests/ --max-line-length=100
mypy src/ --ignore-missing-imports
```

**Passes if:** No formatting issues, no lint errors, types are correct

---

### Stage 3: Unit Tests

**When:** After stages 1 & 2 pass
**What:** Tests individual components in isolation
**Command:** `pytest tests/unit/ -v --cov=src`

```powershell
Run locally:
pip install pytest-cov
pytest tests/unit/ -v --cov=src --cov-report=html
```

**Tests:**
- Drift detection logic
- Evaluation gate decisions
- Data validation schemas
- Proxy metrics calculations
- Model evaluation

**Passes if:** All assertions pass, coverage > 70%

---

### Stage 4: Integration Tests

**When:** After unit tests pass
**What:** Tests components working together
**Command:** `pytest tests/integration/ -v`

```powershell
Run locally:
pytest tests/integration/ -v
```

**Tests:**
- API endpoints
- Monitoring pipeline
- Retraining workflow

**Passes if:** All integration scenarios work

---

### Stage 5: Model Training & Validation

**When:** After integration tests pass
**What:** Trains model and validates performance
**Commands:**
1. Check data: `ls data/`
2. Train: `python src/train_model_mlflow.py` (simulated in CI)
3. Validate: Performance check

**Passes if:** Model trains without errors

---

### Stage 6: Docker Build

**When:** After training passes
**What:** Builds Docker image
**Command:** `docker build -t self-healing-mlops:latest .`

```powershell
Run locally:
docker build -t self-healing-mlops:latest .
docker run --rm self-healing-mlops:latest python --version
```

**Passes if:** Image builds and basic test runs

---

### Stage 7: Deploy

**When:** After Docker build passes AND on `main` branch only
**What:** Deploys to production
**Actions:**
1. Push to container registry
2. Update cloud deployment
3. Run smoke tests
4. Notify team

**Only runs on:** Pushes to `main` branch after all tests pass

---

## 📈 Typical GitHub Actions Experience

### Scenario 1: Code Changes Pass All Tests

```
You push code
     ↓
GitHub detects push
     ↓
Runs all 7 stages automatically
     ↓
All stages PASS ✅
     ↓
If main branch → Deploy runs
     ↓
System updates automatically 🎉
```

### Scenario 2: Tests Fail

```
You push code
     ↓
GitHub runs tests
     ↓
Tests FAIL ❌
     ↓
You see error in Actions tab
     ↓
You fix code locally:
  - pytest tests/ -v  (see error)
  - Fix the code
  - black src/ tests/ (format)
  ↓
git add . && git commit -m "Fix test" && git push
     ↓
GitHub re-runs all tests
     ↓
Tests PASS ✅
```

---

## 🎯 Using GitHub Actions

### View Pipeline Results

1. Go to GitHub repository
2. Click **Actions** tab
3. See all workflow runs with status

### Understanding Status Colors

```
🟢 PASSED   → All tests passed, ready to merge
🔴 FAILED   → Something broke, needs fixing
🟡 RUNNING  → Currently executing, wait a minute
⚪ SKIPPED  → Not applicable to this trigger
```

### Debug Failed Tests

1. Click on failed workflow run
2. Click on failed stage (red ❌)
3. Expand the step that failed
4. Read error message
5. Fix locally with: `pytest tests/ -v`
6. Push again

---

## 📝 Workflow File

Located at: `.github/workflows/ci-cd.yml`

### Key Variables

```yaml
env:
  PYTHON_VERSION: '3.10'  # Python version for all jobs
```

### Key Conditions

```yaml
# Deploy only on main branch pushes
if: github.ref == 'refs/heads/main' && github.event_name == 'push'

# Run only if previous jobs passed
needs: [validate-data, code-quality, unit-tests, ...]
```

---

## 🔐 Secrets & Configuration

### Environment Variables

For production deployment, add secrets in GitHub:

1. Go to GitHub → Settings → Secrets and variables → Actions
2. Add secrets:
   ```
   REGISTRY_USERNAME      (for Docker)
   REGISTRY_PASSWORD      (for Docker)
   DEPLOYMENT_TOKEN       (for cloud)
   SLACK_WEBHOOK          (for notifications)
   ```

3. Reference in workflow:
   ```yaml
   env:
     REGISTRY_USERNAME: ${{ secrets.REGISTRY_USERNAME }}
   ```

### .env File (Local Only)

Create local `.env` for development:
```
MLFLOW_TRACKING_URI=http://localhost:5000
API_PORT=8000
```

**Never commit `.env` to GitHub!**

---

## 🛠️ Common Tasks

### I Want To...

#### **Run All Tests Locally**
```powershell
pytest tests/ -v
```

#### **Run Tests in Specific Module**
```powershell
pytest tests/unit/test_drift_detection.py -v
```

#### **Run Single Test**
```powershell
pytest tests/unit/test_drift_detection.py::TestDriftDetector::test_detect_covariate_shift -v
```

#### **See What Tests Exist**
```powershell
pytest tests/ --collect-only
```

#### **Format All Code**
```powershell
black src/ tests/
```

#### **Check Code Quality**
```powershell
flake8 src/ tests/ --max-line-length=100
```

#### **Check Type Hints**
```powershell
mypy src/ --ignore-missing-imports
```

#### **Build Docker Image**
```powershell
docker build -t self-healing-mlops:latest .
```

#### **Test Docker Image**
```powershell
docker run --rm self-healing-mlops:latest python --version
```

#### **Push to GitHub (Trigger Pipeline)**
```powershell
git add .
git commit -m "Your message"
git push
```

#### **Check Pipeline Status**
Go to: GitHub → Actions tab → Select workflow run

---

## 📊 Pipeline Metrics

### Success Rate
```
Target: 95%+ test pass rate
Metric: (Passed runs / Total runs) × 100
```

### Build Time
```
Target: < 5 minutes per run
Typical breakdown:
  - Setup: 30 seconds
  - Validation: 30 seconds
  - Tests: 2-3 minutes
  - Docker: 1 minute
  - Deploy: 30 seconds
```

### Test Coverage
```
Target: > 70% code coverage
Current: Measured after each unit test run
Trend: Should increase over time
```

---

## 🐛 Troubleshooting

### Issue: Tests Pass Locally But Fail in GitHub Actions

**Cause:** Different Python version or dependencies
**Solution:**
```powershell
# Match GitHub's Python 3.10
python3.10 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest tests/ -v
```

---

### Issue: Can't Push Code (Pre-commit Hooks)

**Cause:** Pre-commit hooks failing
**Solution:**
```powershell
# Fix formatting
black src/ tests/

# Then push
git add .
git commit -m "message"
git push
```

---

### Issue: Docker Build Fails in GitHub Actions

**Cause:** Missing files or permissions
**Solution:**
```powershell
# Test locally
docker build -t self-healing-mlops:latest .

# Check Dockerfile syntax
cat Dockerfile | head -20

# Check if files exist
ls src/
ls requirements.txt
```

---

### Issue: Deployment Failed

**Only affects main branch**
**Check:**
1. Go to Actions tab
2. Click failed deploy job
3. Read error message
4. Fix issue
5. Push to main again

---

## 🎓 Learning Path

### Day 1: Understand Basics
- [ ] Read this guide
- [ ] Run tests locally: `pytest tests/ -v`
- [ ] Make small code change
- [ ] Push and watch GitHub Actions

### Day 2: Run Full Pipeline
- [ ] Fix any test failures
- [ ] Learn code quality: `black`, `flake8`, `mypy`
- [ ] Create Pull Request
- [ ] See all tests run in PR

### Day 3: Merge & Deploy
- [ ] Merge PR to main
- [ ] Watch deployment stage
- [ ] See application update
- [ ] Verify in production

### Day 4: Troubleshoot
- [ ] Introduce test failure
- [ ] Debug in GitHub Actions
- [ ] Fix code
- [ ] Rerun tests
- [ ] Understand error messages

---

## 📚 Quick Reference

### Commands

```powershell
# Setup
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Testing
pytest tests/ -v                              # All
pytest tests/unit/ -v                         # Unit only
pytest tests/integration/ -v                  # Integration only
pytest tests/ -v --cov=src --cov-report=html # With coverage

# Code Quality
black src/ tests/                             # Format
black --check src/ tests/                     # Check
flake8 src/ tests/ --max-line-length=100    # Lint
mypy src/ --ignore-missing-imports           # Type check

# Git & Push
git add .
git commit -m "message"
git push                                      # Triggers CI/CD

# Docker
docker-compose up -d                          # Start services
docker build -t self-healing-mlops:latest .  # Build image
```

### GitHub Actions

| Action | Location |
|--------|----------|
| View Runs | Repository → Actions tab |
| View Logs | Actions → Workflow → Failed Step |
| Trigger | Push code to main/develop |
| Re-run | Actions → Workflow → Re-run |

---

## ✅ Pre-Push Checklist

Always run these before pushing:

```powershell
# 1. Tests pass
pytest tests/ -v

# 2. Code formatted
black --check src/ tests/

# 3. No lint errors
flake8 src/ tests/

# 4. Types correct
mypy src/ --ignore-missing-imports

# 5. No secrets in code
# (Check passwords, API keys, etc.)

# 6. Commit message clear
git commit -m "Clear description of changes"

# 7. Push to feature branch (not main)
git push origin feature-branch-name
```

---

## 🎊 Summary

- ✅ **No Makefile needed** - use command line directly
- ✅ **GitHub Actions does CI/CD** - automated on every push
- ✅ **7 stages run automatically** - validation → testing → deployment
- ✅ **Local testing first** - run `pytest` before pushing
- ✅ **Fast feedback** - see results in Actions tab in minutes

---

**Ready to go!** 🚀

Push your code and watch GitHub Actions work its magic!

```powershell
git add .
git commit -m "your message"
git push
```

Then monitor at: GitHub → Actions tab

---

**Version:** 1.0
**Last Updated:** January 2024
**Status:** Active
