# Kafka Real-Time Streaming - A Practical Guide

**Learn how to build real-time ML prediction systems using Apache Kafka**

Hey there! 👋 Welcome to the Kafka integration guide. By the end of this guide, you'll understand how to build a production-quality streaming system for real-time churn predictions. Don't worry if you've never used Kafka before - we'll start from the basics and build up gradually.

---

## What You'll Learn

By the end of this guide, you'll be able to:
- Explain what Kafka is and why we use it
- Set up a Kafka broker using Docker
- Build a producer that streams customer data
- Create a consumer that makes ML predictions in real-time
- Store prediction results in a database
- Monitor your streaming system using Kafka UI
- Troubleshoot common Kafka issues

**Time to Complete**: 3-4 hours (including hands-on practice)

---

## Prerequisites

Before starting, make sure you have:
- [x] Docker and Docker Compose installed
- [x] Basic understanding of Python
- [x] Familiarity with terminal/command line
- [x] The project code cloned on your machine

Don't worry if you're not an expert in any of these - we'll guide you through everything!

---

## Table of Contents

1. [Why Do We Need Kafka?](#why-do-we-need-kafka)
2. [Understanding Event-Driven Architecture](#understanding-event-driven-architecture)
3. [The Complete System Overview](#the-complete-system-overview)
4. [Setting Up Kafka](#setting-up-kafka)
5. [The Producer Service](#the-producer-service)
6. [The Consumer Service](#the-consumer-service)
7. [The Analytics Service](#the-analytics-service)
8. [Monitoring with Kafka UI](#monitoring-with-kafka-ui)
9. [Running Everything Together](#running-everything-together)
10. [Troubleshooting Guide](#troubleshooting-guide)

---

## Why Do We Need Kafka?

Let's start with a simple question: **Why can't we just make predictions using a regular API?**

Imagine you have a web application where users interact with your bank. Every time a user performs an action (login, transfer money, update profile), you want to predict if they might churn (leave your service).

### The Traditional Approach (Synchronous)

```
User Action → API Call → ML Model → Database → Response
              ↓
         User Waits... 😴
```

**Problems with this approach:**
1. **Slow user experience**: User has to wait for the model to finish (could take 1-2 seconds)
2. **Single point of failure**: If the ML service crashes, the entire request fails
3. **Hard to scale**: As traffic grows, the API becomes a bottleneck
4. **Tight coupling**: The web app needs to know all about the ML service

### The Kafka Approach (Asynchronous)

```
User Action → Kafka → (returns immediately) ✅
              ↓
          Consumer → ML Model → Kafka → Analytics → Database
```

**Benefits of this approach:**
1. **Fast response**: User gets immediate feedback (< 100ms)
2. **Decoupled services**: Services don't depend on each other directly
3. **Scalable**: Add more consumers to handle more traffic
4. **Reliable**: If one service crashes, messages wait in Kafka

Think of Kafka like a **post office**:
- Producers are people sending letters (messages)
- Kafka is the post office that holds letters safely
- Consumers are people receiving letters
- If the receiver is not home, the letter waits at the post office

---

## Understanding Event-Driven Architecture

Before we dive into Kafka, let's understand the big picture.

### What is an Event?

An **event** is something that happened in your system. For example:
- A user logged in
- A transaction was completed
- A customer updated their profile
- A prediction was made

In our system, events are represented as JSON messages:

```json
{
  "CustomerId": 15634602,
  "Age": 42,
  "Balance": 0.0,
  "Geography": "France",
  "Gender": "Female",
  "timestamp": "2025-10-21T10:15:30.123Z"
}
```

### Key Concepts

Let's break down some important Kafka terminology:

#### 1. **Topics** (Think: Channels or Folders)

A topic is like a folder or channel where messages are stored. We have two main topics:
- `customer-events`: Raw customer data coming in
- `predictions`: ML predictions going out

#### 2. **Producers** (Think: Message Senders)

A producer sends messages to a topic. In our case:
- The producer reads customer data from CSV
- Sends it to the `customer-events` topic
- Simulates real-time customer activity

#### 3. **Consumers** (Think: Message Receivers)

A consumer reads messages from a topic. We have two consumers:
- **ML Consumer**: Reads customer events, makes predictions
- **Analytics Consumer**: Reads predictions, stores in database

#### 4. **Brokers** (Think: The Post Office)

The broker is the Kafka server that stores and manages messages. It ensures:
- Messages are safely stored
- Consumers can read them at their own pace
- Messages persist even if consumers are offline

---

## The Complete System Overview

Here's how all the pieces fit together:

```
┌─────────────────────┐
│  CSV Data           │  ← Our "database" of customers
│  (ChurnModelling)   │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────────────────────────┐
│  PRODUCER SERVICE                        │
│  • Reads CSV row by row                  │
│  • Sends 10 events/second                │
│  • Simulates real-time traffic          │
└──────────┬──────────────────────────────┘
           │
           ↓ Publishes to "customer-events"
┌─────────────────────────────────────────┐
│  KAFKA BROKER                            │
│  • Stores messages safely                │
│  • Topic: "customer-events"              │
│  • Messages wait here until consumed     │
└──────────┬──────────────────────────────┘
           │
           ↓ Consumer reads batches of 1000
┌─────────────────────────────────────────┐
│  CONSUMER SERVICE (ML Engine)            │
│  • Collects 1000 messages OR waits 30s  │
│  • Downloads model from S3/MLflow        │
│  • Makes predictions in batch            │
│  • Publishes to "predictions" topic     │
└──────────┬──────────────────────────────┘
           │
           ↓ Publishes to "predictions"
┌─────────────────────────────────────────┐
│  KAFKA BROKER                            │
│  • Topic: "predictions"                  │
└──────────┬──────────────────────────────┘
           │
           ↓
┌─────────────────────────────────────────┐
│  ANALYTICS SERVICE                       │
│  • Reads prediction results              │
│  • Stores in PostgreSQL (RDS)           │
│  • Creates data for dashboards          │
└──────────┬──────────────────────────────┘
           │
           ↓
┌─────────────────────────────────────────┐
│  POSTGRESQL DATABASE                     │
│  • Table: churn_predictions              │
│  • Used by AWS QuickSight for BI        │
└─────────────────────────────────────────┘
```

### Message Flow Example

Let's trace what happens to a single customer event:

**Step 1**: Producer sends message
```json
{
  "CustomerId": 15634602,
  "Age": 42,
  "Geography": "France",
  ...
}
```

**Step 2**: Kafka stores it in `customer-events` topic

**Step 3**: Consumer receives it (with 999 other messages)

**Step 4**: Consumer makes prediction
```python
prediction = model.predict(features)  # Returns: 0 (won't churn)
probability = model.predict_proba(features)[0][1]  # Returns: 0.13 (13% chance)
```

**Step 5**: Consumer publishes result to `predictions` topic
```json
{
  "CustomerId": 15634602,
  "ChurnPrediction": 0,
  "ChurnProbability": 0.13,
  "RiskCategory": "Low",
  "ProcessingTimeMs": 23
}
```

**Step 6**: Analytics service stores in database

**Step 7**: Business team views dashboard with insights! 📊

---

## Setting Up Kafka

Now let's get our hands dirty! We'll set up Kafka using Docker Compose.

### Understanding KRaft Mode

Before Kafka 3.0, you needed two separate systems:
1. **Zookeeper** (to manage Kafka metadata)
2. **Kafka** (to handle messages)

Since Kafka 3.3, we can use **KRaft mode** (Kafka Raft) which combines both into one. This is simpler and faster!

```
Old way:  Zookeeper ← Kafka Broker
New way:  Kafka Broker (self-managed)
```

### Docker Compose Configuration

**Key settings in our Kafka setup (`docker-compose.kafka.yml`):**

**Image & Container:**
- Uses official Confluent Kafka 7.5.0 image
- Container named `kafka-broker` with hostname `kafka` (important for Docker DNS)

**Ports:**
- Port 9092: Used by Docker containers (producer, consumer, analytics) to connect
- Port 9094: Used by your laptop terminal for testing commands

**KRaft Mode Settings:**
- KAFKA_PROCESS_ROLES: 'broker,controller' → This single container does both jobs (no Zookeeper!)
- KAFKA_NODE_ID: 1 → Identifies this Kafka node

**Network Configuration (the tricky part):**
- Three listeners: one for internal Docker communication (9092), one for Kafka's self-management (9093), and one for external access (9094)
- This allows both containers and your laptop to connect to Kafka

**Development Features:**
- Auto-create topics enabled → Topics are created automatically when producer sends messages (no manual setup needed)

### Understanding Kafka Networking (The Tricky Part!)

This is the most confusing part of Kafka. Let's break it down:

**Why do we need different listeners?**

Kafka needs to be accessible from two places:
1. **Inside Docker** (our producer and consumer containers)
2. **Outside Docker** (your terminal for testing)

**The three listeners:**

| Listener | Port | Who Uses It? | Purpose |
|----------|------|-------------|---------|
| `PLAINTEXT://kafka:9092` | 9092 | Docker containers | Internal communication |
| `CONTROLLER://kafka:9093` | 9093 | Kafka itself | KRaft consensus |
| `PLAINTEXT_HOST://0.0.0.0:9094` | 9094 | Your laptop | Testing from terminal |

**Visual Example:**

```
┌─────────────────────────────────────────┐
│  Docker Network                          │
│                                          │
│  ┌──────────┐    kafka:9092             │
│  │ Producer │─────────────┐             │
│  └──────────┘             │             │
│                            ↓             │
│  ┌──────────┐         ┌────────┐        │
│  │ Consumer │────────▶│ Kafka  │        │
│  └──────────┘         │ Broker │        │
│                        └────────┘        │
│                            ↑             │
│  ┌──────────┐             │             │
│  │Analytics │─────────────┘             │
│  └──────────┘                            │
│                                          │
└──────────────────┼──────────────────────┘
                   │ Port mapping 9094:9092
                   │
         ┌─────────┴────────────┐
         │  Your Mac Terminal   │
         │  localhost:9094      │
         └──────────────────────┘
```

### Starting Kafka

Let's start Kafka step by step:

**Step 1**: Make sure Docker is running
```bash
docker --version
# Should show: Docker version 20.x.x or higher
```

**Step 2**: Create the Docker network (if not exists)
```bash
docker network create churn-pipeline-network
```

**Step 3**: Start Kafka
```bash
docker-compose -f docker-compose.kafka.yml up -d kafka
```

**Step 4**: Check if Kafka is running
```bash
docker ps | grep kafka-broker
# Should show: kafka-broker ... Up (healthy)
```

**Step 5**: Check Kafka logs
```bash
docker logs kafka-broker | tail -20
# Should see: "Kafka Server started"
```

**Step 6**: Test Kafka connection
```bash
docker exec kafka-broker kafka-broker-api-versions --bootstrap-server kafka:9092
# Should show a list of API versions (means Kafka is working!)
```

### Common Startup Issues

**Issue 1**: Port already in use
```
Error: port 9092 is already allocated
```
**Fix**: Another Kafka is running. Stop it:
```bash
docker ps  # Find the container
docker stop <container-name>
```

**Issue 2**: Kafka keeps restarting
```bash
docker ps  # Shows "Restarting (1) 2 seconds ago"
```
**Fix**: Check logs for errors:
```bash
docker logs kafka-broker
```
Common causes:
- Not enough memory (allocate at least 2GB to Docker)
- Port conflicts
- Corrupted data volume

**Fix by cleaning volumes**:
```bash
docker-compose -f docker-compose.kafka.yml down -v
docker-compose -f docker-compose.kafka.yml up -d kafka
```

---

## The Producer Service

The producer's job is to simulate real-time customer activity by streaming data from our CSV file to Kafka.

### How It Works

**The producer service does 4 main things:**

1. **Loads the CSV file** (ChurnModelling.csv) into memory when it starts
2. **Reads one row at a time** sequentially (customer 1, then customer 2, then customer 3...)
3. **Converts each row to a JSON message** with all customer fields plus a timestamp
4. **Sends the message to Kafka** topic called "customer-events"

**Key behavior:**
- When it reaches the end of the CSV, it loops back to the beginning (simulating continuous customer activity)
- It waits between each message to control the rate (e.g., 10 events per second = 0.1 seconds between messages)
- It logs progress every 100 events so you can see it's working
- It runs for a specified duration (default 1 hour) then stops

### Understanding the Rate Parameter

The `--rate` parameter controls how fast events are sent:

```bash
--rate 10   # 10 events/second (good for testing)
--rate 100  # 100 events/second (stress testing)
--rate 1    # 1 event/second (very slow, easy to debug)
```

**Why not send everything at once?**

We want to simulate real-world traffic where events come in gradually. This helps us:
- Test how the system handles steady load
- Monitor consumer lag
- Practice scaling strategies

### Starting the Producer

**Step 1**: Start the producer with default settings (10 events/sec for 1 hour)
```bash
docker-compose -f docker-compose.kafka.yml up -d producer
```

**Step 2**: Watch the logs
```bash
docker logs -f kafka-producer
```

You should see:
```
✅ Connected to Kafka at kafka:9092
✅ Produced 10 events
✅ Produced 20 events
✅ Produced 30 events
...
```

**Step 3**: Verify messages are in Kafka
```bash
# Count messages in topic
docker exec kafka-broker kafka-run-class kafka.tools.GetOffsetShell \
  --broker-list kafka:9092 \
  --topic customer-events

# Output: customer-events:0:156
# This means 156 messages in partition 0
```

### Adjusting Producer Settings

You can customize the producer by editing `docker-compose.kafka.yml`:

```yaml
producer:
  command: python producer_service.py --mode streaming --rate 50 --duration 7200
  #                                                      ↑              ↑
  #                                               50 events/sec    2 hours
```

**Common Scenarios:**

| Scenario | Rate | Duration | Use Case |
|----------|------|----------|----------|
| Quick test | 1 | 60 | Debugging (1 event/sec for 1 min) |
| Normal load | 10 | 3600 | Simulating steady traffic |
| High load | 100 | 1800 | Stress testing consumer |
| Demo | 5 | 600 | Showing to stakeholders (slow enough to watch) |

---

## The Consumer Service

This is where the magic happens! The consumer receives customer events and makes ML predictions.

### Why Batch Processing?

Instead of making predictions one-by-one, we process messages in **batches**. Here's why:

**Option 1: Process one message at a time**
```python
for message in consumer:
    prediction = model.predict([message])  # Slow! ~100ms per message
```
- Throughput: 10 messages/second
- ❌ Can't keep up with producer sending 100 msgs/sec

**Option 2: Process in batches**
```python
batch = []
for i in range(1000):
    batch.append(next(consumer))

predictions = model.predict(batch)  # Fast! ~200ms for 1000 messages
```
- Throughput: 5000 messages/second
- ✅ Can easily handle high traffic

**The batch strategy:**
- Collect **1000 messages** OR **wait 30 seconds**, whichever comes first
- This ensures we process quickly during high traffic
- And don't wait too long during low traffic

### How the Consumer Works

**The consumer service follows this workflow:**

**Initialization (when it starts):**
1. Connects to Kafka and subscribes to the "customer-events" topic
2. Downloads the trained ML model and scaler from S3/MLflow
3. Sets up to read messages in batches (1000 messages or 30 seconds, whichever comes first)

**Main processing loop (runs continuously):**

**Step 1: Collect Batch**
- Polls Kafka for new messages every second
- Adds messages to a batch list
- Stops collecting when batch reaches 1000 messages OR 30 seconds have passed

**Step 2: Preprocess Data**
- Converts JSON messages to a DataFrame (table format)
- Performs one-hot encoding (Geography → Geography_France, Geography_Germany, Geography_Spain)
- Performs one-hot encoding (Gender → Gender_Male, Gender_Female)
- Selects only the features the model needs (Age, Balance, NumOfProducts, etc.)
- Scales the features using the pre-trained scaler

**Step 3: Make Predictions**
- Runs the entire batch through the ML model at once (much faster than one-by-one!)
- Gets predictions (0 or 1 for each customer)
- Gets probabilities (0.0 to 1.0 showing confidence)
- Times how long it takes (for monitoring)

**Step 4: Publish Results**
- For each customer in the batch, creates a result message with:
  - Customer ID
  - Prediction (will churn or won't churn)
  - Probability (how confident we are)
  - Risk category (Low/Medium/High based on probability)
  - Processing time
- Sends each result to the "predictions" topic
- Logs progress to console

**Then repeats from Step 1!**

### Understanding Consumer Groups

The `group_id` is important for scaling. Here's how it works:

**Scenario 1: Single Consumer**
```
Topic (3 partitions): [P0] [P1] [P2]
                       ↓    ↓    ↓
Consumer Group A:   [Consumer 1]
                    (reads all 3 partitions)
```

**Scenario 2: Three Consumers (Same Group)**
```
Topic (3 partitions): [P0]  [P1]  [P2]
                       ↓     ↓     ↓
Consumer Group A:   [C1]  [C2]  [C3]
                    (each reads 1 partition)
```

**Benefits:**
- Parallel processing (3x faster)
- Automatic load balancing
- If one consumer dies, others take over its partitions

### Starting the Consumer

**Step 1**: Start the consumer
```bash
docker-compose -f docker-compose.kafka.yml up -d consumer
```

**Step 2**: Watch the logs
```bash
docker logs -f kafka-consumer
```

You should see:
```
🚀 Consumer started, waiting for messages...
✅ Loaded model from S3: churn_model_v1.2.3
📦 Collected 1000 messages
✅ Processed batch in 245ms
📤 Published 1000 predictions
📦 Collected 1000 messages
...
```

**Step 3**: Check consumer lag (are we keeping up?)
```bash
docker exec kafka-broker kafka-consumer-groups \
  --bootstrap-server kafka:9092 \
  --group churn-consumer-group \
  --describe
```

Output:
```
GROUP              TOPIC            PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG
churn-consumer-group customer-events 0          15000          15010           10
```

**Understanding LAG:**
- `LAG = 0`: Consumer is caught up ✅
- `LAG < 100`: Slight delay (acceptable) ⚠️
- `LAG > 1000`: Consumer is falling behind! ❌

**If lag is increasing:**
1. Producer is too fast (reduce `--rate`)
2. Consumer is too slow (increase batch size)
3. Model inference is slow (optimize model)
4. Add more consumers (scale horizontally)

---

## The Analytics Service

The analytics service consumes prediction results and stores them in PostgreSQL for business intelligence.

### Why Separate from the Consumer?

You might wonder: "Why not write to the database directly from the consumer?"

**Separation of concerns:**
- Consumer focuses on ML predictions (throughput)
- Analytics focuses on data persistence (reliability)
- If database is down, predictions continue (resilience)
- Can scale each service independently (flexibility)

### How It Works

**The analytics service is simpler than the consumer:**

**Initialization (when it starts):**
1. Connects to Kafka and subscribes to the "predictions" topic
2. Connects to PostgreSQL database (AWS RDS)
3. Prepares to read predictions one by one

**Main loop (runs continuously):**

1. **Polls Kafka** for new prediction messages (checks every second)
2. **Receives a prediction message** (JSON with customer ID, prediction, probability, etc.)
3. **Inserts the prediction into the database:**
   - Customer ID
   - Prediction (0 or 1)
   - Probability (churn risk score)
   - Customer attributes (geography, age, balance, etc.)
   - Timestamp (when prediction was stored)
4. **Commits the transaction** (saves to database)
5. **Logs progress** every 100 predictions
6. **Repeats!**

**Key difference from consumer:** This service doesn't batch. It processes predictions one at a time because:
- Database writes are already fast
- We want predictions available immediately for dashboards
- Simpler error handling (if one fails, others still succeed)

### Database Schema

**The predictions are stored in a PostgreSQL table with these key fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | Auto-incrementing number | Unique ID for each prediction |
| `customer_id` | Text | Which customer this prediction is for |
| `prediction` | Integer (0 or 1) | 0 = won't churn, 1 = will churn |
| `probability` | Decimal (0.0-1.0) | Confidence level (0.13 = 13% chance of churn) |
| `risk_score` | Decimal (0.0-1.0) | Same as probability (used for business analysis) |
| `geography` | Text | France, Germany, or Spain |
| `age` | Integer | Customer's age |
| `balance` | Decimal | Account balance |
| `predicted_at` | Timestamp | When this prediction was made |

This structure allows business analysts to query and analyze churn patterns by geography, age groups, balance ranges, etc.

### Starting the Analytics Service

**Step 1**: Make sure RDS environment variables are set
```bash
# Check your .env file
cat .env | grep RDS
```

Should show:
```
RDS_HOST=your-rds-endpoint.rds.amazonaws.com
RDS_PORT=5432
RDS_DB_NAME=analytics
RDS_USERNAME=zuucrew
RDS_PASSWORD=your_password
```

**Step 2**: Start the analytics service
```bash
docker-compose -f docker-compose.kafka.yml up -d analytics
```

**Step 3**: Watch the logs
```bash
docker logs -f kafka-analytics
```

You should see:
```
📊 Analytics service started
✅ Connected to RDS at your-rds-endpoint:5432
✅ Stored 100 predictions
✅ Stored 200 predictions
...
```

**Step 4**: Verify data in database
```bash
# Connect to RDS
PGPASSWORD=$RDS_PASSWORD psql -h $RDS_HOST -U $RDS_USERNAME -d analytics

# Count predictions
SELECT COUNT(*) FROM churn_predictions;

# View recent predictions
SELECT 
    customer_id,
    prediction,
    ROUND(probability::numeric, 2) as prob,
    predicted_at
FROM churn_predictions
ORDER BY predicted_at DESC
LIMIT 10;
```

---

## Monitoring with Kafka UI

Kafka UI is a web-based tool that lets you visualize what's happening in your Kafka system.

### Starting Kafka UI

**Step 1**: Start Kafka UI
```bash
docker-compose -f docker-compose.kafka.yml up -d kafka-ui
```

**Step 2**: Open in browser
```bash
open http://localhost:8090
```

### What You Can Do with Kafka UI

#### 1. View Topics

Click **Topics** in the left sidebar. You should see:
- `customer-events` - Raw customer data
- `predictions` - ML prediction results

Click on a topic to see:
- Number of messages
- Number of partitions
- Size on disk
- Configuration settings

#### 2. Browse Messages

Click **Messages** tab to see actual message content:

```json
{
  "CustomerId": 15634602,
  "Age": 42,
  "Balance": 0.0,
  "Geography": "France",
  "timestamp": "2025-10-21T10:15:30.123Z"
}
```

**Tip**: You can search messages by content or filter by timestamp!

#### 3. Monitor Consumer Groups

Click **Consumer Groups** to see:
- Which consumers are active
- How many messages they've processed
- Current lag (how far behind they are)

This is super useful for debugging performance issues!

#### 4. Real-Time Monitoring

Leave the UI open while your system is running. You'll see:
- Messages appearing in real-time
- Consumer lag changing
- Partition distribution

---

## Running Everything Together

Now let's put it all together and run the complete streaming system!

### Step-by-Step Startup

**Step 1**: Start Kafka and Kafka UI
```bash
docker-compose -f docker-compose.kafka.yml up -d kafka kafka-ui
```

**Step 2**: Wait for Kafka to be healthy (check health status)
```bash
docker ps | grep kafka-broker
# Wait until you see "healthy" in the STATUS column
```

**Step 3**: Start the producer
```bash
docker-compose -f docker-compose.kafka.yml up -d producer
```

**Step 4**: Start the consumer
```bash
docker-compose -f docker-compose.kafka.yml up -d consumer
```

**Step 5**: Start the analytics service
```bash
docker-compose -f docker-compose.kafka.yml up -d analytics
```

**Step 6**: Open Kafka UI and watch the magic happen!
```bash
open http://localhost:8090
```

### What to Watch For

**In Kafka UI:**
1. Go to Topics → `customer-events`
   - Message count should be increasing
   - Should increase by ~10 messages/second

2. Go to Topics → `predictions`
   - Message count should be increasing
   - Should be slightly behind `customer-events` (due to batching)

3. Go to Consumer Groups
   - `churn-consumer-group` should show LAG close to 0
   - `analytics-group` should show LAG close to 0

**In Terminal (logs):**
```bash
# Producer logs
docker logs -f kafka-producer

# Consumer logs
docker logs -f kafka-consumer

# Analytics logs
docker logs -f kafka-analytics
```

### Quick Health Check

Run this command to see everything at once:
```bash
# Check all containers
docker-compose -f docker-compose.kafka.yml ps

# Should show all as "Up" and kafka as "Up (healthy)"
```

---

## Troubleshooting Guide

### Common Issues and How to Fix Them

#### Issue 1: Kafka Won't Start

**Symptoms:**
```bash
docker logs kafka-broker
# Shows: "Error: Storage not formatted" or keeps restarting
```

**Solution:**
```bash
# Stop and remove everything
docker-compose -f docker-compose.kafka.yml down -v

# Start fresh
docker-compose -f docker-compose.kafka.yml up -d kafka
```

#### Issue 2: Producer Can't Connect

**Symptoms:**
```bash
docker logs kafka-producer
# Shows: "Connection refused at kafka:9092"
```

**Solution:**
```bash
# Check if Kafka is healthy
docker ps | grep kafka-broker

# If not healthy, check Kafka logs
docker logs kafka-broker | tail -50

# Restart producer after Kafka is healthy
docker-compose -f docker-compose.kafka.yml restart producer
```

#### Issue 3: Consumer Not Consuming

**Symptoms:**
- Producer logs show events being sent
- Consumer logs show "Waiting for messages..."
- No predictions appearing

**Solution:**
```bash
# Check if consumer is subscribed correctly
docker logs kafka-consumer | grep "Subscribed"

# Check consumer group lag
docker exec kafka-broker kafka-consumer-groups \
  --bootstrap-server kafka:9092 \
  --group churn-consumer-group \
  --describe

# If lag is very high, restart consumer
docker-compose -f docker-compose.kafka.yml restart consumer
```

#### Issue 4: Model Not Found

**Symptoms:**
```bash
docker logs kafka-consumer
# Shows: "Could not load model from S3: NoSuchKey"
```

**Solution:**
```bash
# Make sure model was trained and uploaded
make train-pipeline

# Check if model exists in S3
aws s3 ls s3://your-bucket/models/

# Manual upload if needed
aws s3 cp artifacts/models/best_model.pkl s3://your-bucket/models/
```

#### Issue 5: RDS Connection Failed

**Symptoms:**
```bash
docker logs kafka-analytics
# Shows: "could not connect to server: Connection timed out"
```

**Solution:**
```bash
# Test RDS connection manually
PGPASSWORD=$RDS_PASSWORD psql -h $RDS_HOST -U $RDS_USERNAME -d analytics -c "SELECT 1;"

# If fails, check:
# 1. RDS security group allows your IP
# 2. RDS is running (check AWS console)
# 3. Credentials are correct in .env file
```

#### Issue 6: High Consumer Lag

**Symptoms:**
- Consumer lag keeps increasing
- LAG > 1000 and growing

**Solutions:**

**Option 1**: Reduce producer rate
```bash
# Edit docker-compose.kafka.yml
command: python producer_service.py --mode streaming --rate 5 --duration 3600
#                                                            ↑ reduced from 10
```

**Option 2**: Increase batch size (faster processing)
```bash
# Edit docker-compose.kafka.yml consumer environment
environment:
  BATCH_SIZE: 2000  # increased from 1000
```

**Option 3**: Add more consumer instances
```bash
# Scale consumer to 3 instances
docker-compose -f docker-compose.kafka.yml up -d --scale consumer=3
```

### Debugging Tips

**1. Check Service Dependencies**
```bash
# Make sure services started in correct order
docker-compose -f docker-compose.kafka.yml ps
```

**2. Check Logs in Order**
```bash
# Start from Kafka (foundation)
docker logs kafka-broker | tail -50

# Then producer
docker logs kafka-producer | tail -50

# Then consumer
docker logs kafka-consumer | tail -50

# Finally analytics
docker logs kafka-analytics | tail -50
```

**3. Check Network Connectivity**
```bash
# Test if services can reach Kafka
docker exec kafka-producer ping -c 3 kafka
docker exec kafka-consumer ping -c 3 kafka
```

**4. Check Topic Messages Manually**
```bash
# Read from customer-events topic
docker exec kafka-broker kafka-console-consumer \
  --bootstrap-server kafka:9092 \
  --topic customer-events \
  --from-beginning \
  --max-messages 5

# Read from predictions topic
docker exec kafka-broker kafka-console-consumer \
  --bootstrap-server kafka:9092 \
  --topic predictions \
  --from-beginning \
  --max-messages 5
```

---

## Key Takeaways

Congratulations! You've now learned:

✅ **What Kafka is**: A distributed message broker for real-time data streaming  
✅ **Why we use it**: Decoupling, scalability, reliability  
✅ **Event-driven architecture**: Asynchronous communication between services  
✅ **Batch processing**: Processing messages in groups for efficiency  
✅ **Producer-Consumer pattern**: Separating data generation from processing  
✅ **Monitoring**: Using Kafka UI to visualize system health  
✅ **Troubleshooting**: Common issues and how to fix them  

### Real-World Skills

You can now:
- Explain Kafka to a non-technical person
- Set up a streaming pipeline from scratch
- Debug production Kafka issues
- Make design decisions about batch sizes and scaling
- Monitor system health and performance

### Next Steps

1. **Experiment**: Try changing producer rates and batch sizes
2. **Scale**: Add more consumers and see how partitions are distributed
3. **Monitor**: Keep Kafka UI open and watch metrics
4. **Read More**: Check out Kafka's official documentation
5. **Build**: Create your own streaming application!

---

## Additional Resources

### Official Documentation
- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [Confluent Kafka Docker Images](https://docs.confluent.io/platform/current/installation/docker/image-reference.html)
- [KRaft Mode Guide](https://kafka.apache.org/documentation/#kraft)

### Video Tutorials
- Search YouTube for "Apache Kafka Tutorial for Beginners"
- Look for "Event-Driven Architecture Explained"

### Practice Projects
- Build a real-time chat application with Kafka
- Create a stock price monitoring system
- Process Twitter stream data

---

**Last Updated**: October 21, 2025  
**Maintained by**: Production ML Systems Course Team  
**Questions?** Check the troubleshooting section or ask your instructor!

Happy Streaming! 🚀

