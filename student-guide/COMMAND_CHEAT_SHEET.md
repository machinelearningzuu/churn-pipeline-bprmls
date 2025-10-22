# Command Cheat Sheet

**Quick Reference for Docker, AWS CLI, and Common Commands**

This is your go-to reference when you need to quickly look up a command. Bookmark this page!

---

## Table of Contents

1. [Docker Commands](#docker-commands)
2. [Docker Compose Commands](#docker-compose-commands)
3. [AWS CLI Commands](#aws-cli-commands)
4. [Kafka Commands](#kafka-commands)
5. [PostgreSQL Commands](#postgresql-commands)
6. [Git Commands](#git-commands)
7. [Python Commands](#python-commands)
8. [Troubleshooting Commands](#troubleshooting-commands)

---

## Docker Commands

### Basic Docker Operations

```bash
# Check if Docker is running
docker --version
docker info

# List all running containers
docker ps

# List all containers (including stopped ones)
docker ps -a

# Start a container
docker start <container-name>

# Stop a container
docker stop <container-name>

# Restart a container
docker restart <container-name>

# Remove a stopped container
docker rm <container-name>

# Force remove a running container
docker rm -f <container-name>
```

### Docker Images

```bash
# List all local images
docker images

# Pull an image from Docker Hub
docker pull <image-name>:<tag>

# Build an image from a Dockerfile
docker build -t <image-name>:<tag> .

# Build without using cache
docker build --no-cache -t <image-name>:<tag> .

# Remove an image
docker rmi <image-name>:<tag>

# Remove all unused images
docker image prune -a
```

### Docker Logs & Debugging

```bash
# View container logs
docker logs <container-name>

# Follow logs in real-time (like tail -f)
docker logs -f <container-name>

# View last 100 lines
docker logs --tail 100 <container-name>

# View logs from last 10 minutes
docker logs --since 10m <container-name>

# Execute a command inside a running container
docker exec -it <container-name> bash

# Check container resource usage (CPU, memory)
docker stats

# Inspect container details
docker inspect <container-name>
```

### Docker Networks

```bash
# List all networks
docker network ls

# Create a network
docker network create <network-name>

# Remove a network
docker network rm <network-name>

# Connect container to a network
docker network connect <network-name> <container-name>

# Inspect network details
docker network inspect <network-name>
```

### Docker Volumes

```bash
# List all volumes
docker volume ls

# Create a volume
docker volume create <volume-name>

# Remove a volume
docker volume rm <volume-name>

# Remove all unused volumes
docker volume prune

# Inspect volume
docker volume inspect <volume-name>
```

### Docker Cleanup

```bash
# Remove all stopped containers
docker container prune

# Remove all unused images
docker image prune -a

# Remove all unused volumes
docker volume prune

# Remove all unused networks
docker network prune

# Clean everything (USE WITH CAUTION!)
docker system prune -a --volumes
```

---

## Docker Compose Commands

### Basic Operations

```bash
# Start all services (detached mode)
docker-compose up -d

# Start specific service
docker-compose up -d <service-name>

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart <service-name>
```

### Building & Rebuilding

```bash
# Build all services
docker-compose build

# Build specific service
docker-compose build <service-name>

# Build without cache
docker-compose build --no-cache

# Rebuild and start services
docker-compose up -d --build

# Force recreate containers
docker-compose up -d --force-recreate
```

### Logs & Monitoring

```bash
# View logs from all services
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View logs from specific service
docker-compose logs -f <service-name>

# View last 50 lines
docker-compose logs --tail 50

# Check service status
docker-compose ps

# Check which services are running
docker-compose top
```

### Multiple Compose Files

```bash
# Use specific compose file
docker-compose -f docker-compose.kafka.yml up -d

# Use multiple compose files
docker-compose -f docker-compose.yml -f docker-compose.kafka.yml up -d

# Stop services from specific file
docker-compose -f docker-compose.kafka.yml down
```

---

## AWS CLI Commands

### Setup & Configuration

```bash
# Check AWS CLI version
aws --version

# Configure AWS credentials
aws configure

# List configured profiles
aws configure list-profiles

# Use specific profile
aws --profile <profile-name> <command>

# Set default region
aws configure set region ap-south-1
```

### S3 Commands

```bash
# List all buckets
aws s3 ls

# List bucket contents
aws s3 ls s3://<bucket-name>/

# Upload file to S3
aws s3 cp <local-file> s3://<bucket-name>/<path>/

# Upload directory to S3
aws s3 cp <local-dir> s3://<bucket-name>/<path>/ --recursive

# Download file from S3
aws s3 cp s3://<bucket-name>/<file> <local-path>

# Download directory from S3
aws s3 cp s3://<bucket-name>/<path>/ <local-dir> --recursive

# Sync local directory to S3 (only changed files)
aws s3 sync <local-dir> s3://<bucket-name>/<path>/

# Delete file from S3
aws s3 rm s3://<bucket-name>/<file>

# Delete directory from S3
aws s3 rm s3://<bucket-name>/<path>/ --recursive

# Create bucket
aws s3 mb s3://<bucket-name>

# Remove bucket
aws s3 rb s3://<bucket-name> --force
```

### RDS Commands

```bash
# List all RDS instances
aws rds describe-db-instances

# Get specific RDS instance details
aws rds describe-db-instances --db-instance-identifier <instance-name>

# Get RDS endpoint
aws rds describe-db-instances --db-instance-identifier <instance-name> \
  --query 'DBInstances[0].Endpoint.Address' --output text

# Start RDS instance
aws rds start-db-instance --db-instance-identifier <instance-name>

# Stop RDS instance
aws rds stop-db-instance --db-instance-identifier <instance-name>

# Create RDS snapshot
aws rds create-db-snapshot \
  --db-instance-identifier <instance-name> \
  --db-snapshot-identifier <snapshot-name>

# List RDS snapshots
aws rds describe-db-snapshots

# Delete RDS instance (with final snapshot)
aws rds delete-db-instance \
  --db-instance-identifier <instance-name> \
  --final-db-snapshot-identifier <snapshot-name>
```

### EC2 Commands

```bash
# List all EC2 instances
aws ec2 describe-instances

# List running instances
aws ec2 describe-instances --filters "Name=instance-state-name,Values=running"

# Get instance details
aws ec2 describe-instances --instance-ids <instance-id>

# Start instance
aws ec2 start-instances --instance-ids <instance-id>

# Stop instance
aws ec2 stop-instances --instance-ids <instance-id>

# Reboot instance
aws ec2 reboot-instances --instance-ids <instance-id>

# Terminate instance
aws ec2 terminate-instances --instance-ids <instance-id>

# Create key pair
aws ec2 create-key-pair --key-name <key-name> --query 'KeyMaterial' --output text > <key-name>.pem

# List security groups
aws ec2 describe-security-groups

# Create security group
aws ec2 create-security-group \
  --group-name <group-name> \
  --description "<description>"
```

### ECS Commands

```bash
# List ECS clusters
aws ecs list-clusters

# Describe cluster
aws ecs describe-clusters --clusters <cluster-name>

# List services in cluster
aws ecs list-services --cluster <cluster-name>

# Describe service
aws ecs describe-services \
  --cluster <cluster-name> \
  --services <service-name>

# List tasks in cluster
aws ecs list-tasks --cluster <cluster-name>

# Describe task
aws ecs describe-tasks \
  --cluster <cluster-name> \
  --tasks <task-id>

# Update service (force new deployment)
aws ecs update-service \
  --cluster <cluster-name> \
  --service <service-name> \
  --force-new-deployment

# Scale service
aws ecs update-service \
  --cluster <cluster-name> \
  --service <service-name> \
  --desired-count <number>

# Stop task
aws ecs stop-task \
  --cluster <cluster-name> \
  --task <task-id>

# Register task definition
aws ecs register-task-definition --cli-input-json file://<task-def>.json

# List task definitions
aws ecs list-task-definitions

# Deregister task definition
aws ecs deregister-task-definition --task-definition <task-def-arn>
```

### ECR Commands

```bash
# List ECR repositories
aws ecr describe-repositories

# Get login password for Docker
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com

# Create repository
aws ecr create-repository --repository-name <repo-name>

# Delete repository
aws ecr delete-repository --repository-name <repo-name> --force

# List images in repository
aws ecr list-images --repository-name <repo-name>

# Delete image
aws ecr batch-delete-image \
  --repository-name <repo-name> \
  --image-ids imageTag=<tag>
```

### IAM Commands

```bash
# List IAM users
aws iam list-users

# List IAM roles
aws iam list-roles

# Get current user identity
aws sts get-caller-identity

# Create IAM role
aws iam create-role \
  --role-name <role-name> \
  --assume-role-policy-document file://<policy>.json

# Attach policy to role
aws iam attach-role-policy \
  --role-name <role-name> \
  --policy-arn <policy-arn>

# List attached policies
aws iam list-attached-role-policies --role-name <role-name>
```

### CloudWatch Logs

```bash
# List log groups
aws logs describe-log-groups

# List log streams in a group
aws logs describe-log-streams --log-group-name <group-name>

# Get log events
aws logs get-log-events \
  --log-group-name <group-name> \
  --log-stream-name <stream-name>

# Tail logs in real-time
aws logs tail <log-group-name> --follow

# Filter logs
aws logs filter-log-events \
  --log-group-name <group-name> \
  --filter-pattern "<pattern>"
```

---

## Kafka Commands

### Kafka Broker Commands (Inside Container)

```bash
# Enter Kafka container
docker exec -it kafka-broker bash

# List all topics
kafka-topics --bootstrap-server kafka:9092 --list

# Describe a topic
kafka-topics --bootstrap-server kafka:9092 --describe --topic <topic-name>

# Create a topic
kafka-topics --bootstrap-server kafka:9092 --create \
  --topic <topic-name> \
  --partitions 3 \
  --replication-factor 1

# Delete a topic
kafka-topics --bootstrap-server kafka:9092 --delete --topic <topic-name>

# Check broker API versions
kafka-broker-api-versions --bootstrap-server kafka:9092
```

### Kafka Consumer Commands

```bash
# Consume from beginning
kafka-console-consumer --bootstrap-server kafka:9092 \
  --topic <topic-name> \
  --from-beginning

# Consume latest messages
kafka-console-consumer --bootstrap-server kafka:9092 \
  --topic <topic-name>

# Consume with key and value
kafka-console-consumer --bootstrap-server kafka:9092 \
  --topic <topic-name> \
  --property print.key=true \
  --property key.separator=":"

# Consume specific number of messages
kafka-console-consumer --bootstrap-server kafka:9092 \
  --topic <topic-name> \
  --max-messages 10
```

### Kafka Producer Commands

```bash
# Produce messages interactively
kafka-console-producer --bootstrap-server kafka:9092 \
  --topic <topic-name>

# Produce with key
kafka-console-producer --bootstrap-server kafka:9092 \
  --topic <topic-name> \
  --property parse.key=true \
  --property key.separator=":"
```

### Kafka Consumer Groups

```bash
# List all consumer groups
kafka-consumer-groups --bootstrap-server kafka:9092 --list

# Describe consumer group (check lag)
kafka-consumer-groups --bootstrap-server kafka:9092 \
  --group <group-name> \
  --describe

# Reset consumer group offset to earliest
kafka-consumer-groups --bootstrap-server kafka:9092 \
  --group <group-name> \
  --topic <topic-name> \
  --reset-offsets --to-earliest \
  --execute

# Reset consumer group offset to specific position
kafka-consumer-groups --bootstrap-server kafka:9092 \
  --group <group-name> \
  --topic <topic-name> \
  --reset-offsets --to-offset <offset> \
  --execute
```

---

## PostgreSQL Commands

### Connection

```bash
# Connect to PostgreSQL (local)
psql -h localhost -U <username> -d <database>

# Connect to RDS
psql -h <rds-endpoint> -U <username> -d <database>

# Connect with password from environment
PGPASSWORD=<password> psql -h <host> -U <username> -d <database>

# Execute SQL file
psql -h <host> -U <username> -d <database> -f script.sql
```

### Database Operations

```sql
-- List all databases
\l

-- Connect to database
\c <database-name>

-- List all tables
\dt

-- Describe table structure
\d <table-name>

-- List all schemas
\dn

-- List all views
\dv

-- Execute SQL file from psql
\i /path/to/file.sql

-- Quit
\q
```

### Common SQL Queries

```sql
-- Count rows in table
SELECT COUNT(*) FROM <table-name>;

-- Show first 10 rows
SELECT * FROM <table-name> LIMIT 10;

-- Show table size
SELECT pg_size_pretty(pg_total_relation_size('<table-name>'));

-- Show database size
SELECT pg_size_pretty(pg_database_size('<database-name>'));

-- Current connections
SELECT * FROM pg_stat_activity;

-- Kill specific connection
SELECT pg_terminate_backend(<pid>);

-- Vacuum table
VACUUM ANALYZE <table-name>;
```

---

## Git Commands

### Basic Operations

```bash
# Check current status
git status

# Check current branch
git branch

# Switch to branch
git checkout <branch-name>

# Create and switch to new branch
git checkout -b <branch-name>

# Add files to staging
git add <file>
git add .  # Add all files

# Commit changes
git commit -m "commit message"

# Push to remote
git push origin <branch-name>

# Pull from remote
git pull origin <branch-name>

# Fetch latest changes (without merging)
git fetch origin
```

### Branch Management

```bash
# List all branches
git branch -a

# Delete local branch
git branch -d <branch-name>

# Force delete local branch
git branch -D <branch-name>

# Delete remote branch
git push origin --delete <branch-name>

# Rename current branch
git branch -m <new-name>

# Create branch from specific commit
git checkout -b <branch-name> <commit-hash>
```

### Undo Changes

```bash
# Discard local changes in file
git checkout -- <file>

# Discard all local changes
git reset --hard HEAD

# Unstage file
git reset HEAD <file>

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Revert a specific commit (creates new commit)
git revert <commit-hash>
```

### Viewing History

```bash
# View commit history
git log

# View compact history
git log --oneline

# View history with graph
git log --graph --oneline --all

# View changes in last commit
git show HEAD

# View changes in specific commit
git show <commit-hash>

# View file history
git log --follow <file>
```

### Stashing

```bash
# Stash current changes
git stash

# Stash with message
git stash save "message"

# List all stashes
git stash list

# Apply most recent stash
git stash apply

# Apply specific stash
git stash apply stash@{n}

# Pop stash (apply and remove)
git stash pop

# Delete stash
git stash drop stash@{n}

# Clear all stashes
git stash clear
```

---

## Python Commands

### Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Mac/Linux)
source venv/bin/activate

# Activate virtual environment (Windows)
venv\Scripts\activate

# Deactivate virtual environment
deactivate

# Install requirements
pip install -r requirements.txt

# Freeze current packages
pip freeze > requirements.txt
```

### Package Management

```bash
# Install package
pip install <package-name>

# Install specific version
pip install <package-name>==<version>

# Upgrade package
pip install --upgrade <package-name>

# Uninstall package
pip uninstall <package-name>

# List installed packages
pip list

# Show package details
pip show <package-name>

# Search for package
pip search <package-name>
```

### Running Scripts

```bash
# Run Python script
python script.py

# Run with arguments
python script.py --arg1 value1 --arg2 value2

# Run module
python -m module_name

# Run with profiling
python -m cProfile script.py

# Run with debugging
python -m pdb script.py
```

---

## Troubleshooting Commands

### System Information

```bash
# Check disk space
df -h

# Check memory usage
free -h

# Check CPU usage
top

# Check process
ps aux | grep <process-name>

# Kill process
kill <pid>
kill -9 <pid>  # Force kill

# Check port usage
lsof -i :<port>
netstat -an | grep <port>

# Check network connectivity
ping <host>
telnet <host> <port>
curl <url>
```

### Docker Troubleshooting

```bash
# Check Docker service status
systemctl status docker

# Restart Docker service
sudo systemctl restart docker

# View Docker events
docker events

# Check container health
docker inspect --format='{{.State.Health.Status}}' <container-name>

# Check container exit code
docker inspect --format='{{.State.ExitCode}}' <container-name>

# Check resource limits
docker stats <container-name>
```

### Kafka Troubleshooting

```bash
# Check if Kafka is listening
netstat -an | grep 9092

# Check Kafka logs
docker logs kafka-broker | tail -100

# Check topic message count
kafka-run-class kafka.tools.GetOffsetShell \
  --broker-list kafka:9092 \
  --topic <topic-name>

# Verify consumer is consuming
kafka-consumer-groups --bootstrap-server kafka:9092 \
  --group <group-name> \
  --describe
```

### AWS Troubleshooting

```bash
# Check AWS credentials
aws sts get-caller-identity

# Check AWS region
aws configure get region

# Test S3 access
aws s3 ls

# Test RDS connectivity
telnet <rds-endpoint> 5432

# Check ECS task logs
aws logs tail /ecs/<cluster>/<service> --follow

# Check service events
aws ecs describe-services \
  --cluster <cluster-name> \
  --services <service-name> \
  --query 'services[0].events[:5]'
```

---

## Quick Tips

### Docker Tips

1. **Always use `-d` flag** with `docker-compose up` to run in background
2. **Use `docker-compose logs -f`** to follow logs in real-time
3. **Clean up regularly** with `docker system prune` to free up space
4. **Name your containers** using `container_name` in docker-compose for easy reference

### AWS Tips

1. **Always specify region** with `--region` flag or set default
2. **Use `--query` and `--output`** to format output
3. **Test with `--dry-run`** when available (EC2 commands)
4. **Set up AWS profiles** for multiple accounts

### Kafka Tips

1. **Always check consumer lag** before troubleshooting
2. **Use Kafka UI** (http://localhost:8090) for visual inspection
3. **Topic names are case-sensitive**
4. **Delete topics carefully** - data is permanently lost

### Git Tips

1. **Always pull before push** to avoid conflicts
2. **Use meaningful commit messages**
3. **Create feature branches** - never work on main
4. **Stash before switching branches** if you have uncommitted changes

---

**Last Updated**: 2025-10-21  
**Maintained by**: Production ML Systems Course Team


