# 🚀 CI/CD Quick Start Guide

Get your CI/CD pipeline running in 15 minutes!

---

## 📋 Prerequisites

- GitHub account
- AWS account with credentials
- Repository access

---

## ⚡ Quick Setup (5 Steps)

### 1️⃣ Enable GitHub Actions (2 min)

```bash
# Go to your repository
Settings → Actions → General

# Enable
✅ Allow all actions and reusable workflows
✅ Read and write permissions
```

### 2️⃣ Add Secrets (5 min)

```bash
# Go to repository settings
Settings → Secrets and variables → Actions → New repository secret

# Add these secrets:
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=ap-south-1
S3_BUCKET=churn-pipeline-artifacts

RDS_HOST=your-rds-endpoint.amazonaws.com
RDS_PORT=5432
RDS_DB_NAME=analytics
RDS_USERNAME=admin
RDS_PASSWORD=your-password

MLFLOW_TRACKING_URI=http://your-mlflow-server.com
```

### 3️⃣ Create Environments (3 min)

```bash
# Go to repository settings
Settings → Environments

# Create "staging" environment
Name: staging
Deployment branches: main

# Create "production" environment  
Name: production
Deployment branches: main
✅ Required reviewers: [Add yourself]
```

### 4️⃣ Test CI Pipeline (3 min)

```bash
# Make a small change
echo "# Test" >> README.md
git add README.md
git commit -m "test: trigger CI"
git push

# Watch it run
Go to: Actions → CI - Continuous Integration
```

### 5️⃣ Deploy to Staging (2 min)

```bash
# Trigger deployment
Actions → CD - Continuous Deployment → Run workflow
- Branch: main
- Environment: staging
- Click "Run workflow"

# Monitor deployment
Watch the workflow progress in Actions tab
```

---

## ✅ Verification

### Check CI is Working

```bash
# You should see green checkmarks for:
✅ Code Quality Checks
✅ Unit Tests
✅ Integration Tests
✅ Data Validation
✅ Model Validation
```

### Check Docker Build is Working

```bash
# You should see:
✅ Base Image Built
✅ Pipeline Images Built
✅ Kafka Images Built
✅ Airflow Image Built
✅ Security Scan Passed
```

### Check Deployment is Working

```bash
# You should see:
✅ Pre-Deployment Checks
✅ Deploy to Staging
✅ Model Deployment
✅ Post-Deployment Validation
```

---

## 🎯 Next Steps

### 1. Train Your First Model

```bash
Actions → Model Training Pipeline → Run workflow
- Engine: pandas
- Experiment name: churn-prediction
- Run workflow
```

### 2. Set Up Monitoring

```bash
# Monitoring runs automatically every 6 hours
# Check it manually:
Actions → ML Model Monitoring → Run workflow
```

### 3. Deploy to Production

```bash
# After staging is verified:
Actions → CD - Continuous Deployment → Run workflow
- Branch: main
- Environment: production
- Run workflow
- Approve the deployment when prompted
```

---

## 🐛 Troubleshooting

### Issue: CI Tests Failing

```bash
# Check the logs
Actions → CI → [failed run] → [failed job] → [failed step]

# Common fixes:
- Install missing dependencies
- Fix code formatting (run black locally)
- Fix linting errors (run flake8 locally)
```

### Issue: Docker Build Failing

```bash
# Check Dockerfiles
docker build -f docker/Dockerfile.base -t test .

# Common issues:
- Wrong file paths in COPY commands
- Missing dependencies in requirements.txt
- Base image version issues
```

### Issue: Deployment Failing

```bash
# Check AWS credentials
aws sts get-caller-identity

# Check if services are running
aws ecs list-services --cluster staging

# Check RDS connection
psql "host=$RDS_HOST port=5432 dbname=$RDS_DB_NAME user=$RDS_USERNAME"
```

### Issue: Secrets Not Working

```bash
# Verify secrets are set
Settings → Secrets and variables → Actions

# Check secret names match exactly
# Secrets are case-sensitive!
```

---

## 📊 Monitoring Your Pipeline

### View Workflow Runs

```bash
# All runs
Actions → Select workflow → View runs

# Filter by status
✅ Successful runs: Green checkmark
❌ Failed runs: Red X
🟡 In progress: Yellow circle
```

### Check Logs

```bash
# Click on any workflow run
→ Select job
→ Expand step
→ View logs
```

### Download Artifacts

```bash
# At the bottom of workflow run page
Artifacts → Download

# Available artifacts:
- Coverage reports
- Test results
- Security scans
- Model artifacts
- Training reports
```

---

## 🎓 Learning Resources

- **Full Documentation**: `docs/CI_CD_GUIDE.md`
- **GitHub Actions**: https://docs.github.com/en/actions
- **AWS Deployment**: `docs/DEPLOYMENT_GUIDE.md`
- **MLflow**: `docs/MLFLOW_GUIDE.md`

---

## ✨ You're All Set!

Your CI/CD pipeline is now running. Every time you push code:

1. ✅ CI tests run automatically
2. ✅ Docker images are built and pushed
3. ✅ Code is deployed to staging
4. ✅ Model performance is monitored
5. ✅ Ready for production deployment

**Happy Deploying! 🚀**

---

**Need Help?**
- 📖 Read full guide: `docs/CI_CD_GUIDE.md`
- 🐛 Report issues: GitHub Issues
- 💬 Ask questions: GitHub Discussions

