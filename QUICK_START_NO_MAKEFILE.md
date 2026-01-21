# 🚀 Quick Start Guide (No Makefile)

**Get running in 5 minutes without Makefile**

---

## ⚡ 5-Minute Setup

### Step 1: Prerequisites (Already Have?)
```powershell
# Check you have these
python --version          # Should be 3.10+
docker --version          # Should exist
git --version             # Should exist

# If missing, install:
# Python: https://www.python.org/downloads/
# Docker: https://www.docker.com/products/docker-desktop
# Git: https://git-scm.com/download/win
```

### Step 2: Clone & Enter Project
```powershell
git clone <your-repo-url>
cd self-healing-mlops
```

### Step 3: Create Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 4: Install Dependencies
```powershell
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Step 5: Start Services
```powershell
docker-compose up -d
```

### Step 6: Run Tests
```powershell
pytest tests/ -v
```

**Done!** ✅ You're running the full MLOps pipeline.

---

## 📚 Common Commands (No Makefile Needed)

### Testing
```powershell
# Run all tests
pytest tests/ -v

# Run unit tests only
pytest tests/unit/ -v

# Run integration tests only
pytest tests/integration/ -v

# Run with output (-s shows prints)
pytest tests/ -v -s

# Run single test file
pytest tests/unit/test_drift_detection.py -v

# Run single test
pytest tests/unit/test_drift_detection.py::TestDriftDetector::test_detect_covariate_shift -v
```

### Code Quality
```powershell
# Format code
black src/ tests/

# Check if formatting needed
black --check src/ tests/

# Lint code
flake8 src/ tests/ --max-line-length=100

# Type check
mypy src/ --ignore-missing-imports

# Run all checks at once (from repo root)
black --check src/ tests/ && flake8 src/ tests/ && mypy src/
```

### Docker Services
```powershell
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs (all services)
docker-compose logs -f

# View logs (specific service)
docker-compose logs -f mlflow
docker-compose logs -f api
docker-compose logs -f monitoring

# Stop services
docker-compose stop

# Stop and remove everything
docker-compose down

# Restart
docker-compose restart
```

### Data & Training
```powershell
# Create reference data
python scripts/bootstrap_reference.py

# Generate test predictions
bash ./scripts/generate_test_predictions.sh

# Or in PowerShell
bash scripts/generate_test_predictions.sh

# Inject drift
bash ./scripts/inject_drift.sh covariate

# Train model
python src/train_model_mlflow.py

# Start MLflow UI
mlflow ui
# Then open http://localhost:5000
```

### Git & CI/CD
```powershell
# Check git status
git status

# Stage changes
git add .

# Commit
git commit -m "Your message here"

# Push (triggers GitHub Actions)
git push

# Pull latest
git pull

# View branch
git branch

# Create new branch
git checkout -b feature-name
```

---

## 🔍 Understanding the Pipeline

### What Happens When You Push

```
1. You run: git push
   ↓
2. GitHub detects push to main/develop
   ↓
3. GitHub Actions automatically starts
   ↓
4. Pipeline runs 7 stages:
   • Data Validation
   • Code Quality (Black, Flake8, MyPy)
   • Unit Tests
   • Integration Tests
   • Model Training
   • Docker Build
   • Deploy (if main branch)
   ↓
5. You see results in GitHub → Actions tab
```

### Monitor Pipeline
1. Go to GitHub → **Actions** tab
2. Click the workflow run
3. See which stage failed (if any)
4. Click on failed stage to see logs

---

## 🎯 Typical Workflow

### Development & Testing Locally

```powershell
# 1. Activate environment
.\venv\Scripts\Activate.ps1

# 2. Create feature branch
git checkout -b add-new-feature

# 3. Make code changes
# (Edit files in src/ or tests/)

# 4. Run tests locally
pytest tests/ -v

# 5. Format code
black src/ tests/

# 6. Check linting
flake8 src/ tests/ --max-line-length=100

# 7. Check types
mypy src/ --ignore-missing-imports

# 8. Stage and commit
git add .
git commit -m "Add new feature"

# 9. Push to GitHub
git push origin add-new-feature

# 10. GitHub Actions runs automatically
# Check: GitHub → Actions tab

# 11. Create Pull Request (on GitHub)
# GitHub will run tests in PR

# 12. Merge when all tests pass
# (on main branch, deployment runs)
```

---

## 🚀 Common Tasks

### I Want To...

#### **Run Tests**
```powershell
pytest tests/ -v
```

#### **Check Code Quality**
```powershell
black --check src/ tests/
flake8 src/ tests/
mypy src/
```

#### **Fix Code Formatting**
```powershell
black src/ tests/
```

#### **View Logs**
```powershell
docker-compose logs -f
```

#### **See MLflow Dashboard**
```powershell
mlflow ui
# Then open http://localhost:5000
```

#### **Create Reference Data**
```powershell
python scripts/bootstrap_reference.py
```

#### **Train Model**
```powershell
python src/train_model_mlflow.py
```

#### **Generate Test Data**
```powershell
bash ./scripts/generate_test_predictions.sh
```

#### **Simulate Data Drift**
```powershell
bash ./scripts/inject_drift.sh covariate
```

#### **Stop Everything**
```powershell
docker-compose down
deactivate
```

---

## 🐛 Quick Troubleshooting

### Tests fail: "ModuleNotFoundError: No module named 'mlflow'"
```powershell
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Tests fail: "pytest-cov not found"
```powershell
pip install pytest-cov
```

### Docker won't start
```powershell
# Check if Docker Desktop is running
docker ps

# If not running, start Docker Desktop and wait 60 seconds
```

### Port already in use (5000, 8000)
```powershell
# Stop current services
docker-compose down

# Start again
docker-compose up -d
```

### Black/Flake8/MyPy not found
```powershell
pip install black flake8 mypy
```

### Can't run .sh scripts in PowerShell
```powershell
# Option 1: Use Git Bash
bash ./scripts/generate_test_predictions.sh

# Option 2: Use Python instead
python scripts/bootstrap_reference.py
```

---

## 📊 GitHub Actions Dashboard

### View Your Pipeline

1. **Go to GitHub**: Your repository
2. **Click Actions** tab
3. **See workflow runs** with status:
   - ✅ All passed → Ready to merge
   - ❌ Failed → Fix code and push again
   - ⏳ Running → Wait a few minutes

### Understand Status
```
✅ PASSED     → All tests passed, code quality ok
❌ FAILED     → Something broken, see logs
⏳ IN PROGRESS → Currently running, check back
```

### Debug Failed Stage
1. Click on failed workflow
2. Click on failed stage (red ❌)
3. See error message
4. Fix code locally
5. Run tests: `pytest tests/ -v`
6. Commit and push again
7. Pipeline re-runs automatically

---

## 📁 Project Structure

```
self-healing-mlops/
├── src/                    # Source code
│   ├── api_mlflow.py      # FastAPI app
│   ├── train_model_mlflow.py  # Training script
│   └── ...
├── tests/                  # Test files
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── conftest.py        # Test fixtures
├── scripts/               # Utility scripts
│   ├── bootstrap_reference.py
│   ├── generate_test_predictions.sh
│   └── inject_drift.sh
├── .github/workflows/     # GitHub Actions CI/CD
│   └── ci-cd.yml
├── data/                  # Data files
├── models/                # Trained models
├── monitoring/            # Monitoring data
├── requirements.txt       # Dependencies
├── requirements-dev.txt   # Dev dependencies
├── pytest.ini            # Test configuration
├── docker-compose.yml    # Docker services
└── CI_CD_GUIDE.md        # Full CI/CD guide
```

---

## ✅ Checklist Before Pushing

- [ ] All tests pass: `pytest tests/ -v`
- [ ] Code formatted: `black src/ tests/`
- [ ] No linting errors: `flake8 src/ tests/`
- [ ] Types checked: `mypy src/`
- [ ] No debug code left in
- [ ] No credentials or secrets in code
- [ ] Commit message is clear and descriptive
- [ ] You're on a feature branch (not main)

---

## 🎓 Where To Go Next

| Need | Resource |
|------|----------|
| Full CI/CD Guide | [CI_CD_GUIDE.md](CI_CD_GUIDE.md) |
| Architecture & Design | [docs/architecture.md](docs/architecture.md) |
| API Reference | [docs/api.md](docs/api.md) |
| Daily Operations | [docs/runbook.md](docs/runbook.md) |
| Fixing Issues | [docs/troubleshooting.md](docs/troubleshooting.md) |
| Deployment | [VERIFICATION_CHECKLIST.md](VERIFICATION_CHECKLIST.md) |

---

## 🆘 Need Help?

```powershell
# Check Python
python --version

# Check Docker
docker --version

# Check Git
git --version

# List installed packages
pip list

# See what's running
docker-compose ps

# Check tests
pytest tests/ -v

# Check code quality
black --check src/ tests/
flake8 src/ tests/
mypy src/
```

---

## 🎊 You're Ready!

You now know:
- ✅ How to run tests
- ✅ How to check code quality
- ✅ How to use Git
- ✅ How to trigger CI/CD
- ✅ How to debug failures

**Next step:** Make a change, test it, and push!

```powershell
# Try it now:
pytest tests/ -v
```

**Enjoy! 🚀**
