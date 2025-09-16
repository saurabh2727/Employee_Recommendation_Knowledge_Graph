# 🚀 Deployment Guide - Employee Recommendation System

This guide provides comprehensive instructions for deploying the Employee Recommendation System in various environments.

## 📋 Prerequisites

- Python 3.8+ (recommended: 3.11)
- Docker and Docker Compose (for containerized deployment)
- At least 4GB RAM and 2GB disk space
- Git (for version control)

## 🏗️ Deployment Options

### 1. 🐳 Docker Deployment (Recommended)

**Quick Start with Docker:**

```bash
# Clone the repository
git clone <your-repo-url>
cd Employee_Recommendation_Knowledge_Graph

# Build and run with Docker Compose
docker-compose up --build

# Access the application
open http://localhost:5000
```

**Production Docker Deployment:**

```bash
# Build the Docker image
docker build -t employee-recommendation:latest .

# Run the container
docker run -d \
  --name employee-recommendation \
  -p 5000:5000 \
  -e SECRET_KEY="your-production-secret-key" \
  -v $(pwd)/models:/app/models:ro \
  employee-recommendation:latest

# Check container status
docker ps
docker logs employee-recommendation
```

**With Nginx Reverse Proxy:**

```bash
# Run with nginx profile
docker-compose --profile with-nginx up -d

# Access via nginx (port 80)
open http://localhost
```

### 2. 🖥️ Local Development

**Setup Virtual Environment:**

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
python app.py
```

**Production Local Deployment:**

```bash
# Install production server
pip install gunicorn

# Run with gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 wsgi:app

# Or use the production script
python wsgi.py
```

### 3. ☁️ Cloud Deployment

#### **Heroku Deployment:**

```bash
# Install Heroku CLI and login
heroku login

# Create Heroku app
heroku create your-app-name

# Add Procfile
echo "web: gunicorn wsgi:app" > Procfile

# Deploy
git add .
git commit -m "Deploy to Heroku"
git push heroku main

# Set environment variables
heroku config:set SECRET_KEY="your-production-secret"
```

#### **AWS EC2 Deployment:**

```bash
# Launch EC2 instance (Ubuntu 20.04+)
# SSH into instance

# Install Docker
sudo apt update
sudo apt install docker.io docker-compose -y
sudo systemctl start docker
sudo systemctl enable docker

# Clone and deploy
git clone <your-repo-url>
cd Employee_Recommendation_Knowledge_Graph
sudo docker-compose up -d

# Configure security group to allow port 5000
```

#### **Google Cloud Run:**

```bash
# Install Google Cloud SDK
gcloud auth login
gcloud config set project your-project-id

# Build and deploy
gcloud run deploy employee-recommendation \
  --source . \
  --port 5000 \
  --region us-central1 \
  --allow-unauthenticated
```

#### **DigitalOcean App Platform:**

```yaml
# Create app.yaml
name: employee-recommendation
services:
- name: web
  source_dir: /
  github:
    repo: your-username/your-repo
    branch: main
  run_command: gunicorn --workers 4 --bind 0.0.0.0:8080 wsgi:app
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  routes:
  - path: /
```

### 4. 🔧 Advanced Production Setup

#### **Nginx Configuration (nginx.conf):**

```nginx
events {
    worker_connections 1024;
}

http {
    upstream app {
        server employee-recommendation:5000;
    }

    server {
        listen 80;
        server_name your-domain.com;

        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Static files
        location /static {
            alias /app/static;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

#### **Environment Configuration:**

Create `.env` file:

```bash
# Production Environment Variables
FLASK_ENV=production
SECRET_KEY=your-very-secure-secret-key-here
DATABASE_URL=your-database-url-if-needed
LOG_LEVEL=INFO
MAX_WORKERS=4
TIMEOUT=120
```

#### **Monitoring and Logging:**

```bash
# Create logs directory
mkdir -p logs

# Configure log rotation
cat > /etc/logrotate.d/employee-recommendation << EOF
/app/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 appuser appuser
}
EOF
```

## 🔧 Configuration Options

### **Environment Variables:**

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `production` |
| `SECRET_KEY` | Flask secret key | `required` |
| `PORT` | Application port | `5000` |
| `WORKERS` | Gunicorn workers | `4` |
| `TIMEOUT` | Request timeout | `120` |
| `LOG_LEVEL` | Logging level | `INFO` |

### **Performance Tuning:**

```bash
# For high-traffic deployments
gunicorn --bind 0.0.0.0:5000 \
  --workers 8 \
  --worker-class gevent \
  --worker-connections 1000 \
  --timeout 120 \
  --keepalive 5 \
  --max-requests 1000 \
  --max-requests-jitter 50 \
  wsgi:app
```

## 🔒 Security Considerations

### **Production Security Checklist:**

- [ ] Change default SECRET_KEY
- [ ] Disable Flask debug mode
- [ ] Use HTTPS in production
- [ ] Implement rate limiting
- [ ] Set up proper firewall rules
- [ ] Regular security updates
- [ ] Monitor logs for suspicious activity

### **SSL/TLS Setup:**

```bash
# Using Let's Encrypt with Certbot
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 📊 Monitoring & Health Checks

### **Health Check Endpoint:**

The application provides a health check endpoint at `/api/status`:

```bash
# Check application health
curl http://localhost:5000/api/status

# Expected response:
{
  "service": "Employee Recommendation API",
  "status": "OK",
  "model_type": "Enhanced Knowledge Graph with Semantic Embeddings",
  "employee_count": 3000
}
```

### **Docker Health Checks:**

```bash
# Check container health
docker inspect --format='{{.State.Health}}' employee-recommendation

# View health check logs
docker logs employee-recommendation
```

## 🚨 Troubleshooting

### **Common Issues:**

1. **Model not loading:**
   ```bash
   # Ensure model files exist
   ls -la models/
   # Check file permissions
   chmod 644 models/*.pkl
   ```

2. **Port already in use:**
   ```bash
   # Find process using port 5000
   lsof -i :5000
   # Kill process if needed
   kill -9 <pid>
   ```

3. **Memory issues:**
   ```bash
   # Monitor memory usage
   docker stats employee-recommendation
   # Increase container memory if needed
   ```

4. **Permission denied:**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   chmod +x wsgi.py
   ```

### **Log Analysis:**

```bash
# View application logs
docker logs -f employee-recommendation

# View nginx logs (if using)
docker logs -f <nginx-container-name>

# Check system resources
htop
df -h
```

## 🔄 Updates and Maintenance

### **Updating the Application:**

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up --build -d

# Or for rolling update
docker-compose up -d --no-deps web
```

### **Backup Strategy:**

```bash
# Backup models and data
tar -czf backup-$(date +%Y%m%d).tar.gz models/ data/

# Automated backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf "$BACKUP_DIR/app-backup-$DATE.tar.gz" models/ data/
find "$BACKUP_DIR" -name "app-backup-*.tar.gz" -mtime +7 -delete
EOF
chmod +x backup.sh
```

## 📈 Scaling

### **Horizontal Scaling:**

```yaml
# docker-compose.scale.yml
version: '3.8'
services:
  employee-recommendation:
    build: .
    deploy:
      replicas: 3
    ports:
      - "5000-5002:5000"

  load-balancer:
    image: nginx:alpine
    ports:
      - "80:80"
    depends_on:
      - employee-recommendation
```

### **Auto-scaling with Docker Swarm:**

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml employee-rec

# Scale service
docker service scale employee-rec_web=5
```

## 📞 Support

For deployment issues:

1. Check the [FAQ page](/faq) for common questions
2. Review application logs for error details
3. Verify all dependencies are installed correctly
4. Ensure adequate system resources
5. Check network connectivity and firewall settings

---

## 🎯 Quick Deploy Commands

**Local Development:**
```bash
python app.py
```

**Docker (Single Container):**
```bash
docker run -p 5000:5000 employee-recommendation
```

**Docker Compose (Full Stack):**
```bash
docker-compose up -d
```

**Production (with Gunicorn):**
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 wsgi:app
```

Choose the deployment method that best fits your infrastructure and requirements!