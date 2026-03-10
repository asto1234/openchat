# Kubernetes Deployment Guide for OpenChat

This guide explains how to deploy OpenChat on a Kubernetes cluster using the clean server interface and cloud-native architecture.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         OpenChat LoadBalancer Service (External)     │  │
│  │         openchat-service:12345 (NodePort 30001)      │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                      │
│  ┌────────────────────┴──────────────────────────────────┐  │
│  │    OpenChat ClusterIP Service (Internal DNS)         │  │
│  │    openchat-service-internal:12345                   │  │
│  └────────────────────┬──────────────────────────────────┘  │
│                       │                                      │
│  ┌────────────────────┴──────────────────────────────────┐  │
│  │         OpenChat Deployment (3 Replicas)             │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │  Pod 1 (openchat-0)     | Pod 2 (openchat-1)         │  │
│  │  ┌───────────────────┐  │ ┌───────────────────┐      │  │
│  │  │ Init Container    │  │ │ Init Container    │      │  │
│  │  │ (DB init)         │  │ │ (DB init)         │      │  │
│  │  └───────────────────┘  │ └───────────────────┘      │  │
│  │  ┌───────────────────┐  │ ┌───────────────────┐      │  │
│  │  │ OpenChat Server   │  │ │ OpenChat Server   │      │  │
│  │  │ (server_interface)│  │ │ (server_interface)│      │  │
│  │  └───────────────────┘  │ └───────────────────┘      │  │
│  │  ┌───────────────────┐  │ ┌───────────────────┐      │  │
│  │  │ Encryption Module │  │ │ Encryption Module │      │  │
│  │  │ Database Layer    │  │ │ Database Layer    │      │  │
│  │  │ NLP Summarizer    │  │ │ NLP Summarizer    │      │  │
│  │  └───────────────────┘  │ └───────────────────┘      │  │
│  │          │               │           │                │  │
│  │          └─── PVC Volume (Shared Database) ──────────┘  │
│  │                   openchat-pvc (10Gi)                   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                               │
│  ConfigMap (Environment Configuration)                       │
│  - SERVER_HOST, SERVER_PORT                                  │
│  - DB_PATH, MAX_CONNECTIONS                                  │
│  - LOG_LEVEL, ENABLE_METRICS, ENABLE_HEALTH_CHECK            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **Kubernetes Cluster** (1.20+)
   - kubectl configured and connected
   - At least 3 nodes for pod anti-affinity (recommended)
   - Storage class for PersistentVolumeClaim

2. **Required Software**
   ```bash
   kubectl version --client
   helm version  # optional, for advanced deployments
   ```

3. **OpenChat Source Code**
   - All Python modules: encryption.py, database.py, nlp_summarizer.py, etc.
   - Docker image built: `your-registry/openchat:latest`

## File Structure

```
k8s/
  ├── configmap.yaml       # Environment configuration
  ├── service.yaml         # LoadBalancer and ClusterIP services
  ├── deployment.yaml      # StatefulSet deployment with 3 replicas
  └── rbac.yaml           # ServiceAccount and RBAC roles
```

## Step-by-Step Deployment

### 1. Build Docker Image

```bash
# From OpenChat root directory
docker build -t your-registry/openchat:latest .

# Push to registry
docker push your-registry/openchat:latest
```

Update the image in `deployment.yaml`:
```yaml
spec:
  containers:
  - name: openchat
    image: your-registry/openchat:latest  # Update this
```

### 2. Create Namespace (Optional)

```bash
kubectl create namespace openchat
```

Update manifests to use this namespace:
```bash
sed -i 's/namespace: default/namespace: openchat/g' k8s/*.yaml
```

### 3. Deploy ConfigMap

```bash
kubectl apply -f k8s/configmap.yaml
```

Verify:
```bash
kubectl get configmaps
kubectl describe configmap openchat-config
```

### 4. Deploy RBAC

```bash
kubectl apply -f k8s/rbac.yaml
```

Verify:
```bash
kubectl get serviceaccount openchat-sa
kubectl get role openchat-role
```

### 5. Deploy Service

```bash
kubectl apply -f k8s/service.yaml
```

Verify:
```bash
kubectl get services
kubectl describe service openchat-service
```

Get external IP (may take a few moments):
```bash
kubectl get svc openchat-service --watch
```

### 6. Deploy Application

```bash
kubectl apply -f k8s/deployment.yaml
```

Verify:
```bash
kubectl get pods
kubectl get statefulset openchat
kubectl logs -f openchat-0  # Follow logs of first pod
```

## Configuration

### Environment Variables (ConfigMap)

Edit `k8s/configmap.yaml` to customize:

| Variable | Default | Purpose |
|----------|---------|---------|
| `SERVER_HOST` | `0.0.0.0` | Server listening address |
| `SERVER_PORT` | `12345` | Server listening port |
| `DB_PATH` | `/data/openchat.db` | Database file path (PVC mount) |
| `MAX_CONNECTIONS` | `1000` | Maximum concurrent connections |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `ENVIRONMENT` | `production` | Environment name |
| `ENABLE_METRICS` | `true` | Enable metrics endpoint |
| `ENABLE_HEALTH_CHECK` | `true` | Enable health check endpoints |

### Scaling

Increase replicas:
```bash
kubectl scale statefulset openchat --replicas=5
```

Or edit deployment.yaml:
```yaml
spec:
  replicas: 5  # Change this number
```

### Resource Limits

Edit in `deployment.yaml`:
```yaml
resources:
  requests:
    memory: "512Mi"      # Minimum guaranteed
    cpu: "250m"          # Minimum guaranteed
  limits:
    memory: "1Gi"        # Maximum allowed
    cpu: "1000m"         # Maximum allowed
```

## Health Checks & Monitoring

### Kubernetes Health Probes

The deployment includes three health check types:

1. **Liveness Probe** (every 10s after 30s)
   - Restarts pod if server is not responding
   - Connects to TCP:12345

2. **Readiness Probe** (every 5s after 10s)
   - Removes pod from load balancer if not ready
   - Checks HTTP /health endpoint

3. **Startup Probe** (every 5s for up to 5 minutes)
   - Gives slow-starting pods time to initialize
   - Checks TCP:12345

### View Health Status

```bash
kubectl get pods -o wide
kubectl describe pod openchat-0
kubectl logs openchat-0 --previous  # If pod crashed
```

### Metrics Endpoint

Access metrics (requires port-forward):
```bash
kubectl port-forward svc/openchat-service 12345:12345
curl http://localhost:12345/metrics
```

Metrics include:
- Uptime
- Active connections
- Messages processed
- Key exchanges
- Authentication attempts

## Connection & Testing

### Port Forwarding (Local Access)

```bash
# Access externally exposed service
kubectl port-forward svc/openchat-service 12345:12345

# In another terminal, test with client
python client_architecture.py
```

### Direct ClusterIP (Internal)

From within cluster (in a pod):
```python
# Client uses Kubernetes DNS
from client_architecture import ServiceDiscovery, CleanChatClient

discovery = ServiceDiscovery.from_kubernetes_env()
client = CleanChatClient(discovery)
```

### LoadBalancer IP (External)

```bash
kubectl get svc openchat-service
# Use the EXTERNAL-IP returned
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod openchat-0
kubectl logs openchat-0

# Check init container logs
kubectl logs openchat-0 -c init-db
```

### CrashLoopBackOff

```bash
# View crash logs
kubectl logs openchat-0 --previous

# Common issues:
# 1. Database volume not mounted
# 2. Port already in use
# 3. Missing dependencies in image
```

### Connection Issues

```bash
# Test internal connectivity
kubectl run -it --rm debug --image=ubuntu --restart=Never -- bash
apt-get update && apt-get install -y netcat
nc -zv openchat-service-internal 12345

# Check service endpoints
kubectl get endpoints openchat-service
```

### Performance Issues

```bash
# Check resource usage
kubectl top pods openchat-0
kubectl top nodes

# Check event logs
kubectl get events --sort-by='.lastTimestamp'
```

## Upgrading

### Rolling Update

```bash
# Update image in deployment.yaml then:
kubectl apply -f k8s/deployment.yaml

# Monitor rollout
kubectl rollout status statefulset/openchat
```

### Rollback

```bash
kubectl rollout undo statefulset/openchat
kubectl rollout history statefulset/openchat
```

## Cleanup

Remove all OpenChat resources:

```bash
kubectl delete -f k8s/deployment.yaml
kubectl delete -f k8s/service.yaml
kubectl delete -f k8s/rbac.yaml
kubectl delete -f k8s/configmap.yaml

# Or delete entire namespace
kubectl delete namespace openchat
```

## Advanced Patterns

### Service Mesh Integration (Istio)

```yaml
# Add to deployment.yaml metadata
labels:
  version: v1
annotations:
  sidecar.istio.io/inject: "true"
```

### Horizontal Pod Autoscaling

```bash
kubectl autoscale statefulset openchat --min=2 --max=10 --cpu-percent=80
```

### Multi-Cluster Setup

Use Kubernetes Federation v2 or external load balancer to distribute traffic across clusters.

### Persistent Backups

```bash
# Backup database from PVC
kubectl exec -it openchat-0 -- tar czf /tmp/db-backup.tar.gz /data/
kubectl cp openchat-0:/tmp/db-backup.tar.gz ./db-backup.tar.gz
```

## Security Considerations

1. **Network Policies**: Restrict traffic between pods
2. **Pod Security Policies**: Enforce security standards
3. **Secret Management**: Use Kubernetes Secrets for credentials
4. **RBAC**: Current setup has minimal permissions
5. **Image Scanning**: Scan Docker image for vulnerabilities
6. **Audit Logging**: Enable Kubernetes audit logs

## Monitoring & Logging

### Prometheus Integration

```yaml
# Add to pod annotations
prometheus.io/scrape: "true"
prometheus.io/port: "12345"
prometheus.io/path: "/metrics"
```

### Log Aggregation (ELK Stack)

Configure OpenChat logging to JSON format and stream to ElasticSearch.

### OpenTelemetry (Distributed Tracing)

Integrate with Jaeger for request tracing across pods.

## References

- [Kubernetes StatefulSet Documentation](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)
- [Pod Anti-Affinity Guide](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/)
- [Health Probe Best Practices](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
