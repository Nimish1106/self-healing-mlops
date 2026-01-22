# 🚀 CI/CD Pipeline Guide (No Makefile)

**Complete guide to running the Self-Healing MLOps pipeline using GitHub Actions**

---

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Local Development (No Makefile)](#local-development-no-makefile)
- [GitHub Actions Workflow](#github-actions-workflow)
- [Pipeline Stages](#pipeline-stages)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Quick Start

### Prerequisites
```powershell
# Install Python 3.10+
python --version

# Install Git
git --version

# Install Docker Desktop
docker --version
docker-compose --version
```

### Initial Setup (Local)
```powershell
# 1. Clone repository
git clone <repo-url>
cd self-healing-mlops

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# or: source venv/bin/activate  # Git Bash

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Create reference data
python scripts/bootstrap_reference.py

# 5. Start services
docker-compose up -d

# 6. Run tests
pytest tests/ -v
```

---

## 💻 Local Development (No Makefile)

### Common Development Tasks

#### **1. Install Dependencies**
```powershell
# Install all dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Or specific packages
pip install mlflow pandas scikit-learn fastapi
```

#### **2. Create Virtual Environment**
```powershell
# Create venv
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (Git Bash)
source venv/bin/activate

# Deactivate
deactivate
```

#### **3. Run Tests**

**Run all tests:**
```powershell
pytest tests/ -v
```

**Run only unit tests:**
```powershell
pytest tests/unit/ -v --tb=short
```

**Run only integration tests:**
```powershell
pytest tests/integration/ -v
```

**Run specific test file:**
```powershell
pytest tests/unit/test_drift_detection.py -v
```

**Run with coverage:**
```powershell
pip install pytest-cov
pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing
```

#### **4. Code Quality Checks**

**Format code with Black:**
```powershell
pip install black
black src/ tests/
```

**Check formatting:**
```powershell
black --check src/ tests/
```

**Lint with Flake8:**
```powershell
pip install flake8
flake8 src/ tests/ --max-line-length=100
```

**Type check with MyPy:**
```powershell
pip install mypy
mypy src/ --ignore-missing-imports
```

**Run all quality checks:**
```powershell
black --check src/ tests/
flake8 src/ tests/ --max-line-length=100
mypy src/ --ignore-missing-imports
```

#### **5. Docker Services**

**Start services:**
```powershell
docker-compose up -d
```

**Check status:**
```powershell
docker-compose ps
```

**View logs:**
```powershell
docker-compose logs -f
```

**Stop services:**
```powershell
docker-compose stop
```

**Stop and remove:**
```powershell
docker-compose down
```

**Restart:**
```powershell
docker-compose restart
```

#### **6. Data Management**

**Generate test predictions:**
```powershell
bash ./scripts/generate_test_predictions.sh
# or
python scripts/generate_fake_predictions.py
```

**Simulate drift:**
```powershell
bash ./scripts/inject_drift.sh covariate
# or in Git Bash: ./scripts/inject_drift.sh population
```

**Create reference data:**
```powershell
python scripts/bootstrap_reference.py
```

#### **7. Training & Model Management**

**Train model:**
```powershell
python src/train_model_mlflow.py
```

**Start MLflow UI:**
```powershell
mlflow ui
# Then open: http://localhost:5000
```

**Check API:**
```powershell
# Start API (if not in Docker)
python -m src.api_mlflow

# Test prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "age": 25,
    "income": 50000,
    "credit_score": 750,
    "employment_years": 3
  }'
```

---

## 🔄 GitHub Actions Workflow

### How It Works

The CI/CD pipeline runs automatically when you:
- Push to `main` or `develop` branches
- Create a pull request to `main`

### Pipeline Stages (In Order)

```
1. Data Validation
   ↓
2. Code Quality Checks (Black, Flake8, MyPy)
   ↓
3. Unit Tests
   ↓
4. Integration Tests
   ↓
5. Model Training & Validation
   ↓
6. Docker Build
   ↓
7. Deploy (main branch only)
```

### View Pipeline Results

1. Go to your GitHub repository
2. Click **Actions** tab
3. Select a workflow run
4. View logs and results

### Workflow File Location
```
.github/workflows/ci-cd.yml
```

---

## 📊 Pipeline Stages Explained

### Stage 1: Data Validation
```powershell
# What it does: Validates CSV data matches schema
# Command: pytest tests/unit/test_data_validation.py -v
# Why: Ensures data quality before processing
```

**To run locally:**
```powershell
pytest tests/unit/test_data_validation.py -v
```

---

### Stage 2: Code Quality
```powershell
# What it does: Checks formatting, linting, types
# Commands:
#   - Black: Checks code formatting (100 chars)
#   - Flake8: Checks linting rules
#   - MyPy: Checks type hints

# To run locally:
black --check src/ tests/
flake8 src/ tests/ --max-line-length=100
mypy src/ --ignore-missing-imports
```

**Fix issues automatically:**
```powershell
black src/ tests/  # Auto-format
flake8 src/        # Just report
mypy src/          # Just report
```

---

### Stage 3: Unit Tests
```powershell
# What it does: Tests individual components
# Command: pytest tests/unit/ -v
# Coverage: Creates coverage.xml report

# To run locally:
pytest tests/unit/ -v
```

---

### Stage 4: Integration Tests
```powershell
# What it does: Tests components working together
# Command: pytest tests/integration/ -v

# To run locally:
pytest tests/integration/ -v
```

---

### Stage 5: Model Training
```powershell
# What it does: Trains model and validates performance
# Steps:
#   1. Download sample data
#   2. Train model
#   3. Validate performance meets baseline

# To run locally:
python src/train_model_mlflow.py
```

---

### Stage 6: Docker Build
```powershell
# What it does: Builds Docker image
# Command: docker build -t self-healing-mlops:latest .

# To run locally:
docker build -t self-healing-mlops:latest .
```

---

### Stage 7: Deploy
```powershell
# What it does: Deploys to production (main branch only)
# Only runs on:
#   - Pushes to main branch
#   - After all previous stages pass

# Deploy steps (in real environment):
#   1. Push image to container registry
#   2. Update Kubernetes/Cloud deployment
#   3. Run smoke tests
#   4. Notify team
```

---

## 🔧 Local Development Workflow

### Complete Development Cycle

```powershell
# 1. Activate environment
.\venv\Scripts\Activate.ps1

# 2. Make code changes
# (Edit files in src/ or tests/)

# 3. Format code
black src/ tests/

# 4. Check quality
black --check src/ tests/
flake8 src/ tests/ --max-line-length=100
mypy src/ --ignore-missing-imports

# 5. Run tests
pytest tests/unit/ -v
pytest tests/integration/ -v

# 6. Commit changes
git add .
git commit -m "Add new feature"

# 7. Push to GitHub
git push origin feature-branch

# 8. Create Pull Request
# GitHub will run full CI/CD pipeline automatically!

# 9. Monitor Actions
# Go to GitHub → Actions → View workflow
```

---

## 🐛 Troubleshooting

### Issue: Tests fail with "ModuleNotFoundError"

**Solution:**
```powershell
# Install missing dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Verify installation
pip list | Select-String "mlflow"
pip list | Select-String "pytest"
```

---

### Issue: Code formatting fails

**Solution:**
```powershell
# Auto-format all code
black src/ tests/

# Then commit
git add .
git commit -m "Format code"
git push
```

---

### Issue: Type checking fails

**Solution:**
```powershell
# View mypy errors
mypy src/ --ignore-missing-imports

# Common fixes:
# 1. Add type hints: def func(x: int) -> str:
# 2. Use Optional for nullable: Optional[str]
# 3. Use Union for multiple types: Union[int, str]
```

---

### Issue: Docker build fails

**Solution:**
```powershell
# Check Docker is running
docker ps

# Build with debug output
docker build -t self-healing-mlops:latest . --progress=plain

# Check Dockerfile syntax
docker build --dry-run .
```

---

### Issue: GitHub Actions won't start

**Solution:**
```powershell
# Check workflow syntax
# 1. Go to .github/workflows/ci-cd.yml
# 2. Validate YAML formatting (no tabs, consistent indentation)
# 3. Check branch names (main vs master)

# Push to trigger workflow
git push
```

---

## 📈 Performance Tips

### Speed Up Tests
```powershell
# Run only unit tests (faster)
pytest tests/unit/ -v

# Run in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest tests/ -v -n auto
```

### Speed Up Build
```powershell
# Use Docker cache
docker build --cache-from self-healing-mlops:latest \
  -t self-healing-mlops:latest .

# Build only what changed
docker-compose up -d --build
```

### Skip Slow Steps
```powershell
# In development, skip integration tests
pytest tests/unit/ -v

# Skip type checking
# Remove mypy from code-quality step
```

---

## 📊 Monitoring Pipeline

### GitHub Actions Dashboard
1. Go to **Actions** tab
2. Click on a workflow run
3. View:
   - Step details
   - Log output
   - Status (passed/failed)
   - Duration

### Local Monitoring
```powershell
# Watch Docker build
docker build -t self-healing-mlops:latest . --progress=plain

# Watch tests run
pytest tests/ -v -s

# Watch logs
docker-compose logs -f
```

---

## 🎯 Common Commands Reference

```powershell
# Setup
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Testing
pytest tests/ -v                          # All tests
pytest tests/unit/ -v                     # Unit only
pytest tests/integration/ -v              # Integration only
pytest tests/unit/test_drift_detection.py # Specific file

# Quality
black src/ tests/                                           # Format
black --check src/ tests/                                   # Check format
flake8 src/ tests/ --max-line-length=100                  # Lint
mypy src/ --ignore-missing-imports                         # Type check

# Docker
docker-compose up -d                      # Start
docker-compose ps                         # Status
docker-compose logs -f                    # Logs
docker-compose stop                       # Stop
docker-compose down                       # Stop & remove

# Git & GitHub
git add .                                  # Stage changes
git commit -m "message"                    # Commit
git push                                   # Push (triggers CI/CD)
git pull                                   # Pull latest

# Utilities
pip list                                   # List packages
python --version                           # Check Python
pip install package-name                   # Install package
```

---

## 📝 Environment Setup

### Create `.env` file (if needed)
```bash
# .env
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_BACKEND_STORE_URI=
API_HOST=0.0.0.0
API_PORT=8000
```

### Load environment
```powershell
# PowerShell
Get-Content .env | ForEach-Object {
    if ($_ -match '(.+?)=(.+)') {
        [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2])
    }
}

# Git Bash
source .env
export $(cat .env | xargs)
```

---

## ✅ Pre-Commit Checklist

Before pushing code:

```
□ Code formatted: black src/ tests/
□ No lint errors: flake8 src/ tests/
□ Types checked: mypy src/
□ Unit tests pass: pytest tests/unit/ -v
□ Integration tests pass: pytest tests/integration/ -v
□ Commit message is clear
□ Branch name is descriptive
□ No secrets in code (no passwords, keys, etc.)
```

---

## 🚀 Deployment Guide

### Automatic Deployment
1. Make code changes
2. Push to `main` branch
3. GitHub Actions runs all tests
4. If all pass → Docker image builds
5. If Docker builds → Deploy step runs
6. Production updated automatically ✅

### Manual Deployment
```powershell
# Build and test locally
docker build -t self-healing-mlops:latest .

# Push to registry
docker tag self-healing-mlops:latest myregistry.azurecr.io/self-healing-mlops:latest
docker push myregistry.azurecr.io/self-healing-mlops:latest

# Deploy (varies by platform: Kubernetes, App Service, etc.)
```

---

## 📞 Support & Resources

| Need | Command/Link |
|------|--------------|
| Python Help | `python --help` |
| Pytest Help | `pytest --help` |
| Black Help | `black --help` |
| Flake8 Help | `flake8 --help` |
| MyPy Help | `mypy --help` |
| Docker Help | `docker --help` |
| Git Help | `git --help` |
| GitHub Actions Docs | https://docs.github.com/en/actions |

---

## 🎓 Learning Path

### 1. Local Development (Day 1)
- [ ] Set up virtual environment
- [ ] Install dependencies
- [ ] Run tests locally
- [ ] Make a small code change
- [ ] Run tests again

### 2. Code Quality (Day 2)
- [ ] Run Black formatter
- [ ] Check Flake8 linting
- [ ] Fix type hints with MyPy
- [ ] Understand why each check matters

### 3. GitHub & CI/CD (Day 3)
- [ ] Create feature branch
- [ ] Make code changes
- [ ] Push to GitHub
- [ ] Watch Actions run
- [ ] Create Pull Request
- [ ] See all checks pass

### 4. Docker & Deployment (Day 4)
- [ ] Build Docker image locally
- [ ] Run tests in Docker
- [ ] Deploy to staging (if available)
- [ ] Understand deployment flow

---

**Version:** 1.0
**Last Updated:** January 2024
**Status:** Complete
