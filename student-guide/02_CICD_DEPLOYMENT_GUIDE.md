# CI/CD & Deployment - Your Complete Guide

**Learn how to automatically test and deploy your ML system like a pro**

Welcome! 👋 This guide will teach you how to set up automated testing and deployment for your machine learning project. By the end, you'll understand how software teams ship code safely and quickly - a critical skill for any ML engineer.

---

## What You'll Learn

By the end of this guide, you'll be able to:
- Explain what CI/CD is and why it matters
- Set up automated testing using GitHub Actions
- Validate data quality automatically
- Ensure model performance before deployment
- Deploy code safely without breaking things
- Roll back quickly if something goes wrong
- Follow professional software development workflows

**Time to Complete**: 2-3 hours (including hands-on practice)

---

## Prerequisites

Before starting, make sure you have:
- [x] A GitHub account
- [x] Git installed on your machine
- [x] Basic understanding of Git (commit, push, pull)
- [x] Familiarity with Docker
- [x] The project code cloned locally

---

## Table of Contents

1. [What is CI/CD? A Simple Explanation](#what-is-cicd-a-simple-explanation)
2. [Why Do We Need CI/CD?](#why-do-we-need-cicd)
3. [Understanding Git Workflows](#understanding-git-workflows)
4. [Setting Up GitHub Actions](#setting-up-github-actions)
5. [Data Validation Pipeline](#data-validation-pipeline)
6. [Model Validation Pipeline](#model-validation-pipeline)
7. [Your First CI/CD Test](#your-first-cicd-test)
8. [Deployment Strategies Explained](#deployment-strategies-explained)
9. [Troubleshooting CI/CD Failures](#troubleshooting-cicd-failures)
10. [Best Practices](#best-practices)

---

## What is CI/CD? A Simple Explanation

Let's break down this intimidating acronym:

### CI = Continuous Integration

**"Continuous"** means "all the time"  
**"Integration"** means "combining code changes"

**In simple terms**: Every time you push code, it's automatically tested.

### CD = Continuous Deployment

**"Continuous"** means "all the time"  
**"Deployment"** means "putting code into production"

**In simple terms**: If tests pass, code is automatically deployed.

### A Real-World Analogy

Think of CI/CD like a car factory assembly line:

**Without CI/CD (Old Way):**
```
Developer writes code → (wait 1 week) →
QA tests manually → (wait 2 days) →
Fix bugs → (wait 1 week) →
Ops team deploys → (pray it works) 🙏
```
Total time: 2-3 weeks to deploy a small change!

**With CI/CD (Modern Way):**
```
Developer pushes code → Tests run automatically (2 min) →
If tests pass → Deploy automatically (5 min) →
Live in production (7 minutes total!) 🚀
```

---

## Why Do We Need CI/CD?

Let me tell you a story...

### The Horror Story (Without CI/CD)

It's Friday afternoon. You've been working on a new feature all week. You push your code to production. Suddenly:

- ❌ The app crashes
- ❌ The database is corrupted
- ❌ Customers can't access their accounts
- ❌ Your boss is calling you...
- ❌ You spend all weekend fixing it

**What went wrong?**
- You forgot to test with the new data format
- A library version changed
- Someone else pushed conflicting code
- The model accuracy dropped below acceptable levels

### The Happy Story (With CI/CD)

It's Friday afternoon. You push your code. Within 2 minutes:

- ✅ Automated tests run
- ✅ Data validation catches the wrong data format
- ✅ Model validation catches the accuracy drop
- ✅ Build fails (before reaching production!)
- ✅ You get a notification with the exact issue
- ✅ You fix it in 10 minutes
- ✅ Push again, tests pass, auto-deploys
- ✅ You go home on time! 😊

### The Benefits (Why Everyone Uses CI/CD)

| Without CI/CD | With CI/CD |
|---------------|-----------|
| Manual testing (slow, error-prone) | Automated testing (fast, reliable) |
| Deploy once a month | Deploy multiple times a day |
| Bugs reach production | Bugs caught before production |
| Hours to fix issues | Minutes to fix issues |
| High stress 😰 | Lower stress 😊 |

---

## Understanding Git Workflows

Before we dive into CI/CD, let's understand how professional teams use Git.

### The Three-Branch Strategy

```
main (production) ← Only perfect, tested code
  ↑
  merge from
  │
develop (staging) ← Testing happens here
  ↑
  merge from
  │
feature/your-work ← You work here
```

### Branch Purposes

#### 1. **main** (Production Branch)

**Rules:**
- ✅ Only fully tested code
- ✅ Always deployable
- ✅ Protected (can't push directly)
- ✅ Requires pull request approval

**This is the code running for real users!**

#### 2. **develop** (Staging Branch)

**Rules:**
- ✅ Testing ground
- ⚠️ Usually stable, but can have small issues
- ✅ Where features are integrated
- ⚠️ Can push directly (but shouldn't)

**This is where you test before production!**

#### 3. **feature/*** (Your Work Branch)

**Rules:**
- ✅ Your personal workspace
- ✅ Can be messy
- ✅ Break things here without worry
- ✅ Delete after merging

**Examples:**
- `feature/add-kafka-consumer`
- `feature/fix-model-training`
- `feature/john-testing`

### The Development Workflow

Here's how a typical feature goes from idea to production:

```
Day 1 (Monday):
├─ Create feature branch from develop
├─ Write code
└─ Push to feature branch
   └─ CI/CD runs tests ✅

Day 2 (Tuesday):
├─ Continue coding
├─ Push again
└─ CI/CD runs tests ✅

Day 3 (Wednesday):
├─ Feature complete
├─ Create PR: feature → develop
├─ CI/CD runs tests ✅
├─ Team reviews code
└─ Merge to develop
   └─ Deploy to staging environment

Day 4-5 (Thu-Fri):
├─ Test on staging
└─ If everything works:
   └─ Create PR: develop → main
      ├─ CI/CD runs tests ✅
      ├─ Boss approves
      └─ Merge to main
         └─ Auto-deploy to production 🚀
```

### Why This Workflow?

**Question**: "Why so many branches? Can't I just work on main?"

**Answer**: Safety and collaboration!

Imagine 5 developers all pushing to main:
- Developer A breaks the database
- Developer B's code conflicts with C's code
- Developer D's feature is half-done
- Developer E just deployed... and everything crashes!

With branches:
- Everyone works independently
- Test before integrating
- Easy to find who broke what
- Easy to roll back bad changes

---

## Setting Up GitHub Actions

GitHub Actions is GitHub's built-in CI/CD tool. It's free for public repos!

### How GitHub Actions Works

```
You push code → GitHub detects push → Triggers workflow → Runs tests → Reports results
```

All of this happens automatically in the cloud (GitHub's servers).

### Understanding the Workflow File

Your project already has this file: `.github/workflows/ci.yml`

Let's break it down piece by piece:

```yaml
name: Simplified CI/CD Pipeline  # ← Shows up on GitHub

on:  # ← WHEN to run this workflow
  push:  # ← When code is pushed
    branches:
      - main      # ← Only for these branches
      - develop
      - 'feature/**'  # ← Any feature branch
  pull_request:  # ← When PR is created
    branches:
      - main
      - develop
```

**What this means:**
- Workflow runs on every push to main, develop, or feature branches
- Also runs when you create a pull request
- Does NOT run for commits you make locally (only after pushing)

### The Jobs

Our CI/CD pipeline has 4 jobs that run in sequence:

```yaml
jobs:
  data-validation:      # Job 1: Check data quality
    runs-on: ubuntu-latest  # ← Use Ubuntu Linux
    steps:
      - Checkout code
      - Install Python
      - Run data validation script
      - Upload report

  model-validation:     # Job 2: Check model performance
    needs: data-validation  # ← Only run if Job 1 passes
    steps:
      - Download model from S3
      - Run model validation
      - Check F1 score ≥ 75%
      - If fails, block deployment

  docker-build:         # Job 3: Build Docker images
    needs: [data-validation, model-validation]  # ← Only if both pass
    if: github.ref == 'refs/heads/main'  # ← Only on main branch
    steps:
      - Build Docker images
      - Push to Docker Hub

  deploy:               # Job 4: Deploy to production
    needs: docker-build  # ← Only if build succeeds
    if: github.ref == 'refs/heads/main'  # ← Only on main branch
    steps:
      - Deploy to production
      - Run health checks
```

### Visualizing the Flow

```
Push to feature/my-work:
  └─ Job 1: Data Validation ✅
     └─ Job 2: Model Validation ✅
        └─ STOP (not on main, don't deploy)

Push to main:
  └─ Job 1: Data Validation ✅
     └─ Job 2: Model Validation ✅
        └─ Job 3: Docker Build ✅
           └─ Job 4: Deploy ✅
              └─ Live in production! 🚀
```

### GitHub Secrets (Keeping Passwords Safe)

You'll notice things like `${{ secrets.AWS_ACCESS_KEY_ID }}` in the workflow.

**Never, EVER put passwords in code!**

Instead, store them as GitHub Secrets:

1. Go to your GitHub repo
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add these secrets:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `S3_BUCKET`
   - `RDS_HOST`
   - `RDS_PASSWORD`
   - `DOCKER_USERNAME`
   - `DOCKER_PASSWORD`

The workflow can access these securely, but humans can't see them (even you!)

---

## Data Validation Pipeline

The first job in our CI/CD pipeline checks if the data is good quality.

### Why Validate Data?

**Scenario**: You trained a model with data where Age ranges from 18-100. But new data comes in with Age = 300!

Without validation:
- Model makes weird predictions
- Accuracy drops
- Customers get wrong recommendations
- Nobody knows why! 🤷

With validation:
- Pipeline catches Age = 300
- Deployment blocked ❌
- You get notified
- Fix the data
- Try again ✅

### What We Check

Our data validation script (`tests/validate_data.py`) checks:

#### 1. **Schema Validation**

```python
# Do we have all required columns?
required_columns = [
    'CustomerId', 'CreditScore', 'Geography', 'Gender',
    'Age', 'Tenure', 'Balance', 'NumOfProducts',
    'HasCrCard', 'IsActiveMember', 'EstimatedSalary', 'Exited'
]

missing = [col for col in required_columns if col not in data.columns]

if missing:
    raise ValueError(f"Missing columns: {missing}")
```

**Example failure:**
```
❌ VALIDATION FAILED
   Missing required columns: ['CreditScore']
```

#### 2. **Data Type Validation**

```python
# Are data types correct?
if data['Age'].dtype != 'int64':
    raise TypeError("Age must be integer")

if data['Balance'].dtype != 'float64':
    raise TypeError("Balance must be float")
```

**Example failure:**
```
❌ VALIDATION FAILED
   Column Age has type object, expected int64
```

#### 3. **Value Range Validation**

```python
# Are values in expected ranges?
if (data['Age'] < 18).any() or (data['Age'] > 100).any():
    raise ValueError("Age must be between 18 and 100")

if (data['NumOfProducts'] < 1).any() or (data['NumOfProducts'] > 4).any():
    raise ValueError("NumOfProducts must be between 1 and 4")
```

**Example failure:**
```
❌ VALIDATION FAILED
   Column Age has 15 values outside range [18, 100]
```

#### 4. **Categorical Value Validation**

```python
# Are categorical values valid?
valid_geographies = ['France', 'Germany', 'Spain']
invalid = ~data['Geography'].isin(valid_geographies)

if invalid.any():
    raise ValueError(f"Invalid geography: {data[invalid]['Geography'].unique()}")
```

**Example failure:**
```
❌ VALIDATION FAILED
   Invalid geography values: ['USA', 'Canada']
```

#### 5. **Missing Value Check**

```python
# Any missing values?
missing = data.isnull().sum()
if missing.any():
    print(f"⚠️ Missing values found:\n{missing[missing > 0]}")
```

**Example warning:**
```
⚠️ Missing values found:
   CreditScore    15
   Balance         3
```

#### 6. **Data Drift Detection**

```python
# Has the data distribution changed significantly?
from scipy import stats

for col in numeric_columns:
    ks_stat, p_value = stats.ks_2samp(new_data[col], reference_data[col])
    
    if p_value < 0.05:  # Significant change
        print(f"⚠️ DRIFT DETECTED in {col} (p={p_value:.4f})")
```

**What this means:**
- If your training data had average Age = 40
- And new data has average Age = 65
- This is "drift" - the data changed!
- Your model might not work well anymore

**Example warning:**
```
⚠️ DRIFT DETECTED in Age (p=0.0023)
⚠️ DRIFT DETECTED in Balance (p=0.0156)
```

### Running Data Validation Locally

Before pushing code, test locally:

```bash
# Run data validation
python tests/validate_data.py data/raw/ChurnModelling.csv

# Expected output if everything is good:
✅ All required columns present
✅ Data types valid
✅ Value ranges valid
✅ Categorical values valid
✅ No missing values
✅ ALL VALIDATIONS PASSED
```

If something fails:
```
❌ VALIDATION FAILED - 2 errors:
   • Column Age has 3 values outside range [18, 100]
   • Invalid geography values: ['USA']
```

Fix the issues before pushing!

---

## Model Validation Pipeline

The second job checks if your ML model is good enough for production.

### The Golden Rule: F1 Score ≥ 75%

In our project, we've set a rule:

**If F1 score < 75%, the model CANNOT be deployed!**

Why F1 score? Because it balances:
- **Precision**: Don't predict churn when customer won't churn (false positives)
- **Recall**: Don't miss customers who will churn (false negatives)

### Understanding F1 Score (Simple Explanation)

Imagine you're a doctor diagnosing a disease:

**Scenario 1: Precision is low**
- You say 100 people have the disease
- But only 50 actually have it
- Result: 50 people get unnecessary treatment 😢

**Scenario 2: Recall is low**
- You correctly identify 50 people with the disease
- But you miss 50 others who have it
- Result: 50 people don't get treatment they need 😢

**F1 Score balances both!**
- High F1 = Good precision AND good recall
- F1 = 75% is pretty good for most ML problems
- F1 = 90%+ is excellent

### What the Model Validation Checks

```python
# Calculate metrics
predictions = model.predict(X_test)
probabilities = model.predict_proba(X_test)[:, 1]

metrics = {
    'accuracy': accuracy_score(y_test, predictions),
    'precision': precision_score(y_test, predictions),
    'recall': recall_score(y_test, predictions),
    'f1': f1_score(y_test, predictions),
    'roc_auc': roc_auc_score(y_test, probabilities)
}

# Check threshold
if metrics['f1'] < 0.75:
    print("❌ MODEL REJECTED")
    print(f"   F1 Score: {metrics['f1']*100:.2f}% < 75.00%")
    sys.exit(1)  # ← This fails the CI/CD pipeline
else:
    print("✅ MODEL APPROVED FOR DEPLOYMENT")
    print(f"   F1 Score: {metrics['f1']*100:.2f}% ≥ 75.00%")
```

### Example Validation Report

**Passing Model:**
```
🎯 MODEL VALIDATION STARTED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Performance Metrics:
   Accuracy:   86.50%
   Precision:  82.30%
   Recall:     78.90%
   F1 Score:   80.55%  ← Above threshold!
   ROC-AUC:    0.8934

📊 Confusion Matrix:
   TN: 1689    FP: 123
   FN: 95      TP: 356

🎯 Threshold Check:
   Required F1 Score: ≥ 75%
   Actual F1 Score:   80.55%

✅ MODEL APPROVED FOR DEPLOYMENT
```

**Failing Model:**
```
🎯 MODEL VALIDATION STARTED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Performance Metrics:
   Accuracy:   79.20%
   Precision:  68.50%
   Recall:     76.30%
   F1 Score:   72.20%  ← Below threshold!

❌ MODEL REJECTED
   F1 Score (72.20%) below threshold (75.00%)

🔄 REVERTING TO PREVIOUS MODEL
```

### What Happens When Model Fails?

The CI/CD pipeline:
1. ❌ Stops the deployment
2. 📧 Sends you a notification
3. 📊 Generates a report showing what went wrong
4. 🔄 Keeps the old model in production (safe fallback!)
5. 📝 Logs the failure for future reference

You then:
1. Investigate why F1 dropped
2. Retrain with better data or different parameters
3. Push again
4. CI/CD re-runs validation
5. If it passes → automatic deployment! ✅

### Running Model Validation Locally

```bash
# Run model validation
python tests/validate_model.py \
    artifacts/models/best_model.pkl \
    artifacts/data/test_data.pkl

# Or with custom threshold
python tests/validate_model.py \
    artifacts/models/best_model.pkl \
    artifacts/data/test_data.pkl \
    0.80  # ← 80% threshold
```

---

## Your First CI/CD Test

Let's walk through actually using the CI/CD pipeline!

### Step 1: Create a Feature Branch

```bash
# Make sure you're on develop
git checkout develop
git pull origin develop

# Create your feature branch
git checkout -b feature/test-cicd

# Verify you're on the right branch
git branch
# Should show: * feature/test-cicd
```

### Step 2: Make a Small Change

Let's add a comment to test the pipeline:

```bash
# Edit the README
echo "<!-- Testing CI/CD pipeline -->" >> README.md

# Check what changed
git diff README.md
```

### Step 3: Commit and Push

```bash
# Stage the change
git add README.md

# Commit with a clear message
git commit -m "test: verify CI/CD pipeline works"

# Push to GitHub
git push origin feature/test-cicd
```

### Step 4: Watch GitHub Actions

1. **Go to your GitHub repository**
2. **Click the "Actions" tab**
3. **You should see your workflow running!**

```
🟡 Simplified CI/CD Pipeline (Running...)
   ├─ 🟡 Data Validation (Running...)
   ├─ ⏸️  Model Validation (Waiting...)
   ├─ ⏸️  Docker Build (Waiting...)
   └─ ⏸️  Deploy (Waiting...)
```

**Wait 2-5 minutes...**

```
✅ Simplified CI/CD Pipeline (Success!)
   ├─ ✅ Data Validation (1m 23s)
   ├─ ✅ Model Validation (2m 45s)
   ├─ ⏭️  Docker Build (Skipped - not on main)
   └─ ⏭️  Deploy (Skipped - not on main)
```

### Step 5: Click Into the Workflow

Click on "Simplified CI/CD Pipeline" to see details:

```
Jobs:
├─ data-validation
│  ├─ Checkout Code ✅
│  ├─ Set up Python ✅
│  ├─ Install Dependencies ✅
│  ├─ Run Data Validation ✅
│  │  └─ ✅ All required columns present
│  │     ✅ Data types valid
│  │     ✅ Value ranges valid
│  │     ✅ ALL VALIDATIONS PASSED
│  └─ Upload Validation Report ✅
│
├─ model-validation
│  ├─ Download Model from S3 ✅
│  ├─ Run Model Validation ✅
│  │  └─ ✅ MODEL APPROVED FOR DEPLOYMENT
│  │     F1 Score: 80.55% exceeds threshold (75%)
│  └─ Upload Model Report ✅
```

Congrats! Your first CI/CD run! 🎉

### Step 6: Create a Pull Request

Now let's merge to develop:

1. **On GitHub, click "Pull requests" tab**
2. **Click "New pull request"**
3. **Set:**
   - Base: `develop`
   - Compare: `feature/test-cicd`
4. **Click "Create pull request"**
5. **Fill in the description:**

```markdown
## Changes
- Added comment to README to test CI/CD

## Testing
- ✅ CI/CD pipeline passed on feature branch
- ✅ Data validation: PASSED
- ✅ Model validation: PASSED

## Checklist
- [x] Code follows style guidelines
- [x] CI/CD passes
- [x] No breaking changes
```

6. **CI/CD runs again!** (on the PR)
7. **If passes → Click "Merge pull request"**
8. **Delete the feature branch** (GitHub offers this button)

### Step 7: Verify on Develop

```bash
# Switch to develop locally
git checkout develop

# Pull the merged changes
git pull origin develop

# You should see your changes!
cat README.md | tail -1
# Should show: <!-- Testing CI/CD pipeline -->
```

---

## Deployment Strategies Explained

Now that code is tested, how do we deploy it safely?

### Strategy 1: Simple Restart (Development)

**Best for**: Local development, testing

```bash
# Stop everything
docker-compose down

# Start again with new code
docker-compose up -d
```

**Pros:**
- ✅ Simple
- ✅ Fast
- ✅ Works for small projects

**Cons:**
- ❌ Downtime (services offline during restart)
- ❌ All-or-nothing (can't roll back easily)

### Strategy 2: Rolling Deployment (Recommended)

**Best for**: Production with moderate traffic

**How it works:**
```
Step 1: You have 3 instances running (old code)
        [Old] [Old] [Old]

Step 2: Stop 1 instance, deploy new code
        [New] [Old] [Old]  ← 2 still serving traffic

Step 3: If working, update next instance
        [New] [New] [Old]  ← Still 2 serving traffic

Step 4: Update last instance
        [New] [New] [New]  ← All updated!
```

**Pros:**
- ✅ Zero downtime (always have instances running)
- ✅ Gradual rollout (can stop if issues detected)
- ✅ Easy rollback (keep old images)

**Cons:**
- ⚠️ Requires load balancer
- ⚠️ Slightly complex setup

**Example with Docker Compose:**
```bash
# Update services one by one
docker-compose up -d --no-deps --build kafka-producer
# Wait and verify...

docker-compose up -d --no-deps --build kafka-consumer
# Wait and verify...

docker-compose up -d --no-deps --build analytics
# Wait and verify...
```

### Strategy 3: Blue-Green Deployment (Advanced)

**Best for**: Critical systems that need instant rollback

**How it works:**
```
Before deployment:
  Blue Environment (active) ← Traffic goes here
  Green Environment (idle)

During deployment:
  Blue Environment (active) ← Still serving traffic
  Green Environment (deploying new code)

After testing:
  Blue Environment (idle) ← Switch traffic
  Green Environment (active) ← Now serving traffic

If issues found:
  Just switch back to Blue! (instant rollback)
```

**Pros:**
- ✅ Zero downtime
- ✅ Instant rollback
- ✅ Full testing before cutover

**Cons:**
- ❌ Requires 2x resources (expensive)
- ❌ Complex infrastructure
- ❌ Database migrations tricky

### Strategy 4: Canary Deployment (Safest)

**Best for**: Very large systems (like Netflix)

**How it works:**
```
Step 1: Deploy new code to 5% of servers
        5% users see new version
        95% users see old version

Step 2: Monitor for 1 hour
        If error rate increases → Rollback
        If everything good → Continue

Step 3: Deploy to 25% of servers
        Monitor again...

Step 4: Deploy to 100% of servers
        Full rollout complete!
```

**Pros:**
- ✅ Lowest risk (only 5% affected if broken)
- ✅ Real user testing
- ✅ Data-driven rollout

**Cons:**
- ❌ Complex infrastructure
- ❌ Requires sophisticated monitoring
- ❌ Slower rollout

### Which Strategy Should You Use?

| Project Size | Traffic | Recommended Strategy |
|--------------|---------|---------------------|
| Personal project | Low | Simple Restart |
| Small startup | Medium | Rolling Deployment |
| Growing company | High | Blue-Green |
| Large enterprise | Very high | Canary |

**For this course:** Use Rolling Deployment (good balance)

---

## Troubleshooting CI/CD Failures

When CI/CD fails, don't panic! Here's how to debug:

### Step 1: Read the Error Message

```
❌ Data Validation Failed (1m 23s)
   └─ Run Data Validation
      └─ ❌ VALIDATION FAILED - 2 errors:
         • Column Age has 3 values outside range [18, 100]
         • Invalid geography values: ['USA']
```

**This tells you exactly what's wrong!**

### Step 2: Check the Logs

Click on the failed job → Click on the failed step → Read full logs

### Step 3: Reproduce Locally

```bash
# Run the same validation that failed
python tests/validate_data.py data/raw/ChurnModelling.csv

# You should see the same error
```

### Step 4: Fix the Issue

```python
# Find the bad data
df = pd.read_csv('data/raw/ChurnModelling.csv')
print(df[df['Age'] > 100])  # Find bad ages
print(df[df['Geography'] == 'USA'])  # Find bad geography

# Fix the data
df = df[df['Age'] <= 100]  # Remove invalid ages
df = df[df['Geography'].isin(['France', 'Germany', 'Spain'])]  # Remove invalid geography

# Save fixed data
df.to_csv('data/raw/ChurnModelling.csv', index=False)
```

### Step 5: Test Again Locally

```bash
# Run validation again
python tests/validate_data.py data/raw/ChurnModelling.csv

# Should now pass:
✅ ALL VALIDATIONS PASSED
```

### Step 6: Push the Fix

```bash
git add data/raw/ChurnModelling.csv
git commit -m "fix: remove invalid age and geography values"
git push origin feature/test-cicd

# CI/CD will run again automatically!
```

### Common Failure Scenarios

#### Failure 1: Data Validation - Missing Columns

**Error:**
```
❌ Missing required columns: ['CreditScore']
```

**Cause:** CSV file is missing the CreditScore column

**Fix:**
```bash
# Check CSV columns
head -1 data/raw/ChurnModelling.csv

# Make sure it has all required columns
```

#### Failure 2: Model Validation - F1 Too Low

**Error:**
```
❌ MODEL REJECTED
   F1 Score (72.20%) below threshold (75.00%)
```

**Cause:** Model performance dropped (maybe due to data changes)

**Fixes:**
1. **Retrain the model:**
   ```bash
   python pipelines/training_pipeline.py
   ```

2. **Check if data quality is good:**
   ```bash
   python tests/validate_data.py data/raw/ChurnModelling.csv
   ```

3. **If desperate, lower threshold temporarily:**
   ```python
   # In tests/validate_model.py
   f1_threshold = 0.70  # Lower from 0.75 (NOT RECOMMENDED!)
   ```

#### Failure 3: Docker Build Failed

**Error:**
```
❌ Docker Build Failed
   Error: COPY failed: file not found: requirements.txt
```

**Cause:** Docker can't find a file

**Fixes:**
1. **Check if file exists:**
   ```bash
   ls -la requirements.txt
   ```

2. **Check .dockerignore:**
   ```bash
   cat .dockerignore
   # Make sure requirements.txt is NOT ignored
   ```

3. **Test build locally:**
   ```bash
   docker build -f docker/Dockerfile.kafka-consumer -t test .
   ```

#### Failure 4: AWS Credentials Invalid

**Error:**
```
❌ Download Model from S3
   Error: An error occurred (InvalidAccessKeyId)
```

**Cause:** AWS credentials in GitHub Secrets are wrong

**Fix:**
1. Go to GitHub → Settings → Secrets
2. Update `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
3. Make sure they're correct (test locally first)

---

## Best Practices

### 1. Always Test Locally First

```bash
# Before pushing, always run:
python tests/validate_data.py data/raw/ChurnModelling.csv
python tests/validate_model.py artifacts/models/best_model.pkl artifacts/data/test_data.pkl
pytest tests/ -v
```

**Why?** Catch errors locally (faster feedback than waiting for GitHub Actions)

### 2. Write Clear Commit Messages

**Bad:**
```bash
git commit -m "fix"
git commit -m "update"
git commit -m "changes"
```

**Good:**
```bash
git commit -m "fix: correct age validation range to 18-100"
git commit -m "feat: add drift detection to data validation"
git commit -m "test: add unit tests for feature encoding"
```

**Format:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Testing
- `refactor:` - Code refactoring
- `chore:` - Maintenance

### 3. Keep Pull Requests Small

**Bad PR:**
- 50 files changed
- 2000 lines added
- Implements 5 features
- Nobody wants to review this! 😢

**Good PR:**
- 3 files changed
- 100 lines added
- Implements 1 feature
- Easy to review ✅

### 4. Never Skip CI/CD

**Tempting but dangerous:**
```bash
git push --no-verify  # Skips pre-push hooks
```

**Don't do this!** CI/CD exists to protect you.

### 5. Monitor After Deployment

After deploying:

```bash
# Watch logs
docker logs -f kafka-consumer

# Check error rates
# Check response times
# Check resource usage

# If anything looks wrong, rollback immediately!
```

### 6. Have a Rollback Plan

Before every deployment, know how to rollback:

```bash
# Keep previous Docker images
docker images

# Tag images with versions
docker tag app:latest app:v1.0.0

# If new deployment fails, rollback
docker-compose down
docker tag app:v1.0.0 app:latest
docker-compose up -d
```

---

## Key Takeaways

Congratulations! You now understand:

✅ **What CI/CD is**: Automated testing and deployment  
✅ **Why it matters**: Catch bugs early, deploy faster, reduce stress  
✅ **Git workflows**: Feature branches, PR reviews, protected main  
✅ **GitHub Actions**: Automated workflows triggered by pushes  
✅ **Data validation**: Ensuring data quality before training  
✅ **Model validation**: Ensuring model performance before deployment  
✅ **Deployment strategies**: Rolling, blue-green, canary  
✅ **Troubleshooting**: Reading errors, fixing issues, testing locally  

### Real-World Skills

You can now:
- Set up CI/CD for any project
- Write automated tests
- Use professional Git workflows
- Deploy safely to production
- Debug CI/CD failures
- Explain CI/CD to non-technical people

### Next Steps

1. **Practice**: Make more PRs, watch CI/CD run
2. **Experiment**: Try breaking tests intentionally (learn from failures)
3. **Customize**: Adjust thresholds in validation scripts
4. **Expand**: Add more tests (unit tests, integration tests)
5. **Document**: Write deployment runbooks

---

## Additional Resources

### Learning More

- **GitHub Actions Documentation**: https://docs.github.com/en/actions
- **Git Branching Strategies**: Search "Git Flow explained"
- **CI/CD Best Practices**: Search "DevOps CI/CD"

### Practice Projects

- Add pre-commit hooks for linting
- Set up staging environment
- Implement blue-green deployment
- Add performance testing to CI/CD

---

**Last Updated**: October 21, 2025  
**Maintained by**: Production ML Systems Course Team  
**Questions?** Check the troubleshooting section or ask your instructor!

Happy Deploying! 🚀

