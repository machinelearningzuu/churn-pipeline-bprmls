#!/bin/bash
# ==========================================
# Local Deployment Script
# ==========================================
# Complete end-to-end local deployment
#
# Usage: ./run_local.sh [--force-rebuild]
#
# Prerequisites:
#   - Docker Desktop running
#   - AWS credentials configured (for S3/RDS)
#   - .env file with correct settings
#
# Options:
#   --force-rebuild  Force rebuild of all Docker images (default: false)
# ==========================================

set -e  # Exit on any error

# Parse arguments
FORCE_REBUILD=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --force-rebuild)
            FORCE_REBUILD=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: ./run_local.sh [--force-rebuild]"
            exit 1
            ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Set environment variables
export MLFLOW_TRACKING_URI="http://localhost:5001"
export MLFLOW_DEFAULT_ARTIFACT_ROOT="s3://zuucrew-mlflow-artifacts-prod/artifacts/mlflow-artifacts"
export PYTHONPATH="."
export AWS_PROFILE="${AWS_PROFILE:-default}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 LOCAL DEPLOYMENT - End to End"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check AWS credentials
echo "🔍 Checking AWS credentials..."
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo -e "${RED}❌ AWS credentials not found or invalid!${NC}"
    echo ""
    echo "AWS credentials are needed for S3 access and RDS."
    echo ""
    echo "Please configure AWS credentials:"
    echo "  1. Run: aws configure"
    echo "  2. Or set: export AWS_PROFILE=default"
    echo "  3. Or check: ~/.aws/credentials"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=$(aws configure get region 2>/dev/null || echo "ap-south-1")

echo -e "${GREEN}✅ AWS credentials verified${NC}"
echo "   Account: $ACCOUNT_ID"
echo "   Region: $REGION"
echo "   Profile: $AWS_PROFILE"
echo ""

# Check Docker
echo "🐳 Checking Docker..."
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running!${NC}"
    echo "Please start Docker Desktop and try again."
    exit 1
fi
echo -e "${GREEN}✅ Docker is running${NC}"
echo ""

# Check for running ECS services
echo "🔍 Checking for running ECS services..."
if aws sts get-caller-identity >/dev/null 2>&1; then
    ECS_CLUSTER="churn-pipeline-ecs"
    ECS_REGION=$(aws configure get region 2>/dev/null || echo "ap-south-1")
    
    # Check if cluster exists and has running tasks
    ECS_TASKS=$(aws ecs list-tasks --cluster "$ECS_CLUSTER" --region "$ECS_REGION" --desired-status RUNNING --query 'taskArns' --output text 2>/dev/null || echo "")
    
    if [ -n "$ECS_TASKS" ] && [ "$ECS_TASKS" != "None" ]; then
        echo -e "${YELLOW}⚠️  WARNING: ECS services are currently running!${NC}"
        echo ""
        echo "Cluster: $ECS_CLUSTER"
        echo "Region: $ECS_REGION"
        echo ""
        echo "Running local and ECS simultaneously may cause:"
        echo "   • Conflicting DAG executions"
        echo "   • RDS connection issues"
        echo "   • S3 artifact collisions"
        echo "   • MLflow experiment conflicts"
        echo ""
        echo "💡 Recommended: Stop ECS services first"
        echo "   ./stop_ecs.sh"
        echo ""
        read -p "Continue anyway? (not recommended - yes/no): " continue_anyway
        if [ "$continue_anyway" != "yes" ]; then
            echo ""
            echo -e "${RED}❌ Deployment cancelled${NC}"
            echo ""
            echo "To stop ECS services:"
            echo "  ./stop_ecs.sh           # Pause ECS (keep resources)"
            echo "  make aws-stop           # Complete cleanup (delete all)"
            exit 1
        fi
        echo ""
        echo -e "${YELLOW}⚠️  Proceeding with both environments running (not recommended)${NC}"
        echo ""
    else
        echo -e "${GREEN}✅ No ECS services running${NC}"
        echo ""
    fi
else
    echo -e "${YELLOW}⚠️  Cannot check ECS (AWS credentials issue)${NC}"
    echo ""
fi

# Confirmation prompt
echo -e "${YELLOW}This will start the complete local ML pipeline:${NC}"
echo "  • MLflow Tracking Server"
echo "  • Airflow (webserver, scheduler, worker, flower)"
echo "  • Local PostgreSQL (for Airflow metadata)"
echo "  • Redis (for Celery backend)"
echo "  • Kafka Stack (broker, producer, consumer, analytics)"
echo "  • Kafka UI (monitoring)"
echo "  • Initial model training (for real-time inference)"
echo ""
read -p "Continue with local deployment? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo -e "${RED}❌ Deployment cancelled${NC}"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Starting Deployment..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 1: Build Docker images
if [ "$FORCE_REBUILD" = true ]; then
    echo -e "${BLUE}1️⃣ Building Docker images (forced rebuild)...${NC}"
    make docker-build
else
    echo -e "${BLUE}1️⃣ Checking Docker images...${NC}"
    # Check if images exist
    IMAGES_EXIST=true
    for img in churn-pipeline/mlflow:latest churn-pipeline/data:latest churn-pipeline/model:latest churn-pipeline/inference:latest; do
        if ! docker image inspect "$img" >/dev/null 2>&1; then
            IMAGES_EXIST=false
            break
        fi
    done
    
    if [ "$IMAGES_EXIST" = false ]; then
        echo "   📦 Images not found, building..."
        make docker-build
    else
        echo -e "   ${GREEN}✅ Images already exist (use --force-rebuild to rebuild)${NC}"
    fi
fi
echo ""

# Step 2: Build Airflow image
if [ "$FORCE_REBUILD" = true ]; then
    echo -e "${BLUE}2️⃣ Building Airflow image (forced rebuild)...${NC}"
    make airflow-build
else
    echo -e "${BLUE}2️⃣ Checking Airflow image...${NC}"
    if ! docker image inspect churn-pipeline/airflow:2.8.1-amazon >/dev/null 2>&1; then
        echo "   📦 Airflow image not found, building..."
        make airflow-build
    else
        echo -e "   ${GREEN}✅ Airflow image already exists (use --force-rebuild to rebuild)${NC}"
    fi
fi
echo ""

# Step 2.5: Build Kafka services
if [ "$FORCE_REBUILD" = true ]; then
    echo -e "${BLUE}2.5️⃣ Building Kafka services (forced rebuild)...${NC}"
    make kafka-build
else
    echo -e "${BLUE}2.5️⃣ Checking Kafka service images...${NC}"
    KAFKA_IMAGES_EXIST=true
    for img in churn-pipeline/kafka-producer:latest churn-pipeline/kafka-consumer:latest churn-pipeline/kafka-analytics:latest; do
        if ! docker image inspect "$img" >/dev/null 2>&1; then
            KAFKA_IMAGES_EXIST=false
            break
        fi
    done
    
    if [ "$KAFKA_IMAGES_EXIST" = false ]; then
        echo "   📦 Kafka images not found, building..."
        make kafka-build
    else
        echo -e "   ${GREEN}✅ Kafka images already exist (use --force-rebuild to rebuild)${NC}"
    fi
fi
echo ""

# Step 3: Start MLflow and pipeline services
echo -e "${BLUE}3️⃣ Starting MLflow and pipeline services...${NC}"
make docker-up
echo ""

# Wait for MLflow to be ready
echo "⏳ Waiting for MLflow to initialize..."
sleep 10
echo ""

# Step 4: Initialize Airflow with local PostgreSQL
echo -e "${BLUE}4️⃣ Initializing Airflow (local PostgreSQL)...${NC}"
echo -e "${YELLOW}⚠️  This will clear ALL DAG history and create a fresh database${NC}"
make airflow-init
echo ""

# Step 5: Start Airflow services
echo -e "${BLUE}5️⃣ Starting Airflow services...${NC}"
make airflow-up
echo ""

# Wait for Airflow to be ready
echo "⏳ Waiting for Airflow to initialize..."
sleep 15
echo ""

# Step 6: Train initial model (local - faster than Airflow DAGs)
echo -e "${BLUE}6️⃣ Training initial model (required for Kafka consumer)...${NC}"
echo "   Using local pipelines for speed (Airflow DAGs available for scheduled retraining)"
echo ""

echo "   📊 Running data preprocessing..."
make data-pipeline
echo ""

echo "   🎯 Running model training..."
make train-pipeline
echo ""

echo -e "${GREEN}✅ Initial model trained and saved to S3/MLflow${NC}"
echo ""

# Step 7: Setup RDS analytics tables
echo -e "${BLUE}7️⃣ Setting up RDS analytics tables (for Kafka)...${NC}"
if make setup-analytics-tables 2>/dev/null; then
    echo -e "${GREEN}✅ RDS analytics tables created${NC}"
else
    echo -e "${YELLOW}⚠️  RDS tables setup failed (check RDS credentials in .env)${NC}"
    echo "   You can create them later with: make setup-analytics-tables"
fi
echo ""

# Step 8: Start Kafka stack
echo -e "${BLUE}8️⃣ Starting Kafka stack (real-time inference)...${NC}"
make kafka-up
echo ""

# Wait for Kafka to be ready
echo "⏳ Waiting for Kafka to initialize..."
sleep 30
echo ""

# Verify services
echo "🔍 Verifying all services..."
echo ""

# Check Docker containers
RUNNING_CONTAINERS=$(docker ps --filter "status=running" | grep -c "churn-pipeline\|airflow\|mlflow\|kafka" || echo "0")
echo "   Running containers: $RUNNING_CONTAINERS"

# Check Airflow health
if docker exec airflow-webserver airflow db check >/dev/null 2>&1; then
    echo -e "   ${GREEN}✅ Airflow: Connected${NC}"
else
    echo -e "   ${YELLOW}⚠️  Airflow: Check manually${NC}"
fi

# Check Kafka health
if docker exec kafka-broker kafka-topics --list --bootstrap-server localhost:9092 >/dev/null 2>&1; then
    echo -e "   ${GREEN}✅ Kafka: Running${NC}"
else
    echo -e "   ${YELLOW}⚠️  Kafka: Check manually${NC}"
fi

# Check Kafka topics
KAFKA_TOPICS=$(docker exec kafka-broker kafka-topics --list --bootstrap-server localhost:9092 2>/dev/null | wc -l || echo "0")
echo "   Kafka topics: $KAFKA_TOPICS"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ LOCAL DEPLOYMENT COMPLETE!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Access URLs:"
echo "   • Airflow UI:  http://localhost:8080 (admin/admin)"
echo "   • MLflow UI:   http://localhost:5001"
echo "   • Kafka UI:    http://localhost:8090"
echo "   • Flower UI:   http://localhost:5555"
echo ""
echo "📋 Airflow DAGs (for scheduled retraining):"
echo "   • data_pipeline_dag    → Data preprocessing"
echo "   • model_training_dag   → Model training"
echo "   Note: Inference now handled by Kafka (real-time)"
echo ""
echo "🔄 Kafka Services (running continuously):"
echo "   • Producer:   Streaming customer events (10/sec)"
echo "   • Consumer:   Real-time inference (1000 samples / 30 sec)"
echo "   • Analytics:  Aggregating to RDS (hourly/daily metrics)"
echo ""
echo "💡 Useful commands:"
echo "   • Check status:    make docker-status && make airflow-status && make kafka-status"
echo "   • Rebuild images:  ./run_local.sh --force-rebuild"
echo "   • Airflow logs:    docker logs airflow-scheduler -f"
echo "   • Kafka logs:      make kafka-logs"
echo "   • Consumer logs:   docker logs kafka-consumer -f"
echo "   • Stop Airflow:    make airflow-down"
echo "   • Stop Kafka:      make kafka-down"
echo "   • Stop all:        make airflow-down && make docker-down && make kafka-down"
echo ""
echo "📊 Real-time Monitoring:"
echo "   • Kafka UI:        Open http://localhost:8090"
echo "   • RDS predictions: Check churn_predictions table"
echo "   • View metrics:    SELECT * FROM v_realtime_dashboard;"
echo ""
echo -e "${GREEN}🎉 Complete ML pipeline is ready!${NC}"
echo -e "${GREEN}   Real-time inference is now running via Kafka! 🚀${NC}"
echo ""