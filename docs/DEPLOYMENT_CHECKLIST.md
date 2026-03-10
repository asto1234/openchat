# OpenChat Deployment Checklist

Quick reference for deploying OpenChat in different environments.

## Pre-Deployment Verification

### Code Quality
- [ ] All Python files have no syntax errors
- [ ] All imports resolve correctly
- [ ] Security manager initializes without errors
- [ ] Database schema is up-to-date
- [ ] NLP models download successfully

### Dependencies
- [ ] `requirements.txt` includes all packages
- [ ] Python 3.11+ installed
- [ ] Cryptography library compatible version
- [ ] SQLite or PostgreSQL available

### Configuration
- [ ] All environment variables documented
- [ ] Default values are reasonable
- [ ] Secrets not in version control (use .gitignore)
- [ ] Configuration is externalized for containers

## Local Development Deployment

### Setup
- [ ] Clone or extract OpenChat codebase
- [ ] Create Python virtual environment: `python -m venv venv`
- [ ] Activate: `. venv/Scripts/activate` (Windows) or `source venv/bin/activate` (Unix)
- [ ] Install dependencies: `pip install -r requirements.txt`

### Configuration
- [ ] Set environment variables:
  ```bash
  export SERVER_HOST=localhost
  export SERVER_PORT=12345
  export DB_PATH=./openchat.db
  export LOG_LEVEL=DEBUG
  ```

### Start Server
- [ ] Run: `python example_k8s_deployment.py`
- [ ] Verify output: "OPENCHAT SERVER STARTUP"
- [ ] Check for errors in initialization
- [ ] Confirm listening: "Server ready at localhost:12345"

### Test Client
- [ ] In new terminal, run: `python example_client_usage.py`
- [ ] Enter test credentials
- [ ] Send test message: `/msg testuser hello`
- [ ] Verify encryption is working

### Shutdown
- [ ] Press Ctrl+C on server
- [ ] Verify graceful shutdown: "Graceful shutdown complete"
- [ ] Confirm database not corrupted: `file openchat.db`

## Docker Deployment

### Build Image
- [ ] Dockerfile exists and is updated
- [ ] `python` command uses correct interpreter in Dockerfile
- [ ] `requirements.txt` copied before code
- [ ] ENTRYPOINT set to `python example_k8s_deployment.py`
- [ ] Build: `docker build -t openchat:latest .`
- [ ] Check image: `docker images | grep openchat`

### Run Container
- [ ] Create data volume: `docker volume create openchat-data`
- [ ] Set environment variables (or use .env file)
- [ ] Run: 
  ```bash
  docker run -d \
    --name openchat-server \
    -e SERVER_HOST=0.0.0.0 \
    -e SERVER_PORT=12345 \
    -e DB_PATH=/data/openchat.db \
    -v openchat-data:/data \
    -p 12345:12345 \
    openchat:latest
  ```
- [ ] Check logs: `docker logs openchat-server`
- [ ] Verify running: `docker ps | grep openchat`

### Test Container
- [ ] Port is accessible: `telnet localhost 12345`
- [ ] Run client: `python example_client_usage.py --host localhost --port 12345`
- [ ] Send test message
- [ ] Verify database persistence (restart container and check)

### Cleanup
- [ ] Stop container: `docker stop openchat-server`
- [ ] Remove container: `docker rm openchat-server`
- [ ] Check volume: `docker volume ls | grep openchat`

## Docker Compose Deployment

### Prepare
- [ ] `docker-compose.yml` exists
- [ ] Service name is `openchat`
- [ ] Volume is defined: `openchat-data`
- [ ] Environment variables set

### Deploy
- [ ] Run: `docker-compose up -d`
- [ ] Check services: `docker-compose ps`
- [ ] View logs: `docker-compose logs -f openchat`
- [ ] Test: `telnet localhost 12345`

### Monitoring
- [ ] Setup health checks (if configured)
- [ ] Monitor resource usage: `docker stats openchat`
- [ ] Check for restarts: `docker-compose ps`

### Shutdown
- [ ] Run: `docker-compose down`
- [ ] Verify stopped: `docker-compose ps`
- [ ] Clean up volumes (if needed): `docker-compose down -v`

## Kubernetes Deployment

### Cluster Setup
- [ ] Kubernetes cluster running (1.20+)
- [ ] `kubectl` configured and authenticated
- [ ] Default storage class configured: `kubectl get storageclass`
- [ ] Sufficient resources: `kubectl describe nodes`

### Image Registry
- [ ] Tag image: `docker tag openchat:latest your-registry/openchat:latest`
- [ ] Push image: `docker push your-registry/openchat:latest`
- [ ] Verify in registry: registry console or `docker pull` from another machine
- [ ] Update image in `k8s/deployment.yaml`

### Namespace (Optional)
- [ ] Create namespace: `kubectl create namespace openchat`
- [ ] Update all manifests to use: `namespace: openchat`
- [ ] Verify: `kubectl get namespaces`

### Deploy Manifests
- [ ] Apply ConfigMap: `kubectl apply -f k8s/configmap.yaml`
  - [ ] Verify: `kubectl get configmaps`
  - [ ] Check values: `kubectl describe configmap openchat-config`

- [ ] Apply RBAC: `kubectl apply -f k8s/rbac.yaml`
  - [ ] Verify: `kubectl get serviceaccount,role,rolebinding`

- [ ] Apply Service: `kubectl apply -f k8s/service.yaml`
  - [ ] Verify: `kubectl get services`
  - [ ] Check endpoints: `kubectl get endpoints openchat-service`

- [ ] Apply Deployment: `kubectl apply -f k8s/deployment.yaml`
  - [ ] Verify: `kubectl get statefulset openchat`
  - [ ] Watch: `kubectl get pods -l app=openchat --watch`

### Verify Deployment
- [ ] All 3 pods running: `kubectl get pods`
- [ ] Pods have READY 1/1: `kubectl get pods -o wide`
- [ ] No crash loops: `kubectl describe pod openchat-0`
- [ ] PVC mounted: `kubectl get pvc openchat-pvc`
- [ ] Logs clean: `kubectl logs openchat-0`

### Test Connectivity
- [ ] Port-forward: `kubectl port-forward svc/openchat-service 12345:12345`
- [ ] Test TCP: `telnet localhost 12345`
- [ ] Check health: `curl http://localhost:12345/health`
- [ ] View metrics: `curl http://localhost:12345/metrics`
- [ ] Run client: `python example_client_usage.py --host localhost --port 12345`

### Verify Scaling
- [ ] Scale up: `kubectl scale statefulset openchat --replicas=5`
- [ ] Watch pods: `kubectl get pods --watch`
- [ ] Scale down: `kubectl scale statefulset openchat --replicas=3`

### Verify Persistence
- [ ] Send message
- [ ] Delete pod: `kubectl delete pod openchat-0`
- [ ] Pod recreates: wait for new pod to start
- [ ] Database persists: verify message data still exists

### Load Testing (Optional)
- [ ] Run multiple clients concurrently
- [ ] Monitor: `kubectl top pods`
- [ ] Check metrics: `curl http://localhost:12345/metrics`
- [ ] Verify no message loss

### Cleanup
- [ ] Delete all resources: 
  ```bash
  kubectl delete -f k8s/deployment.yaml
  kubectl delete -f k8s/service.yaml
  kubectl delete -f k8s/rbac.yaml
  kubectl delete -f k8s/configmap.yaml
  ```
- [ ] Verify deletion: `kubectl get all`

## Production Hardening

### Security
- [ ] Enable Network Policies: limit pod-to-pod communication
- [ ] Enable Pod Security Policies: enforce security standards
- [ ] Use secrets for sensitive config (future enhancement)
- [ ] Scan image for vulnerabilities: `docker scan openchat:latest`
- [ ] Enable audit logging: Kubernetes API audit

### Monitoring
- [ ] Setup Prometheus scraping (add annotations to pods)
- [ ] Configure Grafana dashboards
- [ ] Setup alerting for:
  - [ ] Pod crashes
  - [ ] High latency
  - [ ] Connection errors
  - [ ] Database errors

### Backup & Disaster Recovery
- [ ] Daily database backups
- [ ] Test restore procedure
- [ ] Document recovery steps
- [ ] Verify RTO/RPO meets requirements

### Updates & Rollouts
- [ ] Test updates in staging cluster first
- [ ] Plan rollout strategy (blue-green, canary)
- [ ] Document rollback procedure
- [ ] Have communication plan for maintenance windows

## Maintenance Checklist

### Daily
- [ ] Check pod status: `kubectl get pods`
- [ ] Review error logs
- [ ] Monitor resource usage

### Weekly
- [ ] Check metrics trends
- [ ] Review and optimize configuration
- [ ] Test disaster recovery

### Monthly
- [ ] Update dependencies
- [ ] Security audit
- [ ] Performance review
- [ ] Database optimization

### Quarterly
- [ ] Full load testing
- [ ] Capacity planning
- [ ] Architecture review
- [ ] Security scanning

## Common Issues & Resolution

| Issue | Check | Resolution |
|-------|-------|-----------|
| Pod won't start | Logs: `kubectl logs pod` | Check image, env vars, volumes |
| Connection refused | Service: `kubectl get svc` | Check service definition, endpoints |
| Database errors | Volume: `kubectl get pvc` | Check PVC, mount point, permissions |
| High latency | Metrics: `/metrics` endpoint | Check CPU/memory, network, disk I/O |
| Memory leaks | Resource: `kubectl top pods` | Check for long-lived connections |
| Pod eviction | Node: `kubectl describe node` | Increase resource limits, add nodes |

## Rollout & Rollback

### Rolling Update
```bash
# Update deployment
kubectl set image statefulset/openchat \
  openchat=your-registry/openchat:v2.0

# Watch progress
kubectl rollout status statefulset/openchat

# Monitor pods
kubectl get pods --watch
```

### Rollback
```bash
# View history
kubectl rollout history statefulset/openchat

# Rollback to previous
kubectl rollout undo statefulset/openchat

# Rollback to specific revision
kubectl rollout undo statefulset/openchat --to-revision=1
```

## Monitoring Commands Reference

```bash
# Pod status
kubectl get pods
kubectl describe pod openchat-0
kubectl logs openchat-0 -f

# Service status
kubectl get services
kubectl get endpoints openchat-service

# Resource usage
kubectl top pods openchat-0
kubectl top nodes

# Events
kubectl get events --sort-by='.lastTimestamp'

# Health checks
kubectl describe statefulset openchat | grep -A 20 "Probe"

# Persistent volumes
kubectl get pvc
kubectl get pv
```

## Backup & Recovery Commands

```bash
# Backup database
kubectl exec openchat-0 -- \
  cp /data/openchat.db /data/openchat.db.backup

# Extract backup to host
kubectl cp openchat-0:/data/openchat.db.backup ./db-backup.db

# Restore from backup
kubectl cp ./db-backup.db openchat-0:/data/openchat.db.restore

# Recreate PVC (last resort)
kubectl delete pvc openchat-pvc
kubectl delete statefulset openchat --cascade=orphan
kubectl apply -f k8s/deployment.yaml
```

## Success Criteria

- [ ] All 3 pods running and ready
- [ ] Service has endpoints and is accessible
- [ ] Client can connect and authenticate
- [ ] Messages are encrypted and persisted
- [ ] Health checks pass (liveness, readiness)
- [ ] Metrics endpoint responding
- [ ] Logs show no errors or warnings
- [ ] Graceful shutdown works (SIGTERM)
- [ ] Database survives pod restarts
- [ ] Multiple clients can connect simultaneously

## Sign-Off Checklist

Production deployment sign-off:
- [ ] All above checklist items completed
- [ ] Performance tested under load
- [ ] Security audit completed
- [ ] Backup/restore tested
- [ ] Team trained on operations
- [ ] Runbooks created
- [ ] On-call procedures established
- [ ] Monitoring and alerting configured
- [ ] Incident response plan documented
- [ ] Go-live approval received

---

**Deployment Date**: ________________
**Deployed By**: ________________
**Approved By**: ________________
**Notes**: 
