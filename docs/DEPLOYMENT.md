"""
Docker configuration for OpenChat
"""

# Dockerfile content (save as Dockerfile)
dockerfile_content = """
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    git \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m openchat && chown -R openchat:openchat /app
USER openchat

# Expose port
EXPOSE 12345

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import socket; socket.create_connection(('localhost', 12345), timeout=5)"

# Run server
CMD ["python", "secure_server.py", "--host", "0.0.0.0", "--port", "12345"]
"""

# docker-compose.yml content
docker_compose_content = """
version: '3.8'

services:
  openchat-server:
    build: .
    container_name: openchat-server
    ports:
      - "12345:12345"
    volumes:
      - ./openchat.db:/app/openchat.db
      - ./logs:/app/logs
    environment:
      - SERVER_HOST=0.0.0.0
      - SERVER_PORT=12345
      - DB_PATH=/app/openchat.db
      - LOG_LEVEL=INFO
    restart: unless-stopped
    networks:
      - openchat-network
    security_opt:
      - no-new-privileges:true

  postgres:
    image: postgres:15-alpine
    container_name: openchat-db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=openchat
      - POSTGRES_USER=openchat
      - POSTGRES_PASSWORD=change_me_in_production
    restart: unless-stopped
    networks:
      - openchat-network
    security_opt:
      - no-new-privileges:true

volumes:
  postgres_data:

networks:
  openchat-network:
    driver: bridge
"""

# Deployment guide
deployment_guide = """
# OpenChat Deployment Guide

## Docker Deployment

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum

### Single Container (SQLite)

```bash
# Build image
docker build -t openchat:latest .

# Run container
docker run -d \\
  --name openchat-server \\
  -p 12345:12345 \\
  -v openchat_data:/app \\
  openchat:latest
```

### Multi-Container (PostgreSQL)

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f openchat-server

# Stop services
docker-compose down
```

## Production Deployment Checklist

### Security
- [ ] Change default passwords
- [ ] Enable TLS/SSL certificates
- [ ] Use environment variables for secrets
- [ ] Enable firewall rules
- [ ] Set up API rate limiting
- [ ] Configure CORS properly
- [ ] Use reverse proxy (nginx/HAProxy)
- [ ] Enable DDoS protection (Cloudflare/AWS Shield)

### Infrastructure
- [ ] Use managed PostgreSQL (RDS/Cloud SQL/Azure DB)
- [ ] Enable automated backups
- [ ] Set up database replication
- [ ] Use CDN for static content
- [ ] Set up load balancer
- [ ] Configure health checks
- [ ] Enable autoscaling

### Monitoring & Logging
- [ ] Set up ELK/Splunk for logs
- [ ] Enable Prometheus monitoring
- [ ] Configure alerts (PagerDuty/OpsGenie)
- [ ] Set up APM (DataDog/New Relic)
- [ ] Enable distributed tracing
- [ ] Monitor database performance
- [ ] Set up error tracking (Sentry)

### Database
- [ ] Migrate from SQLite to PostgreSQL
- [ ] Configure connection pooling
- [ ] Set up read replicas
- [ ] Enable encryption at rest
- [ ] Configure backup strategy
- [ ] Monitor query performance
- [ ] Set up maintenance windows

### CI/CD
- [ ] Set up GitHub Actions/GitLab CI
- [ ] Configure automated testing
- [ ] Set up security scanning
- [ ] Enable code coverage tracking
- [ ] Configure deployment pipeline
- [ ] Set up rollback procedures
- [ ] Enable canary deployments

### Compliance
- [ ] GDPR compliance audit
- [ ] SOC 2 compliance
- [ ] Data retention policy
- [ ] User data deletion process
- [ ] Penetration testing
- [ ] Security audit
- [ ] Incident response plan

## Nginx Reverse Proxy Configuration

```nginx
upstream openchat_backend {
    server openchat-server:12345;
}

server {
    listen 80;
    server_name example.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com;
    
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
    limit_req zone=general burst=50 nodelay;
    
    location / {
        proxy_pass http://openchat_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

## Kubernetes Deployment

### Helm Chart Values

```yaml
# values.yaml
replicaCount: 3

image:
  repository: openchat
  tag: latest
  pullPolicy: IfNotPresent

service:
  type: LoadBalancer
  port: 12345

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 500m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80

database:
  host: postgres.default.svc.cluster.local
  port: 5432
  name: openchat
```

### Deploy

```bash
helm repo add openchat https://charts.openchat.dev
helm install openchat openchat/openchat -f values.yaml
```

## Monitoring Setup

### Prometheus Config

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'openchat'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: '/metrics'
```

### Grafana Dashboards

Pre-built dashboards available at:
- https://grafana.com/grafana/dashboards/openchat

## Backup Strategy

### Automated Backups

```bash
#!/bin/bash
# backup.sh
BACKUP_DIR=/backups/openchat
DATE=$(date +%Y%m%d_%H%M%S)

# PostgreSQL backup
pg_dump -h $DB_HOST -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# S3 backup
aws s3 cp $BACKUP_DIR/db_$DATE.sql.gz s3://my-backups/openchat/

# Keep only last 30 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete
```

## Scaling Strategy

### Vertical Scaling
1. Increase server CPU/RAM
2. Optimize database queries
3. Enable caching (Redis)
4. Use connection pooling

### Horizontal Scaling
1. Deploy multiple instances
2. Use load balancer
3. Share database backend
4. Enable session replication

### Database Scaling
1. Master-slave replication
2. Read replicas for queries
3. Sharding for large datasets
4. Connection pooling (PgBouncer)

## Cost Optimization

1. Use spot instances
2. Enable autoscaling
3. Right-size resources
4. Use managed services
5. Enable caching
6. Optimize storage
7. Monitor costs

## Disaster Recovery

### RTO/RPO Targets
- Recovery Time Objective (RTO): 1 hour
- Recovery Point Objective (RPO): 15 minutes

### Backup Locations
- Primary: Local storage
- Secondary: AWS S3/Azure Blob
- Tertiary: Off-site datacenter

### Restore Procedures
1. Restore database from latest backup
2. Validate data integrity
3. Start application servers
4. Run health checks
5. Monitor for issues

## Support

- Documentation: https://docs.openchat.dev
- Issues: https://github.com/openchat/openchat/issues
- Security: security@openchat.dev
"""

if __name__ == "__main__":
    print("Docker and Deployment Configuration")
    print("=" * 50)
    print("\nDocker deployment guide created.")
    print("See deployment_guide variable for full instructions.")
