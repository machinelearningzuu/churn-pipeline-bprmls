# Kafka Docker Logs Monitoring Guide

This guide shows you how to monitor the Kafka producer and consumer Docker logs to verify that real-time inference is working.

## Quick Commands

### 1. Check All Kafka Container Status
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "kafka-|NAMES"
```

### 2. Producer Logs (Data Streaming)
```bash
# View last 50 lines
docker logs kafka-producer --tail 50

# Follow logs in real-time
docker logs kafka-producer --follow

# View logs since 5 minutes ago
docker logs kafka-producer --since 5m
```

**What to look for:**
- `✅ Event X: Customer XXXXX` - Events being sent to Kafka
- `Successfully connected to native Kafka broker at kafka:9092` - Connection established
- Error messages if producer fails

### 3. Consumer Logs (Real-Time Inference)
```bash
# View last 50 lines
docker logs kafka-consumer --tail 50

# Follow logs in real-time
docker logs kafka-consumer --follow

# View logs since 5 minutes ago
docker logs kafka-consumer --since 5m
```

**What to look for:**
- `🔮 Prediction:` - Inference results
- `Processed batch of X events` - Batch processing stats
- Model loading messages
- S3/MLflow artifact download logs
- Error messages if inference fails

### 4. Analytics Service Logs
```bash
# View last 50 lines
docker logs kafka-analytics --tail 50

# Follow logs in real-time
docker logs kafka-analytics --follow
```

**What to look for:**
- Database insertion logs
- Aggregation statistics
- RDS connection status
- Error messages if analytics fails

### 5. Kafka Broker Logs
```bash
# View last 100 lines
docker logs kafka-broker --tail 100

# Follow logs in real-time
docker logs kafka-broker --follow
```

**What to look for:**
- Topic creation logs
- Partition assignment
- Broker health status
- Connection logs from producer/consumer

## Combined Monitoring

### Watch All Services Together
```bash
# In separate terminal windows/panes:
docker logs kafka-producer --follow
docker logs kafka-consumer --follow
docker logs kafka-analytics --follow
```

### Or use docker-compose logs:
```bash
# All Kafka services
docker-compose -f docker-compose.kafka.yml logs --follow

# Specific services
docker-compose -f docker-compose.kafka.yml logs --follow producer consumer

# Last 100 lines from all services
docker-compose -f docker-compose.kafka.yml logs --tail=100
```

## Troubleshooting

### Check if Services are Running
```bash
docker ps --filter "name=kafka-" --format "table {{.Names}}\t{{.Status}}\t{{.RunningFor}}"
```

### Check if Producer is Sending Data
```bash
docker logs kafka-producer --tail 20 | grep "✅ Event"
```

### Check if Consumer is Processing
```bash
docker logs kafka-consumer --tail 50 | grep -E "Prediction|Processed"
```

### View Error Messages Only
```bash
# Producer errors
docker logs kafka-producer 2>&1 | grep -i error

# Consumer errors
docker logs kafka-consumer 2>&1 | grep -i error

# All Kafka errors
docker ps --filter "name=kafka-" --format "{{.Names}}" | xargs -I {} sh -c 'echo "=== {} ===" && docker logs {} 2>&1 | grep -i error'
```

### Check Kafka Broker Health
```bash
# Check if broker is healthy
docker inspect kafka-broker --format='{{.State.Health.Status}}'

# Check broker logs for errors
docker logs kafka-broker --tail 100 | grep -i error
```

### View Full Logs (for debugging)
```bash
# Producer full logs
docker logs kafka-producer > producer-logs.txt

# Consumer full logs
docker logs kafka-consumer > consumer-logs.txt

# Analytics full logs
docker logs kafka-analytics > analytics-logs.txt
```

## Kafka UI (Web Interface)

Access the Kafka UI for visual monitoring:
```
http://localhost:8090
```

Features:
- Topic inspection
- Message browsing
- Consumer group monitoring
- Broker health status
- Performance metrics

## Expected Output Examples

### Healthy Producer Output:
```
✅ Event  1: Customer 15632645 | Franc | Age 42
✅ Event  2: Customer 15629752 | Germa | Age 35
✅ Event  3: Customer 15713812 | Spain | Age 44
...
```

### Healthy Consumer Output:
```
🔮 Prediction: Customer 15632645 | Churn Probability: 0.23 | Prediction: No Churn
🔮 Prediction: Customer 15629752 | Churn Probability: 0.78 | Prediction: Churn
📊 Processed batch of 10 events in 1.2 seconds
```

### Healthy Analytics Output:
```
✅ Inserted 10 predictions into RDS
📊 Current metrics - Total: 1234, Churn: 345, No Churn: 889
```

## Performance Monitoring

### Check Event Rate (Producer)
```bash
docker logs kafka-producer --tail 1000 | grep "✅ Event" | wc -l
```

### Check Processing Rate (Consumer)
```bash
docker logs kafka-consumer --tail 1000 | grep "Processed batch" | tail -5
```

### Monitor in Real-Time with Timestamps
```bash
docker logs kafka-producer --follow --timestamps | grep "Event"
docker logs kafka-consumer --follow --timestamps | grep "Prediction"
```

## Restart Services (if needed)

```bash
# Restart producer
docker restart kafka-producer

# Restart consumer
docker restart kafka-consumer

# Restart all Kafka services
docker-compose -f docker-compose.kafka.yml restart

# Stop and start (clean restart)
make kafka-down
make kafka-up
```

## Log Cleanup

Docker logs can grow large. To clean up:
```bash
# Truncate logs for a specific container
truncate -s 0 $(docker inspect --format='{{.LogPath}}' kafka-producer)

# Or restart with --log-opt max-size in docker-compose.yml
```

## Summary

The key logs to monitor for real-time inference:
1. **Producer**: Verify events are being sent to Kafka
2. **Consumer**: Verify predictions are being made
3. **Analytics**: Verify results are being stored in RDS
4. **Broker**: Verify Kafka itself is healthy

Use `docker logs <container> --follow` for live monitoring, or `--tail N` for recent logs.

