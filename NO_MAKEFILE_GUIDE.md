# 📋 NO MAKEFILE - Complete Setup & CI/CD Guide

**January 2024 - Updated for Windows & GitHub Actions**

---

## ✅ Status

- ✅ Makefile **removed** (backed up as `Makefile.backup`)
- ✅ GitHub Actions **configured** (`.github/workflows/ci-cd.yml`)
- ✅ Direct command guides created
- ✅ Windows PowerShell ready
- ✅ Git Bash compatible

---

## 🚀 Start Here - 5 Minute Setup

### Windows PowerShell

```powershell
# 1. Navigate to project
cd c:\Users\admin\Desktop\self-healing-mlops

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Start Docker services
docker-compose up -d

# 5. Run tests
pytest tests/ -v

# 6. Done! View dashboard
start http://localhost:5000  # MLflow
start http://localhost:8000/docs  # API
```

---

## 📚 Complete Guide Links

| Topic | Guide |
|-------|-------|
| **Quick Start (No Makefile)** | [QUICK_START_NO_MAKEFILE.md](QUICK_START_NO_MAKEFILE.md) |
| **CI/CD Pipeline with GitHub Actions** | [GITHUB_ACTIONS_GUIDE.md](GITHUB_ACTIONS_GUIDE.md) |
| **Complete Development Commands** | [CI_CD_GUIDE.md](CI_CD_GUIDE.md) |
| **Architecture & Design** | [docs/architecture.md](docs/architecture.md) |
| **API Reference** | [docs/api.md](docs/api.md) |
| **Daily Operations** | [docs/runbook.md](docs/runbook.md) |
| **Troubleshooting** | [docs/troubleshooting.md](docs/troubleshooting.md) |

---

## 🎯 What You Need to Know

### No More Makefile Commands

**Old way (before):**
```powershell
make setup
make test
make test-unit
make quality
make train
```

**New way (now):**
```powershell
pip install -r requirements.txt
pip install -r requirements-dev.txt

pytest tests/ -v
pytest tests/unit/ -v
black --check src/ tests/; flake8 src/ tests/; mypy src/
python src/train_model_mlflow.py
```

### GitHub Actions Does Everything

When you push code:
1. **Automatically runs** all tests
2. **Automatically checks** code quality
3. **Automatically validates** data
4. **Automatically trains** model
5. **Automatically builds** Docker image
6. **Automatically deploys** (on main branch)

No manual commands needed - it's all automated! ✨

---

## 💻 Essential Commands Reference

### Setup & Installation

```powershell
# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (Git Bash)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Check installation
pip list | Select-String "mlflow"
```

### Testing

```powershell
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Specific test file
pytest tests/unit/test_drift_detection.py -v

# Single test
pytest tests/unit/test_drift_detection.py::TestDriftDetector::test_initialization -v

# With coverage
pip install pytest-cov
pytest tests/ -v --cov=src --cov-report=html --cov-report=term
```

### Code Quality

```powershell
# Format code (auto-fix)
black src/ tests/

# Check formatting
black --check src/ tests/

# Lint
flake8 src/ tests/ --max-line-length=100

# Type check
mypy src/ --ignore-missing-imports

# All quality checks
black --check src/ tests/
flake8 src/ tests/ --max-line-length=100
mypy src/ --ignore-missing-imports
```

### Docker Services

```powershell
# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs (all)
docker-compose logs -f

# View logs (specific)
docker-compose logs -f api
docker-compose logs -f mlflow
docker-compose logs -f monitoring

# Stop services
docker-compose stop

# Stop and remove
docker-compose down

# Restart
docker-compose restart

# Restart specific
docker-compose restart api
```

### Data & Training

```powershell
# Create reference data
python scripts/bootstrap_reference.py

# Generate test data
bash ./scripts/generate_test_predictions.sh

# Or in PowerShell with bash
bash scripts/generate_test_predictions.sh

# Inject drift
bash ./scripts/inject_drift.sh covariate
bash ./scripts/inject_drift.sh population

# Train model
python src/train_model_mlflow.py

# MLflow UI
mlflow ui
# Then open: http://localhost:5000
```

### Git & GitHub

```powershell
# Check status
git status

# Stage all changes
git add .

# Commit
git commit -m "Clear description of changes"

# Push (triggers CI/CD)
git push

# Pull latest
git pull

# Create branch
git checkout -b feature-name

# Switch branch
git checkout branch-name

# View branches
git branch
```

---

## 🔄 Typical Development Workflow

### Step-by-Step

```powershell
# 1. Activate environment
.\venv\Scripts\Activate.ps1

# 2. Create feature branch
git checkout -b add-new-feature

# 3. Make code changes
# (Edit src/ or tests/ files)

# 4. Run tests locally
pytest tests/ -v

# 5. Fix any failures
# (Debug and modify code)

# 6. Format code
black src/ tests/

# 7. Check quality
black --check src/ tests/
flake8 src/ tests/
mypy src/

# 8. Stage changes
git add .

# 9. Commit
git commit -m "Add new feature that does X"

# 10. Push to GitHub
git push origin add-new-feature

# 11. GitHub Actions runs automatically
# Check: GitHub → Actions tab

# 12. Create Pull Request (on GitHub)
# Wait for all checks to pass

# 13. Merge to main
# (Merge button appears on GitHub)

# 14. Deployment automatic
# (GitHub Actions deploy stage runs)
```

---

## 🌐 GitHub Actions Workflow

### Automatic Triggers

CI/CD runs when:
- ✅ You push to `main` branch
- ✅ You push to `develop` branch
- ✅ You create Pull Request to `main`

### Pipeline Stages (In Order)

```
1. Data Validation       ──┐
   (Pandera schemas)       │
                           ├─→ 3. Unit Tests
2. Code Quality          ──┤    (pytest)
   (Black, Flake8, MyPy)   │
                           ├─→ 4. Integration Tests
                           │    (API, workflows)
                           │
                           ├─→ 5. Train & Validate
                           │    (Model training)
                           │
                           ├─→ 6. Docker Build
                           │    (Image creation)
                           │
                           └─→ 7. Deploy
                                (main branch only)
```

### Monitor Results

1. Go to GitHub repository
2. Click **Actions** tab
3. Click on workflow run
4. See each stage status:
   - 🟢 **PASSED** - Stage succeeded
   - 🔴 **FAILED** - Stage failed, click to see why
   - 🟡 **RUNNING** - Currently executing

### Debug Failures

1. Click failed stage
2. Expand failed step
3. Read error message
4. Fix locally:
   ```powershell
   pytest tests/ -v  # See the error
   # Fix the code
   black src/ tests/
   ```
5. Commit and push again
6. Pipeline re-runs automatically

---

## 📊 Pre-Commit Checklist

Before pushing, run these locally:

```powershell
# ✅ 1. Tests pass
pytest tests/ -v
# If fails → Debug locally before pushing

# ✅ 2. Code formatted
black --check src/ tests/
# If fails → Run: black src/ tests/

# ✅ 3. No lint errors
flake8 src/ tests/ --max-line-length=100
# If fails → Fix issues shown

# ✅ 4. Types correct
mypy src/ --ignore-missing-imports
# If fails → Add type hints

# ✅ 5. No secrets
# Check for passwords, API keys, tokens (DON'T commit these!)

# ✅ 6. Commit message clear
git commit -m "Clear description"

# ✅ 7. Create feature branch (not main)
git checkout -b feature-name
```

---

## 🎯 Common Scenarios

### Scenario 1: Make Code Change & Push

```powershell
# 1. Change code
# 2. Test locally
pytest tests/ -v

# 3. Format
black src/ tests/

# 4. Push
git add .
git commit -m "Change description"
git push

# 5. Watch GitHub Actions
# Go to: GitHub → Actions tab
# See: All 7 stages run automatically ✅
```

### Scenario 2: Test Fails

```powershell
# 1. You pushed code
# 2. Tests failed (see GitHub Actions)
# 3. Click failed test to see error
# 4. Reproduce locally
pytest tests/unit/test_drift_detection.py -v

# 5. Debug and fix
# (Edit the code)

# 6. Test again
pytest tests/ -v

# 7. Push fix
git add .
git commit -m "Fix test failure"
git push

# 8. GitHub re-runs tests automatically
# All pass now ✅
```

### Scenario 3: Deploy to Production

```powershell
# 1. Make sure you're on main branch
git checkout main

# 2. Make changes and push
git add .
git commit -m "Production change"
git push origin main

# 3. GitHub Actions automatically:
#    - Runs all 7 pipeline stages
#    - If all pass → Deploy stage runs
#    - Application updates automatically

# 4. Check status
# Go to: GitHub → Actions tab
# See: Deployment completed ✅
```

---

## 🔧 Useful Tools & Tips

### Python Help

```powershell
# See Python version
python --version

# List installed packages
pip list

# See specific package
pip show mlflow

# Search packages
pip search pytest  # (may be disabled)
```

### Testing Tips

```powershell
# Run tests, stop on first failure
pytest tests/ -x

# Verbose output with prints
pytest tests/ -v -s

# Run specific marker
pytest tests/ -m "unit"
pytest tests/ -m "integration"

# Run in parallel (faster)
pip install pytest-xdist
pytest tests/ -n auto
```

### Code Quality Tips

```powershell
# Dry-run black (don't modify)
black --diff src/ tests/

# Lint specific file
flake8 src/api_mlflow.py

# Show type errors
mypy src/ --ignore-missing-imports
```

### Docker Tips

```powershell
# See image sizes
docker images

# Delete unused images
docker image prune

# Delete all containers
docker container prune

# See network
docker network ls
```

---

## ⚠️ Common Issues & Fixes

### Issue: Tests fail with "ModuleNotFoundError"

```powershell
# Solution: Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Issue: Port already in use

```powershell
# Solution: Find and stop process using port
Get-NetTCPConnection -LocalPort 5000
Stop-Process -Id <PID> -Force

# Or stop Docker services
docker-compose down
docker-compose up -d
```

### Issue: Docker won't start

```powershell
# Solution: Check Docker is running
docker ps

# If error → Start Docker Desktop
# Wait 60 seconds
docker ps  # Should work now
```

### Issue: Can't run .sh scripts

```powershell
# Solution: Use Git Bash
bash ./scripts/generate_test_predictions.sh

# Or use Python instead
python scripts/bootstrap_reference.py
```

### Issue: Git won't push

```powershell
# Solution: Fix pre-commit checks
black src/ tests/
flake8 src/ tests/
mypy src/

# Then try again
git add .
git commit -m "Fix quality"
git push
```

---

## 📞 Quick Help

| Need | Command |
|------|---------|
| Run tests | `pytest tests/ -v` |
| Check quality | `black --check src/ tests/; flake8 src/ tests/; mypy src/` |
| Format code | `black src/ tests/` |
| View Docker logs | `docker-compose logs -f` |
| Stop services | `docker-compose stop` |
| Start services | `docker-compose up -d` |
| Train model | `python src/train_model_mlflow.py` |
| View MLflow | `start http://localhost:5000` |
| Push to GitHub | `git add .; git commit -m "message"; git push` |
| View CI/CD | Go to GitHub → Actions tab |

---

## 🎓 Learning Resources

### For New Developers

1. Start: [QUICK_START_NO_MAKEFILE.md](QUICK_START_NO_MAKEFILE.md)
2. Understand: [docs/architecture.md](docs/architecture.md)
3. Build: Make code changes and push
4. Monitor: Go to GitHub Actions tab

### For DevOps/Platform

1. Learn: [GITHUB_ACTIONS_GUIDE.md](GITHUB_ACTIONS_GUIDE.md)
2. Review: `.github/workflows/ci-cd.yml`
3. Customize: Modify workflow as needed
4. Deploy: Watch deployment stage

### For Data Science

1. Explore: [docs/api.md](docs/api.md)
2. Training: `python src/train_model_mlflow.py`
3. Monitoring: `python scripts/bootstrap_reference.py`
4. MLflow: `mlflow ui` then `http://localhost:5000`

---

## ✅ Verification Checklist

After setup, verify you can:

```powershell
☐ Activate virtual environment
.\venv\Scripts\Activate.ps1

☐ List installed packages
pip list | Select-String mlflow

☐ Run tests
pytest tests/unit/ -v

☐ Format code
black src/ tests/

☐ Start Docker
docker-compose ps

☐ View MLflow
start http://localhost:5000

☐ Push to GitHub
git push

☐ View GitHub Actions
# GitHub → Actions tab
```

---

## 🎊 You're All Set!

You now have:
- ✅ **No Makefile** - Direct commands instead
- ✅ **GitHub Actions** - Automated CI/CD
- ✅ **Full Documentation** - Guides for every task
- ✅ **Windows Ready** - PowerShell & Git Bash
- ✅ **Production Ready** - 7-stage pipeline

**Next step:**
```powershell
pytest tests/ -v
git add .
git commit -m "First commit"
git push
```

Watch GitHub Actions run automatically! 🚀

---

**Version:** 2.0 (No Makefile)
**Date:** January 2024
**Status:** Active & Tested
