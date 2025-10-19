# Complete Debugging Guide: ML Pipeline Issues & Solutions

**Last Updated:** October 12, 2025  
**Purpose:** Reference guide for all issues encountered and their solutions

---

## 📚 Table of Contents

1. [Local Development Issues](#local-development-issues)
2. [Docker & Networking Issues](#docker--networking-issues)
3. [AWS RDS Issues](#aws-rds-issues)
4. [ECS Deployment Issues](#ecs-deployment-issues)
5. [Airflow Issues](#airflow-issues)
6. [Image Architecture Issues](#image-architecture-issues)
7. [Make & Shell Script Issues](#make--shell-script-issues)
8. [Security & Authentication Issues](#security--authentication-issues)
9. [Quick Reference Commands](#quick-reference-commands)

---

## Local Development Issues

### Issue #1: Docker Network Conflict

**Error:**
```
WARN[0000] a network with name ml-pipeline-network exists but was not created by compose.
Set `external: true` to use an existing network
network ml-pipeline-network was found but has incorrect label
com.docker.compose.network set to "" (expected: "ml-net")
```

**Root Cause:**
- Network was created manually with `docker network create`
- Docker Compose expected to manage the network itself
- Label mismatch between manual creation and Compose expectations

**Solution:**
```yaml
# docker-compose.yml
networks:
  churn-pipeline-network:
    external: true  # Tell Compose to use existing network
```

**Commands:**
```bash
# Remove old network
docker network rm ml-pipeline-network

# Create new external network
docker network create churn-pipeline-network

# Update docker-compose.yml to use external: true

# Restart services
make docker-down
make docker-up
```

---

### Issue #2: Network Name Inconsistency

**Error:**
```
Different network names used across files:
- ml-pipeline-network (docker-compose.yml)
- churn-pipeline-network (DAGs)
```

**Root Cause:**
- Project renamed from "ml-pipeline" to "churn-pipeline"
- Some files still referenced old name
- DAGs couldn't connect to pipeline containers

**Solution:**
```bash
# Find all occurrences
grep -r "ml-pipeline-network" .

# Replace in these files:
# - docker-compose.yml
# - docker-compose.airflow.yml
# - airflow/dags/*.py
# - Makefile

# For each file:
sed -i '' 's/ml-pipeline-network/churn-pipeline-network/g' filename

# Recreate network
docker network rm ml-pipeline-network
docker network create churn-pipeline-network

# Restart all services
make airflow-down
make docker-down
make docker-up
make airflow-up
```

---

### Issue #3: Python Bytecode Cache Issues

**Error:**
```
Airflow showing old DAG code even after file edits
```

**Root Cause:**
- Python caches bytecode in `__pycache__` folders
- `.pyc` files contain compiled code from previous versions
- Airflow reads cached version instead of source file

**Solution:**
```bash
# Remove all Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

# Also clear Airflow-specific cache
rm -rf airflow/logs/*
rm -rf /tmp/airflow*

# Restart Airflow
make airflow-down
make airflow-up
```

**Makefile automation:**
```makefile
airflow-init:
	# Remove Python cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	
	# Remove Airflow cache
	rm -rf airflow/logs/* 2>/dev/null || true
	rm -rf /tmp/airflow* 2>/dev/null || true
	
	# Initialize
	docker compose -f docker-compose.airflow.yml up airflow-init
```

---

## Docker & Networking Issues

### Issue #4: Containers Can't Communicate

**Error:**
```
airflow-webserver | Could not connect to mlflow-tracking:5001
airflow-webserver | Name or service not known
```

**Root Cause:**
- Containers not on same Docker network
- DNS resolution failing between containers

**Solution:**
```bash
# Verify both services are on same network
docker inspect mlflow-tracking | grep -A 5 Networks
docker inspect airflow-webserver | grep -A 5 Networks

# If on different networks, stop all and recreate
make airflow-down
make docker-down

# Ensure network exists
docker network create churn-pipeline-network

# Update docker-compose files to use same network
networks:
  - churn-pipeline-network

# Start services
make docker-up
make airflow-up

# Test connectivity
docker exec airflow-webserver ping mlflow-tracking
docker exec airflow-webserver curl mlflow-tracking:5001
```

---

### Issue #5: Port Already in Use

**Error:**
```
Error starting userland proxy: listen tcp4 0.0.0.0:8080: bind: address already in use
```

**Root Cause:**
- Another process using port 8080
- Old container still running

**Solution:**
```bash
# Find process using port
lsof -i :8080

# Kill process
kill -9 <PID>

# Or find and stop Docker container
docker ps | grep 8080
docker stop <container-id>

# Check for zombie containers
docker ps -a | grep airflow
docker rm -f <container-id>

# Restart services
make docker-up
```

---

## AWS RDS Issues

### Issue #6: Password Authentication Failed

**Error:**
```
psql: error: connection to server at "xxx.rds.amazonaws.com" (1.2.3.4), port 5432 failed:
FATAL: password authentication failed for user "zuucrew"
```

**Root Cause (Multiple):**

#### Root Cause 6a: Quotes in .env File

**.env file:**
```bash
RDS_PASSWORD="your-password"  # BAD - includes quotes
```

**Solution:**
```bash
# Remove quotes
RDS_PASSWORD=your-password  # GOOD

# Test connection
psql -h $RDS_HOST -U $RDS_USER -d postgres
```

#### Root Cause 6b: Special Characters in Password

**Password:** `churnpipe#bprmls`

**Error:**
```python
ValueError: Port could not be cast to integer value as 'churnpipe'
```

**Root Cause:**
- `#` character in password breaks URL parsing
- PostgreSQL connection string: `postgresql://user:pass#word@host:5432/db`
- Parser sees `#` as URL fragment separator
- Everything after `#` is treated as fragment, not password

**Solution Option 1: URL Encode**
```bash
# In .env
RDS_PASSWORD=churnpipe%23bprmls  # %23 is URL-encoded #
```

**Solution Option 2: Change Password (Recommended)**
```bash
# Use simpler password without special characters
./scripts/reset_rds_password.sh old-password churnpipe2025

# This script:
# 1. Updates RDS master password
# 2. Updates Secrets Manager
# 3. Updates .env file
# 4. Tests connection
```

**Manual password change:**
```bash
# Update RDS
aws rds modify-db-instance \
  --db-instance-identifier churn-pipeline-metadata-db \
  --master-user-password churnpipe2025 \
  --apply-immediately \
  --region ap-south-1

# Wait for it to apply (2-3 minutes)
aws rds describe-db-instances \
  --db-instance-identifier churn-pipeline-metadata-db \
  --query 'DBInstances[0].DBInstanceStatus' \
  --output text

# Update .env
# Change: RDS_PASSWORD=old
# To: RDS_PASSWORD=churnpipe2025

# Test
psql -h $RDS_HOST -U $RDS_USER -d postgres
```

---

### Issue #7: SSL/TLS Connection Required

**Error:**
```
psql: error: connection to server at "xxx.rds.amazonaws.com" failed:
no pg_hba.conf entry for host "1.2.3.4", user "zuucrew", database "postgres", no encryption
```

**Root Cause:**
- RDS configured to require SSL connections
- `psql` command not using SSL mode

**Solution:**
```bash
# Add sslmode to connection string
psql -h $RDS_HOST -U $RDS_USER -d postgres --set=sslmode=require

# For Python/SQLAlchemy
postgresql+psycopg2://user:pass@host:5432/db?sslmode=require

# Update docker-compose.airflow.yml
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: >
  postgresql+psycopg2://airflow:airflow@airflow-postgres:5432/airflow?sslmode=require
```

---

### Issue #8: IP Address Changed - Access Denied

**Error:**
```
psql: error: connection to server at "xxx.rds.amazonaws.com" failed:
Connection timed out
```

**Root Cause:**
- Your public IP changed (ISP assigned new IP)
- RDS security group still allows old IP only

**Solution:**
```bash
# Get current public IP
MY_IP=$(curl -s https://checkip.amazonaws.com)
echo "My IP: $MY_IP"

# Get RDS security group
SG_ID=$(aws rds describe-db-instances \
  --db-instance-identifier churn-pipeline-metadata-db \
  --query 'DBInstances[0].VpcSecurityGroups[0].VpcSecurityGroupId' \
  --output text \
  --region ap-south-1)

echo "Security Group: $SG_ID"

# Remove old rules (if you know old IP)
aws ec2 revoke-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 5432 \
  --cidr OLD_IP/32 \
  --region ap-south-1

# Add new IP
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 5432 \
  --cidr $MY_IP/32 \
  --region ap-south-1

# Test
psql -h $RDS_HOST -U $RDS_USER -d postgres --set=sslmode=require
```

---

### Issue #9: RDS Instance Not Found

**Error:**
```bash
❌ RDS instance 'churn-pipeline-metadata-db' not found!
```

**Root Cause:**
- RDS instance doesn't exist
- Wrong instance identifier
- Wrong AWS region

**Solution:**
```bash
# List all RDS instances
aws rds describe-db-instances \
  --query 'DBInstances[*].[DBInstanceIdentifier,DBInstanceStatus,Endpoint.Address]' \
  --output table \
  --region ap-south-1

# Check different region
aws rds describe-db-instances --region us-east-1

# If instance doesn't exist, create it
aws rds create-db-instance \
  --db-instance-identifier churn-pipeline-metadata-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 13.7 \
  --master-username zuucrew \
  --master-user-password your-password \
  --allocated-storage 20 \
  --publicly-accessible \
  --region ap-south-1

# Wait for creation (5-10 minutes)
aws rds wait db-instance-available \
  --db-instance-identifier churn-pipeline-metadata-db \
  --region ap-south-1
```

---

## ECS Deployment Issues

### Issue #10: AWS CLI Pager Stuck

**Error:**
```
Script hangs showing:
(END)
```

**Root Cause:**
- AWS CLI uses `less` pager by default
- In scripts, pager waits for user input
- Script can't continue

**Solution:**
```bash
# Add to beginning of every script
export AWS_PAGER=""

# Or set globally
echo 'export AWS_PAGER=""' >> ~/.bashrc
source ~/.bashrc

# Or per-command
aws ecs list-tasks --no-cli-pager --cluster churn-pipeline-ecs
```

**Add to all scripts:**
```bash
#!/bin/bash
set -e
export AWS_PAGER=""  # Add this line

source 00_env.sh
# ... rest of script
```

---

### Issue #11: Security Group Name Validation

**Error:**
```
An error occurred (InvalidParameterValue) when calling the CreateSecurityGroup operation:
Value (sg-ecs-churn-pipeline) for parameter GroupName is invalid.
Group names may not be in the format sg-*.
```

**Root Cause:**
- AWS reserves `sg-*` prefix for security group IDs
- Can't use as security group name

**Solution:**
```bash
# Change from:
SG_NAME="sg-ecs-churn-pipeline"  # BAD

# To:
SG_NAME="ecs-tasks-churn-pipeline"  # GOOD

# Update in 20_networking.sh and 99_cleanup_all.sh
```

---

### Issue #12: Missing Dependency Between Scripts

**Error:**
```bash
./40_cluster_alb.sh: line 72: SG_ALB_ID: unbound variable
```

**Root Cause:**
- User skipped running `20_networking.sh`
- `SG_ALB_ID` variable is generated by `20_networking.sh` and saved to `.env.out`
- `40_cluster_alb.sh` sources `.env.out` expecting that variable

**Solution:**
```bash
# Always run scripts in order!
# Correct order:
./rebuild_for_amd64.sh
./10_bootstrap.sh
./20_networking.sh    # ← Must run this first
./30_iam.sh
./40_cluster_alb.sh   # ← This needs output from 20_networking.sh
./50_register_tasks.sh
./60_services.sh
./70_airflow_init.sh
./80_airflow_vars.sh

# If you get "unbound variable" errors, check .env.out
cat ecs-deploy/.env.out

# Missing variables? Run the earlier scripts
cd ecs-deploy
./20_networking.sh
./30_iam.sh
# ... then continue from where you left off
```

---

### Issue #13: ECS Cluster Inactive

**Error:**
```
An error occurred (ClusterNotFoundException) when calling the CreateService operation:
The referenced cluster was inactive.
```

**Root Cause:**
- ECS cluster was deleted or failed to create
- Cluster in `INACTIVE` state

**Solution:**
```bash
# Check cluster status
aws ecs describe-clusters \
  --clusters churn-pipeline-ecs \
  --region ap-south-1

# If INACTIVE, delete and recreate
aws ecs delete-cluster \
  --cluster churn-pipeline-ecs \
  --region ap-south-1

# Wait 1 minute
sleep 60

# Recreate
aws ecs create-cluster \
  --cluster-name churn-pipeline-ecs \
  --region ap-south-1

# Continue with deployment
cd ecs-deploy
./50_register_tasks.sh
./60_services.sh
```

---

### Issue #14: Missing ALB Listener Rule

**Error:**
```
An error occurred (InvalidParameterException) when calling the CreateService operation:
The target group with targetGroupArn arn:aws:elasticloadbalancing:...:targetgroup/churn-pipeline-mlflow-tg/...
does not have an associated load balancer.
```

**Root Cause:**
- Target group created but not linked to ALB
- Missing listener rule for MLflow port 5001

**Solution:**
```bash
# Get ALB ARN
ALB_ARN=$(aws elbv2 describe-load-balancers \
  --names churn-pipeline-alb \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text \
  --region ap-south-1)

# Get MLflow target group ARN
TG_ARN=$(aws elbv2 describe-target-groups \
  --names churn-pipeline-mlflow-tg \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text \
  --region ap-south-1)

# Create listener for port 5001
aws elbv2 create-listener \
  --load-balancer-arn "$ALB_ARN" \
  --protocol HTTP \
  --port 5001 \
  --default-actions Type=forward,TargetGroupArn="$TG_ARN" \
  --region ap-south-1

# Verify
aws elbv2 describe-listeners \
  --load-balancer-arn "$ALB_ARN" \
  --region ap-south-1
```

---

### Issue #15: Private Subnets Return Null

**Error:**
```bash
PRIVATE_SUBNETS=$(aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$VPC_ID" "Name=map-public-ip-on-launch,Values=false" \
  --query 'Subnets[*].SubnetId' \
  --output json)

echo $PRIVATE_SUBNETS
# Output: null
```

**Root Cause:**
- VPC has no private subnets
- All subnets have `MapPublicIpOnLaunch=True`

**Solution:**
```bash
# Check all subnets
aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'Subnets[*].[SubnetId,MapPublicIpOnLaunch,AvailabilityZone]' \
  --output table \
  --region ap-south-1

# If all are public (MapPublicIpOnLaunch=True):
# Option 1: Use public subnets for both
PUBLIC_SUBNETS='["subnet-xxx","subnet-yyy","subnet-zzz"]'
PRIVATE_SUBNETS='["subnet-xxx","subnet-yyy","subnet-zzz"]'  # Same as public

# Update ECS task network config to assign public IP
aws ecs create-service \
  --network-configuration "awsvpcConfiguration={
      subnets=[subnet-xxx,subnet-yyy,subnet-zzz],
      securityGroups=[sg-xxx],
      assignPublicIp=ENABLED  # ← Must be ENABLED for public subnets
  }"

# Update all scripts:
# - 60_services.sh
# - 70_airflow_init.sh
# - 80_airflow_vars.sh
```

---

## Airflow Issues

### Issue #16: DAG History Persists After Init

**Error:**
```
User runs: make airflow-init
But old DAG runs still visible in UI
```

**Root Cause:**
- `airflow-init` was only running DB migration
- Wasn't dropping existing database or volumes
- Old DAG runs persisted across init

**Solution:**
```makefile
# Makefile - Enhanced airflow-init
airflow-init:
	@echo "🧹 Cleaning Airflow environment..."
	
	# Stop services
	docker compose -f docker-compose.airflow.yml down -v
	
	# Remove logs
	rm -rf airflow/logs/* 2>/dev/null || true
	
	# Remove Python cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	
	# Remove DAG/plugin cache
	rm -rf /tmp/airflow* 2>/dev/null || true
	
	# Remove volumes (drops local PostgreSQL)
	docker volume rm week_11_airflow-postgres-data 2>/dev/null || true
	
	# Start fresh
	docker compose -f docker-compose.airflow.yml up airflow-init
```

---

### Issue #17: Airflow Scheduler Running DAGs Too Often

**Error:**
```
DAG scheduled for every 20 minutes
But runs every 5 minutes or constantly
```

**Root Cause (Multiple):**

#### Root Cause 17a: Old start_date with catchup

```python
dag = DAG(
    start_date=datetime(2025, 10, 8),  # 4 days ago
    catchup=False,  # This doesn't fully prevent backfill
)
```

**What happens:**
- Scheduler starts, sees start_date is 4 days ago
- Tries to "catch up" missed runs
- Creates multiple DAG runs

**Solution:**
```python
# Always use recent start_date
dag = DAG(
    start_date=datetime(2025, 10, 12),  # Today
    catchup=False,
)
```

#### Root Cause 17b: Accumulated Old DAG Runs

```bash
# Check DAG runs
docker exec airflow-webserver \
  airflow dags list-runs -d data_pipeline_every_20m

# Output shows 596 old runs!
```

**Solution:**
```bash
# Delete all old runs
docker exec airflow-webserver \
  airflow dags delete -y data_pipeline_every_20m

docker exec airflow-webserver \
  airflow dags delete -y inference_pipeline_every_10m

docker exec airflow-webserver \
  airflow dags delete -y train_pipeline_every_60m

# Restart scheduler
docker restart airflow-scheduler
```

#### Root Cause 17c: max_active_runs > 1

```python
dag = DAG(
    max_active_runs=2,  # Allows 2 concurrent runs
)
```

**What happens:**
- Scheduler can start new run before previous finishes
- Appears to run "too often"

**Solution:**
```python
dag = DAG(
    max_active_runs=1,  # Only 1 run at a time
)
```

---

### Issue #18: DAG Timeout Errors

**Error:**
```
DagRunTimeout: DAG run timed out
Task failed with timeout
```

**Root Cause:**
- `dagrun_timeout` too short
- `execution_timeout` too short
- Tasks take longer than expected

**Solution:**
```python
# Before (too aggressive)
dag = DAG(
    dagrun_timeout=timedelta(minutes=9),
    default_args={
        'execution_timeout': timedelta(minutes=9),
    }
)

# After (more reasonable)
dag = DAG(
    dagrun_timeout=timedelta(minutes=30),  # Increased
    default_args={
        'execution_timeout': timedelta(minutes=30),
        'retries': 2,  # Allow retries
        'retry_delay': timedelta(minutes=2),
    }
)
```

---

### Issue #19: 502 Bad Gateway - Airflow UI

**Error:**
```
Browser: http://alb-dns.amazonaws.com
Response: 502 Bad Gateway
```

**Root Cause:**
- Airflow webserver crashed
- Worker crashed trying to load incompatible DAGs
- Old DAG metadata in database doesn't match new DAG files

**Diagnosis:**
```bash
# Check service health
aws ecs describe-services \
  --cluster churn-pipeline-ecs \
  --services airflow-webserver-svc \
  --query 'services[0].deployments[0].rolloutState' \
  --region ap-south-1

# Check target group health
aws elbv2 describe-target-health \
  --target-group-arn $TG_AIRFLOW_ARN \
  --region ap-south-1

# Check CloudWatch logs
aws logs tail /ecs/churn-pipeline \
  --follow \
  --filter-pattern "airflow-web" \
  --region ap-south-1
```

**Solution:**
```bash
# Stop all Airflow services
aws ecs update-service \
  --cluster churn-pipeline-ecs \
  --service airflow-webserver-svc \
  --desired-count 0 \
  --region ap-south-1

aws ecs update-service \
  --cluster churn-pipeline-ecs \
  --service airflow-scheduler-svc \
  --desired-count 0 \
  --region ap-south-1

aws ecs update-service \
  --cluster churn-pipeline-ecs \
  --service airflow-worker-svc \
  --desired-count 0 \
  --region ap-south-1

# Drop and recreate Airflow database
psql -h $RDS_HOST -U $RDS_USER -d postgres --set=sslmode=require

DROP DATABASE airflow;
CREATE DATABASE airflow;
\q

# Reinitialize Airflow
cd ecs-deploy
./70_airflow_init.sh
./80_airflow_vars.sh

# Restart services
aws ecs update-service \
  --cluster churn-pipeline-ecs \
  --service airflow-webserver-svc \
  --desired-count 1 \
  --region ap-south-1

aws ecs update-service \
  --cluster churn-pipeline-ecs \
  --service airflow-scheduler-svc \
  --desired-count 1 \
  --region ap-south-1

aws ecs update-service \
  --cluster churn-pipeline-ecs \
  --service airflow-worker-svc \
  --desired-count 1 \
  --region ap-south-1
```

---

### Issue #20: "DAG seems to be missing from DagBag"

**Error:**
```
DAG "data_pipeline_every_20m" seems to be missing from DagBag.
This means you can remove information about it from metadata
```

**Root Cause:**
- Database contains references to old DAG IDs
- DAG files renamed or deleted
- DAG file has syntax errors

**Solution:**
```bash
# Check if DAG file exists and is valid
python ecs-deploy/airflow/dags/data_pipeline_ecs_dag.py

# If old DAG ID in database, remove it
psql -h $RDS_HOST -U $RDS_USER -d airflow --set=sslmode=require

# Delete from task_instance table
DELETE FROM task_instance WHERE dag_id = 'data_pipeline_every_20m';

# Delete from task_fail table
DELETE FROM task_fail WHERE dag_id = 'data_pipeline_every_20m';

# Delete from dag_run table
DELETE FROM dag_run WHERE dag_id = 'data_pipeline_every_20m';

# Delete from dag table
DELETE FROM dag WHERE dag_id = 'data_pipeline_every_20m';

\q

# Restart scheduler
aws ecs update-service \
  --cluster churn-pipeline-ecs \
  --service airflow-scheduler-svc \
  --force-new-deployment \
  --region ap-south-1
```

---

### Issue #21: Redis Connection Timeout

**Error:**
```
[2025-10-12] ERROR - Cannot connect to redis://xxx.cache.amazonaws.com:6379/0
redis.exceptions.TimeoutError: Timeout connecting to server
```

**Root Cause:**
- Security group blocking port 6379
- ECS tasks can't reach Redis ElastiCache

**Solution:**
```bash
# Get ECS security group
SG_ECS_ID=sg-xxx

# Get Redis security group (usually default VPC SG)
SG_DEFAULT=$(aws ec2 describe-security-groups \
  --filters "Name=vpc-id,Values=$VPC_ID" "Name=group-name,Values=default" \
  --query 'SecurityGroups[0].GroupId' \
  --output text \
  --region ap-south-1)

# Allow ECS tasks to talk to each other on Redis port
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ECS_ID \
  --protocol tcp \
  --port 6379 \
  --source-group $SG_ECS_ID \
  --region ap-south-1

# Allow ECS tasks to reach Redis
aws ec2 authorize-security-group-ingress \
  --group-id $SG_DEFAULT \
  --protocol tcp \
  --port 6379 \
  --source-group $SG_ECS_ID \
  --region ap-south-1

# Force service redeploy
aws ecs update-service \
  --cluster churn-pipeline-ecs \
  --service airflow-scheduler-svc \
  --force-new-deployment \
  --region ap-south-1

aws ecs update-service \
  --cluster churn-pipeline-ecs \
  --service airflow-worker-svc \
  --force-new-deployment \
  --region ap-south-1
```

---

### Issue #22: Only One DAG Visible in ECS Airflow

**Error:**
```
ECS Airflow UI shows only train_pipeline_ecs_hourly
Missing: data_pipeline_ecs_every_20m, inference_pipeline_ecs_every_10m
```

**Root Cause:**
- Database contains old DAG metadata
- Old DAGs conflict with new DAGs
- Scheduler can't process DAG files

**Solution:**
```bash
# Connect to RDS
psql -h $RDS_HOST -U $RDS_USER -d airflow --set=sslmode=require

# Check DAG table
SELECT dag_id, fileloc FROM dag;

# If you see old local DAG IDs, delete them
DELETE FROM task_instance 
WHERE dag_id IN ('data_pipeline_every_20m', 'inference_pipeline_every_10m', 'train_pipeline_every_60m');

DELETE FROM task_fail 
WHERE dag_id IN ('data_pipeline_every_20m', 'inference_pipeline_every_10m', 'train_pipeline_every_60m');

DELETE FROM dag_run 
WHERE dag_id IN ('data_pipeline_every_20m', 'inference_pipeline_every_10m', 'train_pipeline_every_60m');

DELETE FROM dag 
WHERE dag_id IN ('data_pipeline_every_20m', 'inference_pipeline_every_10m', 'train_pipeline_every_60m');

\q

# Restart all Airflow services
aws ecs update-service --cluster churn-pipeline-ecs \
  --service airflow-webserver-svc --force-new-deployment --region ap-south-1

aws ecs update-service --cluster churn-pipeline-ecs \
  --service airflow-scheduler-svc --force-new-deployment --region ap-south-1

aws ecs update-service --cluster churn-pipeline-ecs \
  --service airflow-worker-svc --force-new-deployment --region ap-south-1

# Wait 2 minutes, then refresh UI
```

---

### Issue #29: EcsOperator Import Error - "cannot import name 'EcsOperator'"

**Error:**
```
Broken DAG: [/opt/airflow/dags/train_pipeline_ecs_dag.py] 
Traceback (most recent call last):
  File "/opt/airflow/dags/train_pipeline_ecs_dag.py", line 8, in <module>
    from airflow.providers.amazon.aws.operators.ecs import EcsOperator
ImportError: cannot import name 'EcsOperator' from 'airflow.providers.amazon.aws.operators.ecs'

Broken DAG: [/opt/airflow/dags/inference_pipeline_ecs_dag.py]
ImportError: cannot import name 'EcsOperator' from 'airflow.providers.amazon.aws.operators.ecs'

Broken DAG: [/opt/airflow/dags/data_pipeline_ecs_dag.py]
ImportError: cannot import name 'EcsOperator' from 'airflow.providers.amazon.aws.operators.ecs'
```

**Root Cause:**
- `EcsOperator` is the **old name** (deprecated)
- In newer versions of `apache-airflow-providers-amazon`, it was renamed to `EcsRunTaskOperator`
- Airflow 2.8.1 with amazon provider 8.16.0 uses the new name
- Also, the parameter `region_name` was changed to `region`

This is a **breaking change** between provider versions.

**Solution:**

Update all three ECS DAG files:

**File 1: `ecs-deploy/airflow/dags/data_pipeline_ecs_dag.py`**
```python
# Change line 8 from:
from airflow.providers.amazon.aws.operators.ecs import EcsOperator

# To:
from airflow.providers.amazon.aws.operators.ecs import EcsRunTaskOperator

# Change line 37 from:
run_data_pipeline = EcsOperator(
    task_id="run_data_pipeline_ecs",
    cluster=ECS_CLUSTER,
    task_definition=TASK_DEF_DATA,
    launch_type="FARGATE",
    region_name=AWS_REGION,  # ← Old parameter

# To:
run_data_pipeline = EcsRunTaskOperator(
    task_id="run_data_pipeline_ecs",
    cluster=ECS_CLUSTER,
    task_definition=TASK_DEF_DATA,
    launch_type="FARGATE",
    region=AWS_REGION,  # ← New parameter
```

**File 2: `ecs-deploy/airflow/dags/inference_pipeline_ecs_dag.py`**
```python
# Same changes:
# 1. Import: EcsOperator → EcsRunTaskOperator
# 2. Parameter: region_name → region
```

**File 3: `ecs-deploy/airflow/dags/train_pipeline_ecs_dag.py`**
```python
# Same changes:
# 1. Import: EcsOperator → EcsRunTaskOperator
# 2. Parameter: region_name → region
```

**After fixing the files, rebuild and redeploy:**

```bash
# 1. Rebuild Airflow image with fixed DAGs
cd ecs-deploy
./rebuild_for_amd64.sh

# 2. Push to ECR
./10_bootstrap.sh

# 3. Force services to redeploy with new image
./update_services.sh

# 4. Wait for services to restart (5-10 minutes)
sleep 300

# 5. Check Airflow UI - DAGs should now appear with no errors
```

**Quick one-liner:**
```bash
cd ecs-deploy && ./rebuild_for_amd64.sh && ./10_bootstrap.sh && ./update_services.sh
```

**Verification:**

After ~30 minutes, check Airflow UI. You should see:
- ✅ `data_pipeline_ecs_every_20m` (green, no errors)
- ✅ `inference_pipeline_ecs_every_10m` (green, no errors)
- ✅ `train_pipeline_ecs_hourly` (green, no errors)

**Prevention:**

When using Airflow providers, always check the documentation for your specific version:
```bash
# Check installed provider version
pip show apache-airflow-providers-amazon

# Check documentation for that version
# https://airflow.apache.org/docs/apache-airflow-providers-amazon/8.16.0/operators/ecs.html
```

**Migration Guide:**

If you see `EcsOperator` in older code or tutorials:
- Airflow providers < 8.0: Use `EcsOperator`
- Airflow providers >= 8.0: Use `EcsRunTaskOperator`

Other renamed parameters in EcsRunTaskOperator:
- `region_name` → `region`
- Some parameters were removed (check docs for your version)

---

## Image Architecture Issues

### Issue #23: Platform Mismatch - ARM64 vs AMD64

**Error:**
```
Waiter ServicesStable failed: Max attempts exceeded
CannotPullContainerError: pull image manifest has been retried 7 time(s):
failed to resolve reference: unexpected status from HEAD request:
404 Not Found: image Manifest does not contain descriptor matching platform 'linux/amd64'.
```

**Root Cause:**
- Mac with Apple Silicon (M1/M2/M3) builds ARM64 images
- AWS Fargate only supports AMD64/x86_64
- Docker pushed ARM64 images to ECR
- ECS tasks can't run ARM64 images

**Diagnosis:**
```bash
# Check image platform
docker inspect churn-pipeline/airflow:2.8.1-amazon \
  --format='{{.Os}}/{{.Architecture}}'

# Output: linux/arm64  ← Problem!
# Need: linux/amd64
```

**Solution:**
```bash
# Rebuild all images for AMD64
cd ecs-deploy
./rebuild_for_amd64.sh

# This script:
# 1. Uses Docker Buildx for cross-platform builds
# 2. Rebuilds 5 images for linux/amd64
# 3. Verifies platform
# 4. Cleans up dangling images

# Verify new platform
docker inspect churn-pipeline/airflow:2.8.1-amazon \
  --format='{{.Os}}/{{.Architecture}}'
# Output: linux/amd64  ← Correct!

# Push to ECR
./10_bootstrap.sh

# Force services to pull new images
./update_services.sh
```

**Prevention:**
```bash
# Always rebuild for AMD64 before ECS deployment
# On Apple Silicon Mac:
./ecs-deploy/rebuild_for_amd64.sh  # Always run this first

# On Intel Mac / Linux / Windows:
# Not needed - already builds AMD64 by default
```

---

### Issue #24: Dangling Docker Images

**Error:**
```bash
docker images

REPOSITORY          TAG       IMAGE ID       SIZE
churn-pipeline/...  latest    abc123        1.2GB
<none>              <none>    def456        1.2GB  ← Dangling
<none>              <none>    ghi789        1.1GB  ← Dangling
```

**Root Cause:**
- Old image layers left behind after rebuilds
- Docker keeps them as cache
- Takes up disk space

**Solution:**
```bash
# Remove dangling images
docker image prune -f

# Remove all unused images
docker image prune -a -f

# Automated in rebuild script
# ecs-deploy/rebuild_for_amd64.sh already includes:
docker image prune -f

# Check disk space
docker system df
```

---

## Make & Shell Script Issues

### Issue #25: Make Can't Handle AWS Credentials

**Error:**
```bash
make deploy-ecs
# Error: The config profile (default) could not be found
```

**Root Cause:**
- Make runs each `@` line in separate subshell
- Environment variables don't persist between lines
- `export AWS_PROFILE=default` in one line
- Next line doesn't see that variable

**Attempted Fixes (All Failed):**
```makefile
# Attempt 1
deploy-ecs:
	export AWS_PROFILE=default
	aws sts get-caller-identity  # Can't see AWS_PROFILE

# Attempt 2
export AWS_PROFILE := default
deploy-ecs:
	aws sts get-caller-identity  # Still fails

# Attempt 3  
deploy-ecs:
	AWS_PROFILE=default aws sts get-caller-identity  # Works once
	cd ecs-deploy && ./10_bootstrap.sh  # Can't see AWS_PROFILE
```

**Solution:**
```bash
# Don't use Make for ECS deployment
# Use shell script instead: run_ecs.sh

#!/bin/bash
set -e

# Single shell process - variables persist
export AWS_PROFILE=${AWS_PROFILE:-default}

# Now all commands see AWS_PROFILE
aws sts get-caller-identity
cd ecs-deploy
./10_bootstrap.sh
./20_networking.sh
# ... etc
```

**Update Makefile:**
```makefile
deploy-ecs:
	@echo "⚠️  Please use the shell script instead:"
	@echo ""
	@echo "    ./run_ecs.sh"
	@echo ""
	@echo "  Make has issues with environment variable inheritance."
	@exit 1
```

---

### Issue #26: Make Heredoc Syntax Error

**Error:**
```bash
make airflow-init
bash: CREATE: command not found
bash: EOSQL: command not found
```

**Root Cause:**
- Incorrect heredoc syntax in Makefile
- Backslash at end of lines broke heredoc

**Before (broken):**
```makefile
airflow-init:
	psql ... <<-EOSQL \
		DROP DATABASE IF EXISTS airflow; \
		CREATE DATABASE airflow; \
	EOSQL
```

**After (fixed):**
```makefile
airflow-init:
	psql ... -c "DROP DATABASE IF EXISTS airflow"
	psql ... -c "CREATE DATABASE airflow"
```

---

## Security & Authentication Issues

### Issue #27: 504 Gateway Timeout - Airflow UI

**Error:**
```
Browser: http://alb-dns.amazonaws.com
Response: 504 Gateway Time-out
```

**Root Cause:**
- ALB can't reach Airflow webserver
- Security group blocking traffic
- Webserver not running or unhealthy

**Diagnosis:**
```bash
# Check target health
TG_ARN=$(aws elbv2 describe-target-groups \
  --names churn-pipeline-airflow-tg \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text)

aws elbv2 describe-target-health \
  --target-group-arn $TG_ARN

# Output:
# State: unhealthy
# Reason: Target.FailedHealthChecks

# Check security group
aws ec2 describe-security-groups \
  --group-ids sg-xxx \
  --query 'SecurityGroups[0].IpPermissions'

# Look for rule allowing ALB → ECS on port 8080
```

**Solution:**
```bash
# Get security group IDs
SG_ECS_ID=sg-xxx  # ECS tasks
SG_ALB_ID=sg-yyy  # ALB

# Add ingress rule: ALB → ECS on port 8080
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ECS_ID \
  --protocol tcp \
  --port 8080 \
  --source-group $SG_ALB_ID \
  --region ap-south-1

# Add ingress rule: ALB → ECS on port 5001 (MLflow)
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ECS_ID \
  --protocol tcp \
  --port 5001 \
  --source-group $SG_ALB_ID \
  --region ap-south-1

# Verify rules
aws ec2 describe-security-groups \
  --group-ids $SG_ECS_ID \
  --query 'SecurityGroups[0].IpPermissions'

# Should see rules allowing traffic from $SG_ALB_ID on ports 8080 and 5001
```

---

### Issue #28: MLflow UI Not Working (Port 5001)

**Error:**
```
http://alb-dns.amazonaws.com:5001/ not working
Connection timeout or refused
```

**Root Cause (Multiple):**

#### Root Cause 28a: Missing ALB Listener

**Diagnosis:**
```bash
# Check ALB listeners
aws elbv2 describe-listeners \
  --load-balancer-arn $ALB_ARN \
  --region ap-south-1

# Only see port 80 listener, no 5001
```

**Solution:**
```bash
# Create listener for port 5001
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTP \
  --port 5001 \
  --default-actions Type=forward,TargetGroupArn=$TG_MLFLOW_ARN \
  --region ap-south-1
```

#### Root Cause 28b: ALB Security Group Blocking Port 5001

**Solution:**
```bash
# Allow inbound on port 5001
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ALB_ID \
  --protocol tcp \
  --port 5001 \
  --cidr 0.0.0.0/0 \
  --region ap-south-1
```

#### Root Cause 28c: MLflow Service Not Running

**Diagnosis:**
```bash
# Check service status
aws ecs describe-services \
  --cluster churn-pipeline-ecs \
  --services mlflow-tracking-svc \
  --region ap-south-1
```

**Solution:**
```bash
# Start service if stopped
aws ecs update-service \
  --cluster churn-pipeline-ecs \
  --service mlflow-tracking-svc \
  --desired-count 1 \
  --region ap-south-1
```

---

## Quick Reference Commands

### Diagnosis Commands

```bash
# Check all running containers
docker ps

# Check Docker networks
docker network ls
docker network inspect churn-pipeline-network

# Check Docker images
docker images

# Check system resource usage
docker stats

# Check disk space
docker system df

# View logs
docker logs <container-name> -f

# Exec into container
docker exec -it <container-name> bash

# Test network connectivity
docker exec <container-name> ping <other-container-name>
docker exec <container-name> curl <other-container-name>:port

# Check Airflow DAGs
docker exec airflow-webserver airflow dags list

# Check Airflow DB connection
docker exec airflow-webserver airflow db check

# Check AWS credentials
aws sts get-caller-identity

# Check RDS connection
psql -h $RDS_HOST -U $RDS_USER -d postgres --set=sslmode=require

# Check ECS services
aws ecs describe-services \
  --cluster churn-pipeline-ecs \
  --services airflow-webserver-svc \
  --region ap-south-1

# Check ECS tasks
aws ecs list-tasks \
  --cluster churn-pipeline-ecs \
  --region ap-south-1

# Check CloudWatch logs
aws logs tail /ecs/churn-pipeline --follow --region ap-south-1

# Check security groups
aws ec2 describe-security-groups \
  --group-ids sg-xxx \
  --region ap-south-1

# Check target group health
aws elbv2 describe-target-health \
  --target-group-arn $TG_ARN \
  --region ap-south-1

# Check image platform
docker inspect <image-name> --format='{{.Os}}/{{.Architecture}}'
```

### Cleanup Commands

```bash
# Local cleanup
make clean-all  # Everything (local + ECS)
make docker-clean-all  # Local Docker only
make airflow-down && make docker-down  # Stop services

# Remove Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

# Remove dangling images
docker image prune -f

# Remove all unused resources
docker system prune -a -f

# ECS cleanup
make docker-clean-all-ecs  # Via Make
cd ecs-deploy && ./99_cleanup_all.sh  # Direct script
```

### Recovery Commands

```bash
# Restart local services
make airflow-down
make docker-down
make deploy-local

# Restart ECS services
aws ecs update-service \
  --cluster churn-pipeline-ecs \
  --service <service-name> \
  --force-new-deployment \
  --region ap-south-1

# Reset Airflow local database
make airflow-init

# Reset Airflow ECS database
psql -h $RDS_HOST -U $RDS_USER -d postgres --set=sslmode=require
DROP DATABASE airflow;
CREATE DATABASE airflow;
\q
cd ecs-deploy && ./70_airflow_init.sh

# Rebuild images for ECS
cd ecs-deploy
./rebuild_for_amd64.sh
./10_bootstrap.sh
./update_services.sh
```

---

## Troubleshooting Workflow

When something breaks, follow this systematic approach:

1. **Identify the Error**
   - Read the error message carefully
   - Note the exact command that failed
   - Check timestamps to see when it started

2. **Check Logs**
   ```bash
   # Local
   docker logs <container-name>
   
   # ECS
   aws logs tail /ecs/churn-pipeline --follow
   ```

3. **Verify Connectivity**
   ```bash
   # Ping
   docker exec <container> ping <other-container>
   
   # HTTP
   docker exec <container> curl <other-container>:port
   ```

4. **Check Configuration**
   ```bash
   # Environment variables
   docker exec <container> env | grep -i <var-name>
   
   # Files
   docker exec <container> cat /path/to/config
   ```

5. **Verify Resources**
   ```bash
   # Docker
   docker stats
   docker system df
   
   # AWS
   aws ecs describe-services --cluster ... --services ...
   aws elbv2 describe-target-health --target-group-arn ...
   ```

6. **Search This Document**
   - Use Ctrl+F to search for error message
   - Look in relevant section (Docker, RDS, ECS, Airflow)

7. **Try Clean State**
   ```bash
   # Local: Full reset
   make clean-all
   ./run_local.sh
   
   # ECS: Redeploy
   cd ecs-deploy && ./99_cleanup_all.sh
   ./run_ecs.sh
   ```

---

## Summary

This guide covered:
- ✅ 29 distinct issues and their solutions
- ✅ Database connection and authentication problems
- ✅ Docker networking and architecture issues
- ✅ AWS ECS deployment challenges
- ✅ Airflow DAG and scheduling problems
- ✅ Security group and connectivity issues
- ✅ Platform architecture mismatches
- ✅ Make and shell scripting limitations

**Key Lessons:**
1. Always check logs first
2. Verify security groups for ECS issues
3. Use shell scripts for AWS deployments (not Make)
4. Rebuild images for AMD64 on Apple Silicon
5. Keep DAG start_dates recent
6. Clear caches when things behave strangely
7. Run deployment scripts in order
8. Test locally before deploying to ECS

---

**Still stuck? Check the teaching guide for architectural understanding!**

