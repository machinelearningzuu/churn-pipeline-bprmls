# 🚀 CI/CD Guide for Churn Prediction Pipeline

Complete guide for setting up and managing Continuous Integration and Continuous Deployment for the ML pipeline.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [GitHub Actions Workflows](#github-actions-workflows)
3. [Setup Instructions](#setup-instructions)
4. [Environment Configuration](#environment-configuration)
5. [Secrets Management](#secrets-management)
6. [Deployment Process](#deployment-process)
7. [Monitoring & Alerts](#monitoring--alerts)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

### CI/CD Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          GitHub Repository                       │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌──────────────┐  │
│  │ Feature  │→ │   Pull   │→ │  Develop  │→ │     Main     │  │
│  │ Branch   │  │  Request │  │  Branch   │  │   Branch     │  │
│  └──────────┘  └──────────┘  └───────────┘  └──────────────┘  │
│       │             │              │                │            │
└───────┼─────────────┼──────────────┼────────────────┼───────────┘
        │             │              │                │
        ▼             ▼              ▼                ▼
   ┌────────────────────────────────────────────────────────┐
   │                 GitHub Actions                         │
   │                                                         │
   │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐│
   │  │    CI    │  │  Docker  │  │   CD     │  │  ML    ││
   │  │ Testing  │  │  Build   │  │ Deploy   │  │Monitor ││
   │  └──────────┘  └──────────┘  └──────────┘  └────────┘│
   └────────────────────────────────────────────────────────┘
           │              │              │              │
           ▼              ▼              ▼              ▼
   ┌───────────┐  ┌────────────┐  ┌──────────┐  ┌───────────┐
   │ Code      │  │  Container │  │ Staging  │  │  Model    │
   │ Quality   │  │  Registry  │  │ & Prod   │  │ Metrics   │
   └───────────┘  └────────────┘  └──────────┘  └───────────┘
```

### Workflows Summary

| Workflow | Trigger | Purpose | Duration |
|----------|---------|---------|----------|
| **CI - Continuous Integration** | Push, PR | Code quality, tests | ~10 min |
| **Docker Build & Push** | Main, Develop, Tags | Build images | ~15 min |
| **CD - Deployment** | After Docker build | Deploy services | ~20 min |
| **ML Model Monitoring** | Every 6 hours | Check model health | ~5 min |
| **Model Training Pipeline** | Manual, Weekly | Train new models | ~45 min |

---

## 🔄 GitHub Actions Workflows

### 1. CI - Continuous Integration (`ci.yml`)

**Triggers:**
- Push to `main`, `develop`, `feature/**` branches
- Pull requests to `main`, `develop`

**Jobs:**
1. **Code Quality Checks**
   - Black (code formatting)
   - Flake8 (linting)
   - MyPy (type checking)
   - Pylint (static analysis)
   - Bandit (security scan)
   - Safety (dependency vulnerabilities)

2. **Unit Tests**
   - Multi-Python version testing (3.9, 3.10, 3.11)
   - Code coverage reporting
   - Parallel test execution

3. **Integration Tests**
   - Kafka integration
   - PostgreSQL integration
   - S3 integration

4. **Data Validation**
   - Schema validation
   - Data quality checks

5. **Model Validation**
   - Model performance checks
   - Model artifact validation

### 2. Docker Build & Push (`docker-build.yml`)

**Triggers:**
- Push to `main`, `develop`
- Version tags (`v*.*.*`)
- Manual dispatch

**Jobs:**
1. **Build Base Image**
   - Multi-platform (amd64, arm64)
   - Layer caching

2. **Build Pipeline Images**
   - Data pipeline
   - Model training
   - Inference service
   - MLflow

3. **Build Kafka Services**
   - Producer
   - Consumer
   - Analytics

4. **Build Airflow**
   - Scheduler
   - Webserver

5. **Security Scan**
   - Trivy vulnerability scanning
   - SARIF reports to GitHub Security

### 3. CD - Continuous Deployment (`cd-deploy.yml`)

**Triggers:**
- Successful Docker build on `main`
- Manual deployment with environment selection

**Environments:**
- **Staging**: Automatic deployment from `main`
- **Production**: Manual approval required

**Jobs:**
1. **Pre-Deployment Validation**
   - AWS credentials check
   - RDS availability
   - S3 access

2. **Deploy to Staging**
   - Update configuration
   - Database migrations
   - ECS service update
   - Health checks
   - Smoke tests

3. **Deploy to Production**
   - Create backup
   - Blue-green deployment
   - Traffic switching
   - Monitoring
   - Rollback on failure

4. **Model Deployment**
   - MLflow model registration
   - S3 model version update
   - Trigger model reload

5. **Post-Deployment Validation**
   - Integration tests
   - Kafka validation
   - MLflow tracking check
   - RDS analytics verification

### 4. ML Model Monitoring (`ml-monitoring.yml`)

**Triggers:**
- Schedule: Every 6 hours
- Manual dispatch

**Jobs:**
1. **Model Performance Monitoring**
   - Accuracy tracking
   - Prediction distribution
   - Confidence scores

2. **Data Drift Detection**
   - Statistical tests (KS test, Chi-square)
   - Feature distribution comparison
   - HTML drift reports

3. **Prediction Quality Check**
   - Anomaly detection
   - Confidence analysis

4. **Retrain Trigger**
   - Automatic retraining if thresholds exceeded

### 5. Model Training Pipeline (`model-training.yml`)

**Triggers:**
- Manual dispatch with parameters
- Weekly schedule (Sunday 2 AM UTC)

**Jobs:**
1. **Data Pipeline**
   - Data processing
   - Feature engineering
   - Data validation

2. **Model Training**
   - Train with specified engine (pandas/spark)
   - MLflow experiment tracking
   - Hyperparameter tuning

3. **Model Evaluation**
   - Performance metrics
   - Approval gate (accuracy >= 80%)

4. **Model Registration**
   - Register in MLflow
   - Version tagging
   - Metadata storage

---

## ⚙️ Setup Instructions

### 1. Fork/Clone Repository

```bash
git clone https://github.com/yourusername/churn-pipeline.git
cd churn-pipeline
```

### 2. Enable GitHub Actions

1. Go to repository **Settings** → **Actions** → **General**
2. Enable **Allow all actions and reusable workflows**
3. Enable **Read and write permissions** for workflows

### 3. Configure Branch Protection

```bash
# Main branch protection
Settings → Branches → Add rule:
- Branch name pattern: main
- ✅ Require pull request reviews (1 reviewer)
- ✅ Require status checks to pass
- ✅ Require conversation resolution before merging
- ✅ Include administrators
```

### 4. Set Up Environments

```bash
# GitHub Settings → Environments

# Staging Environment
- Name: staging
- Deployment branches: main
- Environment secrets: (staging AWS credentials)

# Production Environment
- Name: production
- Deployment branches: main
- Required reviewers: (add team members)
- Environment secrets: (production AWS credentials)
```

---

## 🔐 Secrets Management

### Required GitHub Secrets

#### Repository Secrets (Settings → Secrets and variables → Actions)

**AWS Credentials:**
```bash
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=ap-south-1
S3_BUCKET=churn-pipeline-artifacts
```

**RDS Configuration:**
```bash
RDS_HOST=churn-pipeline-db.xxxx.ap-south-1.rds.amazonaws.com
RDS_PORT=5432
RDS_DB_NAME=analytics
RDS_USERNAME=admin
RDS_PASSWORD=...
```

**MLflow:**
```bash
MLFLOW_TRACKING_URI=http://mlflow.yourcompany.com
```

**Notifications (Optional):**
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
PAGERDUTY_TOKEN=...
```

#### Environment-Specific Secrets

**Staging:**
```bash
AWS_ACCESS_KEY_ID_STAGING=...
RDS_HOST_STAGING=...
MLFLOW_TRACKING_URI_STAGING=...
```

**Production:**
```bash
AWS_ACCESS_KEY_ID_PROD=...
RDS_HOST_PROD=...
MLFLOW_TRACKING_URI_PROD=...
```

### Adding Secrets via CLI

```bash
# Using GitHub CLI
gh secret set AWS_ACCESS_KEY_ID -b"AKIA..."
gh secret set AWS_SECRET_ACCESS_KEY -b"..."
gh secret set RDS_PASSWORD -b"..."

# For environment-specific secrets
gh secret set AWS_ACCESS_KEY_ID_PROD --env production -b"AKIA..."
```

---

## 🚢 Deployment Process

### Development Workflow

```bash
# 1. Create feature branch
git checkout -b feature/new-model-architecture

# 2. Make changes
git add .
git commit -m "feat: implement new model architecture"

# 3. Push and create PR
git push origin feature/new-model-architecture

# 4. CI runs automatically on PR
#    - Code quality checks
#    - Unit tests
#    - Integration tests

# 5. Code review + approval

# 6. Merge to develop
#    - CI runs again
#    - Docker images built (develop tags)

# 7. Merge develop to main (when ready for release)
#    - CI + Docker build
#    - Automatic deployment to staging
#    - Manual approval for production
```

### Manual Deployment

```bash
# Via GitHub UI
Actions → CD - Continuous Deployment → Run workflow
- Select branch: main
- Select environment: staging or production
- Click "Run workflow"

# Monitor deployment
Actions → CD - Continuous Deployment → [workflow run]
```

### Model Training Workflow

```bash
# Via GitHub UI
Actions → Model Training Pipeline → Run workflow
- Training engine: pandas or spark
- Experiment name: churn-prediction
- Click "Run workflow"

# Via GitHub CLI
gh workflow run model-training.yml \
  -f engine=pandas \
  -f experiment_name=churn-prediction-v2
```

---

## 📊 Monitoring & Alerts

### CloudWatch Integration

```yaml
# Add to workflows for CloudWatch metrics
- name: Send Metrics to CloudWatch
  run: |
    aws cloudwatch put-metric-data \
      --namespace "ChurnPipeline" \
      --metric-name "DeploymentSuccess" \
      --value 1
```

### Slack Notifications

```yaml
# Add to workflow for Slack alerts
- name: Notify Slack
  if: always()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### GitHub Actions Badges

Add to `README.md`:

```markdown
![CI](https://github.com/yourusername/churn-pipeline/workflows/CI/badge.svg)
![Docker](https://github.com/yourusername/churn-pipeline/workflows/Docker%20Build/badge.svg)
![Deploy](https://github.com/yourusername/churn-pipeline/workflows/CD/badge.svg)
```

---

## 🎯 Best Practices

### 1. Commit Message Convention

```bash
# Use conventional commits
feat: add new feature
fix: fix bug
docs: update documentation
test: add tests
ci: update CI/CD
chore: maintenance tasks
```

### 2. Pull Request Guidelines

- ✅ Link to issue/ticket
- ✅ Clear description of changes
- ✅ Screenshots for UI changes
- ✅ Update tests
- ✅ Update documentation
- ✅ Request review from team

### 3. Code Review Checklist

- ✅ Code follows style guide
- ✅ Tests are passing
- ✅ No security vulnerabilities
- ✅ Documentation updated
- ✅ No breaking changes (or communicated)

### 4. Deployment Checklist

**Before Deployment:**
- ✅ All tests passing
- ✅ Code reviewed and approved
- ✅ Database migrations ready
- ✅ Rollback plan prepared
- ✅ Monitoring configured

**After Deployment:**
- ✅ Health checks passing
- ✅ Smoke tests successful
- ✅ No error spikes
- ✅ Performance metrics normal

### 5. Security Best Practices

- ✅ Never commit secrets
- ✅ Use environment variables
- ✅ Rotate credentials regularly
- ✅ Enable Dependabot
- ✅ Review security alerts
- ✅ Use least privilege access

---

## 🔧 Troubleshooting

### Common Issues

#### 1. CI Tests Failing

```bash
# Check logs
Actions → CI → [failed run] → [failed job]

# Run locally
pytest tests/ -v

# Fix and push
git add .
git commit -m "fix: resolve failing tests"
git push
```

#### 2. Docker Build Failing

```bash
# Check Dockerfile
docker build -f docker/Dockerfile.base -t test .

# Check build logs
Actions → Docker Build → [failed run] → [failed step]

# Common fixes:
- Update base image version
- Fix COPY paths
- Install missing dependencies
```

#### 3. Deployment Failing

```bash
# Check AWS credentials
aws sts get-caller-identity

# Check ECS service
aws ecs describe-services --cluster prod --services churn-pipeline

# Check RDS connectivity
psql "host=$RDS_HOST port=5432 dbname=$RDS_DB_NAME user=$RDS_USERNAME"

# Rollback if needed
aws ecs update-service --cluster prod --service churn-pipeline \
  --task-definition churn-pipeline:PREVIOUS_VERSION --force-new-deployment
```

#### 4. Model Performance Degraded

```bash
# Check monitoring workflow
Actions → ML Model Monitoring → [latest run]

# Check drift report
# Download artifacts → data_drift_*.html

# Trigger retraining
Actions → Model Training Pipeline → Run workflow
```

### Getting Help

- 📖 Documentation: `docs/`
- 💬 GitHub Discussions: [Link to discussions]
- 🐛 Issues: [Link to issues]
- 📧 Team Email: team@yourcompany.com

---

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [AWS ECS Deployment](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/)
- [MLflow Model Registry](https://mlflow.org/docs/latest/model-registry.html)

---

## ✅ Checklist: Initial Setup

- [ ] Fork/clone repository
- [ ] Enable GitHub Actions
- [ ] Configure branch protection
- [ ] Set up environments (staging, production)
- [ ] Add required secrets
- [ ] Configure Dependabot
- [ ] Test CI workflow
- [ ] Test Docker build
- [ ] Deploy to staging
- [ ] Deploy to production
- [ ] Set up monitoring
- [ ] Train first model
- [ ] Document custom changes

---

**Last Updated:** $(date)
**Version:** 1.0.0
**Maintained by:** ML Platform Team

