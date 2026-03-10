# OpenChat Clean Server Interface & Client Architecture Documentation

## Overview

This document describes the clean server interface and client architecture designed for production deployment on Docker and Kubernetes. These new components modernize the OpenChat deployment while maintaining full compatibility with the existing encryption, database, and NLP modules.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Server Interface](#server-interface)
3. [Client Architecture](#client-architecture)
4. [Integration Guide](#integration-guide)
5. [Deployment Options](#deployment-options)
6. [Configuration](#configuration)
7. [Monitoring & Health Checks](#monitoring--health-checks)
8. [Examples](#examples)
9. [Troubleshooting](#troubleshooting)

## Architecture Overview

### Conceptual Model

```
┌──────────────────────────────────────┐
│      OpenChat Deployment Model       │
├──────────────────────────────────────┤
│                                      │
│  Client Layer                        │
│  ├─ ServiceDiscovery                │
│  ├─ ClientConnection (with retries) │
│  ├─ CleanChatClient (high-level API)│
│  └─ ClientPool (load distribution)  │
│                                      │
│  ↕ JSON Protocol (async sockets)   │
│                                      │
│  Server Layer                        │
│  ├─ ServerConfig (env-based)        │
│  ├─ HealthChecker (K8s probes)      │
│  ├─ ServerMetrics (monitoring)      │
│  └─ CleanServerInterface (core)     │
│                                      │
│  ↓                                    │
│                                      │
│  Integration Layer                   │
│  ├─ SecurityManager (E2E encryption) │
│  ├─ DatabaseManager (persistent)     │
│  └─ NLPSummarizer (optional)         │
│                                      │
└──────────────────────────────────────┘
```

### Key Design Principles

1. **Cloud-Native**: Configuration via environment variables, health checks for orchestration
2. **Container-Friendly**: No hardcoded paths, graceful shutdown, structured logging
3. **Kubernetes-Ready**: Service discovery, anti-affinity, resource limits, RBAC
4. **Resilient**: Automatic retry logic, exponential backoff, health tracking
5. **Observable**: Metrics endpoint, health checks, structured logging
6. **Compatible**: Works with existing encryption, database, and NLP modules

## Server Interface

### ServerConfig Class

Reads all configuration from environment variables (injected by Kubernetes ConfigMap).

```python
from server_interface import ServerConfig

config = ServerConfig()

# Attributes:
# config.host              # '0.0.0.0' (listening address)
# config.port              # 12345 (listening port)
# config.db_path           # '/data/openchat.db' (database path)
# config.max_connections   # 1000 (max concurrent connections)
# config.log_level         # 'INFO' (logging level)
# config.replica_id        # 'replica-0' (unique pod identifier)
# config.enable_metrics    # True (metrics endpoint)
# config.enable_health_check # True (health checks)
```

### ServerMetrics Class

Tracks operational metrics for monitoring and troubleshooting.

```python
from server_interface import ServerMetrics

metrics = ServerMetrics()

# Tracked Metrics:
# - uptime: Server running time
# - connections_total: Total connection attempts
# - connections_active: Current active connections
# - messages_processed: Total messages handled
# - key_exchanges: Cryptographic key exchanges
# - authentication_attempts: Auth attempts (success + failure)
# - bytes_sent: Total bytes transmitted
# - bytes_received: Total bytes received

# Access via HTTP
# GET /metrics → JSON metrics object
```

### HealthChecker Class

Implements Kubernetes health check protocols.

```python
from server_interface import HealthChecker

checker = HealthChecker()

# Check Types:
# 1. Liveness: Is server running? (TCP connect)
# 2. Readiness: Can server handle traffic? (HTTP /health)
# 3. Startup: Has server initialized? (TCP connect with timeout)

# HTTP Endpoints:
# GET /health          → {"status": "healthy", "timestamp": "..."}
# GET /ready           → {"status": "ready", "timestamp": "..."}
# GET /metrics         → {...metrics...}
```

### CleanServerInterface Class

Main server implementation with lifecycle management.

```python
from server_interface import CleanServerInterface

server = CleanServerInterface(
    host='0.0.0.0',
    port=12345,
    db_path='/data/openchat.db',
    max_connections=1000,
    security_manager=security,      # From encryption.py
    database_manager=database,        # From database.py
    nlp_summarizer=nlp                # From nlp_summarizer.py
)

# Lifecycle:
# server.run()          → Start async server (handles SIGTERM/SIGINT)

# Features:
# - Async connection handling
# - Protocol implementation (JSON framing)
# - Graceful shutdown on termination signals
# - Connection tracking and cleanup
# - Health check endpoints
# - Metrics collection
```

## Client Architecture

### ServiceDiscovery Class

Handles connection endpoint management with multiple discovery modes.

```python
from client_architecture import ServiceDiscovery, ConnectionMode

# Kubernetes service discovery (automatic)
discovery = ServiceDiscovery.from_kubernetes_env()

# Direct connection
discovery = ServiceDiscovery.from_direct_config('localhost', 12345)

# Multi-endpoint with custom configuration
discovery = ServiceDiscovery(mode=ConnectionMode.DNS_DISCOVERY)
discovery.add_endpoint(ServerEndpoint(host='openchat-0', port=12345))
discovery.add_endpoint(ServerEndpoint(host='openchat-1', port=12345))

# Methods:
endpoint = discovery.get_next_endpoint()         # Round-robin selection
discovery.mark_endpoint_healthy(endpoint)        # Update health status
discovery.mark_endpoint_unhealthy(endpoint)      # Mark failed
```

### ClientConnection Class

Low-level connection management with retry logic.

```python
from client_architecture import ClientConnection

conn = ClientConnection(
    host='localhost',
    port=12345,
    timeout=10.0,
    max_retries=3,
    initial_backoff=1.0
)

# Lifecycle:
await conn.connect()                  # Connect with retries
await conn.send_message(data)         # Send JSON message
data = await conn.receive_message()   # Receive JSON message
await conn.disconnect()               # Graceful shutdown

# Features:
# - Automatic retry with exponential backoff
# - Connection timeout handling
# - Heartbeat/keep-alive
# - Clean disconnection
```

### CleanChatClient Class

High-level API for chat operations.

```python
from client_architecture import CleanChatClient

client = CleanChatClient(
    discovery=service_discovery,
    logger=logger
)

# Lifecycle:
await client.connect()                            # Connect to server
await client.authenticate('username', 'password')  # Authenticate
await client.send_message('recipient', 'Hello!')  # Send message
msg = await client.receive_message()              # Receive message
await client.disconnect()                         # Disconnect
```

### ClientPool Class

Connection pooling for multi-client scenarios.

```python
from client_architecture import ClientPool

pool = ClientPool(
    discovery=service_discovery,
    pool_size=10
)

# Usage:
async with pool.get_connection() as client:
    await client.send_message('user', 'Hello!')
```

## Integration Guide

### Step 1: Import Required Modules

```python
# Clean interfaces
from server_interface import CleanServerInterface, ServerConfig
from client_architecture import ServiceDiscovery, CleanChatClient

# Existing modules
from encryption import SecurityManager
from database import DatabaseManager
from nlp_summarizer import NLPSummarizer
```

### Step 2: Initialize Components

```python
# Load configuration
config = ServerConfig()

# Initialize security (E2E encryption)
security = SecurityManager()

# Initialize database
database = DatabaseManager(config.db_path)
database.initialize()

# Initialize NLP (optional)
try:
    nlp = NLPSummarizer()
except Exception:
    nlp = None  # Continue without NLP
```

### Step 3: Create Server

```python
server = CleanServerInterface(
    host=config.host,
    port=config.port,
    db_path=config.db_path,
    max_connections=config.max_connections,
    security_manager=security,
    database_manager=database,
    nlp_summarizer=nlp
)

# Start server
await server.run()
```

### Step 4: Create Client

```python
# Discover server (Kubernetes or direct)
discovery = ServiceDiscovery.from_kubernetes_env()

# Create client
client = CleanChatClient(discovery=discovery)

# Connect and authenticate
await client.connect()
await client.authenticate('alice', 'password123')

# Use client
await client.send_message('bob', 'Hello Bob!')
```

### Complete Example

See [example_k8s_deployment.py](example_k8s_deployment.py) for server integration.
See [example_client_usage.py](example_client_usage.py) for client integration.

## Deployment Options

### Option 1: Local Development

```bash
# Set environment variables
export SERVER_HOST=localhost
export SERVER_PORT=12345
export DB_PATH=./openchat.db

# Run server
python example_k8s_deployment.py

# In another terminal, run client
python example_client_usage.py --host localhost --port 12345
```

### Option 2: Docker Container

```bash
# Build image
docker build -t openchat:latest .

# Run container
docker run -it \
  -e SERVER_HOST=0.0.0.0 \
  -e SERVER_PORT=12345 \
  -e DB_PATH=/data/openchat.db \
  -v openchat-data:/data \
  -p 12345:12345 \
  openchat:latest

# Run client (from host)
python example_client_usage.py --host localhost --port 12345
```

### Option 3: Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f openchat

# Stop services
docker-compose down
```

### Option 4: Kubernetes

```bash
# Deploy to cluster
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/deployment.yaml

# Wait for deployment
kubectl wait --for=condition=Ready pod -l app=openchat --timeout=300s

# Port-forward for testing
kubectl port-forward svc/openchat-service 12345:12345

# Run client
python example_client_usage.py --host localhost --port 12345

# View logs
kubectl logs -f openchat-0
```

See [K8S_GUIDE.md](K8S_GUIDE.md) for complete Kubernetes deployment guide.

## Configuration

### Environment Variables

| Variable | Default | Kubernetes | Description |
|----------|---------|-----------|-------------|
| `SERVER_HOST` | `0.0.0.0` | ConfigMap | Server listening address |
| `SERVER_PORT` | `12345` | ConfigMap | Server listening port |
| `DB_PATH` | `openchat.db` | ConfigMap | Database file path |
| `MAX_CONNECTIONS` | `1000` | ConfigMap | Maximum concurrent connections |
| `LOG_LEVEL` | `INFO` | ConfigMap | Logging level |
| `ENVIRONMENT` | `production` | ConfigMap | Environment name |
| `ENABLE_METRICS` | `true` | ConfigMap | Enable metrics endpoint |
| `ENABLE_HEALTH_CHECK` | `true` | ConfigMap | Enable health checks |
| `REPLICA_ID` | `default` | StatefulSet | Pod replica identifier |
| `POD_NAME` | `localhost` | StatefulSet | Kubernetes pod name |
| `POD_NAMESPACE` | `default` | StatefulSet | Kubernetes namespace |

### Kubernetes ConfigMap

Edit `k8s/configmap.yaml` to change configuration:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: openchat-config
data:
  SERVER_HOST: "0.0.0.0"
  SERVER_PORT: "12345"
  DB_PATH: "/data/openchat.db"
  # ... other variables ...
```

Apply changes:
```bash
kubectl apply -f k8s/configmap.yaml
kubectl rollout restart statefulset/openchat
```

## Monitoring & Health Checks

### Health Check Endpoints

```bash
# Liveness (is server running?)
curl -v telnet://localhost:12345

# Readiness (can server accept traffic?)
curl http://localhost:12345/health

# Metrics (operational metrics)
curl http://localhost:12345/metrics
```

### Kubernetes Health Probes

Configured in `k8s/deployment.yaml`:

```yaml
# Liveness Probe: Restart if no response
livenessProbe:
  tcpSocket:
    port: 12345
  initialDelaySeconds: 30
  periodSeconds: 10

# Readiness Probe: Remove from load balancer if not ready
readinessProbe:
  httpGet:
    path: /health
    port: 12345
  initialDelaySeconds: 10
  periodSeconds: 5

# Startup Probe: Allow time for initialization
startupProbe:
  tcpSocket:
    port: 12345
  initialDelaySeconds: 0
  periodSeconds: 5
  failureThreshold: 60  # Up to 5 minutes
```

### Metrics Format

```json
{
  "uptime_seconds": 3600.5,
  "connections_total": 150,
  "connections_active": 5,
  "messages_processed": 1250,
  "key_exchanges": 150,
  "authentication_attempts": 160,
  "authentication_successes": 150,
  "bytes_sent": 1024000,
  "bytes_received": 512000,
  "timestamp": "2024-01-15T10:30:45Z"
}
```

### Prometheus Integration

Add to pod annotations for Prometheus scraping:

```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "12345"
  prometheus.io/path: "/metrics"
```

## Examples

### Example 1: Start Server with All Components

```bash
cd openchat/
python example_k8s_deployment.py
```

This example:
- Loads configuration from environment
- Initializes security manager
- Sets up database
- Loads NLP module
- Starts clean server interface
- Handles signals for graceful shutdown

### Example 2: Interactive Client Chat

```bash
python example_client_usage.py
```

Features:
- Automatic service discovery (or direct connection)
- User authentication
- Message sending (`/msg recipient message`)
- Message listening (`/listen`)
- Connection status checking (`/status`)
- Interactive command interface

### Example 3: Multi-Endpoint Load Balancing

```python
from client_architecture import ServiceDiscovery, ServerEndpoint

# Configure multiple endpoints
discovery = ServiceDiscovery()
discovery.add_endpoint(ServerEndpoint('openchat-0.example.com', 12345))
discovery.add_endpoint(ServerEndpoint('openchat-1.example.com', 12345))
discovery.add_endpoint(ServerEndpoint('openchat-2.example.com', 12345))

# Client automatically round-robins
client = CleanChatClient(discovery=discovery)
await client.connect()  # Connects to first healthy endpoint
```

### Example 4: Kubernetes Deployment

```bash
# Deploy complete stack
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/deployment.yaml

# Watch deployment
kubectl get statefulset openchat -w

# Test with port-forward
kubectl port-forward svc/openchat-service 12345:12345
python example_client_usage.py --host localhost --port 12345
```

## Troubleshooting

### Server Won't Start

**Symptom**: Server exits immediately

**Solution**:
```bash
# Check for required modules
python -c "from encryption import SecurityManager; print('OK')"

# Check environment variables
echo $SERVER_HOST $SERVER_PORT $DB_PATH

# Run with verbose logging
LOG_LEVEL=DEBUG python example_k8s_deployment.py
```

### Client Can't Connect

**Symptom**: Connection timeout or refused

**Solution**:
```bash
# Check if server is running
netstat -an | grep 12345

# Test network connectivity
telnet localhost 12345

# Check service discovery
python -c "from client_architecture import ServiceDiscovery; sd = ServiceDiscovery.from_kubernetes_env(); print(sd.endpoints)"
```

### Kubernetes Pods Not Ready

**Symptom**: Pods in `CrashLoopBackOff` or `Pending` state

**Solution**:
```bash
# Check pod events
kubectl describe pod openchat-0

# Check pod logs
kubectl logs openchat-0
kubectl logs openchat-0 -c init-db

# Check service endpoints
kubectl get endpoints openchat-service

# Check persistent volume
kubectl get pvc openchat-pvc
kubectl get pv
```

### Database Corruption

**Symptom**: Database errors in logs

**Solution**:
```bash
# Backup current database
kubectl exec openchat-0 -- cp /data/openchat.db /data/openchat.db.backup

# Delete PVC to reinitialize
kubectl delete pvc openchat-pvc
kubectl apply -f k8s/deployment.yaml
```

### Memory or CPU Issues

**Symptom**: Pods OOMKilled or throttled

**Solution**:
```bash
# Check resource usage
kubectl top pods openchat-0
kubectl top nodes

# Edit limits in k8s/deployment.yaml
# Increase resources:
resources:
  limits:
    memory: "2Gi"      # Increase from 1Gi
    cpu: "2000m"       # Increase from 1000m

kubectl apply -f k8s/deployment.yaml
```

## Advanced Topics

### Custom Protocol Handlers

Extend `CleanServerInterface` to add custom message handlers:

```python
class CustomServerInterface(CleanServerInterface):
    async def handle_custom_message(self, client_addr, message):
        # Custom message processing
        pass
```

### Service Mesh Integration (Istio)

Add Istio sidecar injection:

```yaml
metadata:
  annotations:
    sidecar.istio.io/inject: "true"
```

### Multi-Cluster Deployment

Use external load balancer or Kubernetes Federation to distribute across clusters.

### Persistent Backups

```bash
# Daily backup job
kubectl create cronjob openchat-backup \
  --image=busybox \
  --schedule="0 2 * * *" \
  -- /bin/sh -c "kubectl cp default/openchat-0:/data/openchat.db ./backup.db"
```

## Related Documentation

- [K8S_GUIDE.md](K8S_GUIDE.md) - Complete Kubernetes deployment guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - Overall system architecture
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment strategies
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide

## Support

For issues or questions:
1. Check logs: `kubectl logs -f openchat-0`
2. Review configuration: `kubectl describe configmap openchat-config`
3. Test connectivity: `telnet localhost 12345`
4. Check metrics: `curl http://localhost:12345/metrics`
