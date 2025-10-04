# E-Commerce Platform Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the e-commerce platform using Docker Swarm with microservices architecture.

## Prerequisites

### System Requirements
- **Operating System**: Ubuntu 20.04+ or CentOS 8+
- **RAM**: Minimum 8GB, Recommended 16GB+
- **CPU**: Minimum 4 cores, Recommended 8 cores+
- **Storage**: Minimum 100GB SSD
- **Network**: Stable internet connection

### Software Requirements
- Docker Engine 20.10+
- Docker Compose 2.0+
- Git
- Python 3.11+
- Node.js 16+ (for frontend)

## 1. Initial Setup

### 1.1 Install Docker and Docker Compose
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### 1.2 Initialize Docker Swarm
```bash
# Initialize swarm
docker swarm init

# Get join token for worker nodes
docker swarm join-token worker
```

## 2. Environment Configuration

### 2.1 Create Environment Files
```bash
# Create .env file
cat > .env << EOF
# Database Configuration
POSTGRES_DB=ecommerce
POSTGRES_USER=user
POSTGRES_PASSWORD=your_secure_password
DATABASE_URL=postgresql://user:your_secure_password@postgres:5432/ecommerce

# Redis Configuration
REDIS_URL=redis://redis:6379

# JWT Configuration
JWT_SECRET=your_jwt_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# Google Maps API
GOOGLE_MAPS_API_KEY=your_google_maps_api_key

# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# SMS Configuration
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=your_twilio_number

# Social Media APIs
FACEBOOK_APP_ID=your_facebook_app_id
FACEBOOK_APP_SECRET=your_facebook_app_secret
INSTAGRAM_ACCESS_TOKEN=your_instagram_token

# Payment Gateway
STRIPE_PUBLIC_KEY=your_stripe_public_key
STRIPE_SECRET_KEY=your_stripe_secret_key

# File Storage
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=password123

# Monitoring
PROMETHEUS_ENDPOINT=http://prometheus:9090
GRAFANA_ENDPOINT=http://grafana:3000
EOF
```

### 2.2 Create SSL Certificates
```bash
# Create SSL directory
mkdir -p nginx/ssl

# Generate self-signed certificate (for development)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/key.pem \
    -out nginx/ssl/cert.pem \
    -subj "/C=BD/ST=Dhaka/L=Dhaka/O=ECommerce/CN=localhost"

# For production, use Let's Encrypt or commercial certificates
```

## 3. Database Setup

### 3.1 Create Database Initialization Script
```bash
mkdir -p database
cat > database/init.sql << EOF
-- Create database if not exists
CREATE DATABASE IF NOT EXISTS ecommerce;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);

-- Create full-text search indexes
CREATE INDEX IF NOT EXISTS idx_products_search ON products USING gin(to_tsvector('english', name || ' ' || description));
EOF
```

## 4. Service Configuration

### 4.1 Create Service Directories
```bash
# Create service directories
mkdir -p services/{user-service,product-service,order-service,location-service,ai-service,marketing-service,notification-service,analytics-service,celery-worker,celery-beat}

# Create Dockerfiles for each service
for service in user-service product-service order-service location-service ai-service marketing-service notification-service analytics-service celery-worker celery-beat; do
    cat > services/$service/Dockerfile << EOF
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
done
```

### 4.2 Create Monitoring Configuration
```bash
# Create monitoring directory
mkdir -p monitoring

# Prometheus configuration
cat > monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'api-gateway'
    static_configs:
      - targets: ['api-gateway:80']

  - job_name: 'user-service'
    static_configs:
      - targets: ['user-service:8000']

  - job_name: 'product-service'
    static_configs:
      - targets: ['product-service:8000']

  - job_name: 'order-service'
    static_configs:
      - targets: ['order-service:8000']

  - job_name: 'ai-service'
    static_configs:
      - targets: ['ai-service:8000']
EOF

# Grafana dashboards
mkdir -p monitoring/grafana/dashboards
```

## 5. Deployment Process

### 5.1 Deploy to Docker Swarm
```bash
# Deploy the stack
docker stack deploy -c docker-compose.yml ecommerce

# Check service status
docker service ls

# Check service logs
docker service logs ecommerce_api-gateway
docker service logs ecommerce_user-service
docker service logs ecommerce_product-service
```

### 5.2 Scale Services
```bash
# Scale user service to 5 replicas
docker service scale ecommerce_user-service=5

# Scale product service to 3 replicas
docker service scale ecommerce_product-service=3

# Scale AI service to 2 replicas
docker service scale ecommerce_ai-service=2
```

### 5.3 Update Services
```bash
# Update a service
docker service update --image ecommerce/user-service:latest ecommerce_user-service

# Rollback a service
docker service rollback ecommerce_user-service
```

## 6. Health Checks and Monitoring

### 6.1 Health Check Endpoints
```python
# Add to each service
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/metrics")
async def metrics():
    # Return Prometheus metrics
    pass
```

### 6.2 Monitoring Setup
```bash
# Access monitoring services
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
# Jaeger: http://localhost:16686
```

## 7. Security Configuration

### 7.1 Network Security
```bash
# Create overlay network
docker network create --driver overlay --attachable ecommerce-network

# Update docker-compose.yml to use the network
```

### 7.2 SSL/TLS Configuration
```bash
# For production, use Let's Encrypt
certbot certonly --standalone -d yourdomain.com

# Update nginx configuration with real certificates
```

### 7.3 Firewall Configuration
```bash
# Configure UFW firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 2376/tcp
sudo ufw allow 2377/tcp
sudo ufw allow 7946/tcp
sudo ufw allow 7946/udp
sudo ufw allow 4789/udp
sudo ufw enable
```

## 8. Backup and Recovery

### 8.1 Database Backup
```bash
# Create backup script
cat > backup.sh << EOF
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec ecommerce_postgres pg_dump -U user ecommerce > backup_$DATE.sql
gzip backup_$DATE.sql
EOF

chmod +x backup.sh

# Schedule daily backups
echo "0 2 * * * /path/to/backup.sh" | crontab -
```

### 8.2 File Storage Backup
```bash
# Backup MinIO data
docker exec ecommerce_minio mc mirror /data /backup/$(date +%Y%m%d)
```

## 9. Performance Optimization

### 9.1 Database Optimization
```sql
-- Add indexes for better performance
CREATE INDEX CONCURRENTLY idx_products_search ON products USING gin(to_tsvector('english', name || ' ' || description));
CREATE INDEX CONCURRENTLY idx_orders_created_at ON orders(created_at);
CREATE INDEX CONCURRENTLY idx_users_created_at ON users(created_at);
```

### 9.2 Caching Strategy
```python
# Redis caching configuration
CACHE_CONFIG = {
    "default": {
        "CACHE_TYPE": "redis",
        "CACHE_REDIS_URL": "redis://redis:6379/0"
    }
}
```

### 9.3 Load Balancing
```nginx
# Nginx load balancing configuration
upstream backend {
    least_conn;
    server user-service:8000 weight=3;
    server user-service:8000 weight=3;
    server user-service:8000 weight=3;
}
```

## 10. Troubleshooting

### 10.1 Common Issues
```bash
# Check service status
docker service ls

# Check service logs
docker service logs ecommerce_user-service

# Check node status
docker node ls

# Check network
docker network ls
```

### 10.2 Performance Issues
```bash
# Check resource usage
docker stats

# Check service health
curl http://localhost/health

# Check database connections
docker exec ecommerce_postgres psql -U user -d ecommerce -c "SELECT * FROM pg_stat_activity;"
```

## 11. Production Deployment

### 11.1 Production Checklist
- [ ] SSL certificates configured
- [ ] Environment variables secured
- [ ] Database backups scheduled
- [ ] Monitoring configured
- [ ] Logging configured
- [ ] Security headers set
- [ ] Rate limiting configured
- [ ] Health checks implemented

### 11.2 CI/CD Pipeline
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build Docker images
      - name: Deploy to Docker Swarm
      - name: Run health checks
```

## 12. Maintenance

### 12.1 Regular Maintenance Tasks
```bash
# Update services
docker service update --image ecommerce/user-service:latest ecommerce_user-service

# Clean up unused images
docker image prune -f

# Clean up unused volumes
docker volume prune -f

# Update system packages
sudo apt update && sudo apt upgrade -y
```

### 12.2 Monitoring Alerts
- Set up alerts for high CPU usage
- Set up alerts for high memory usage
- Set up alerts for disk space
- Set up alerts for service failures
- Set up alerts for database connections

This deployment guide provides a comprehensive approach to deploying and maintaining the e-commerce platform using Docker Swarm with microservices architecture.
