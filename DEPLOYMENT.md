# 🚀 Deployment Guide

This guide covers deploying the LLM Family Doctor application to production using Docker Compose and GitHub Actions CI/CD.

## 🏗️ Infrastructure Setup

### 1. AWS Setup

#### Create ECR Repository
```bash
aws ecr create-repository --repository-name familydoc --region us-east-1
```

#### Create EC2 Instance
- **Instance Type**: t3.medium or larger
- **OS**: Ubuntu 22.04 LTS
- **Security Groups**: 
  - SSH (port 22)
  - HTTP (port 80)
  - HTTPS (port 443)
- **IAM Role**: Attach policy with ECR access

#### Install Docker on EC2
```bash
# SSH to your EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Install Docker
sudo apt update
sudo apt install -y docker.io docker-compose

# Add user to docker group
sudo usermod -aG docker ubuntu
newgrp docker

# Start Docker service
sudo systemctl enable docker
sudo systemctl start docker
```

### 2. Application Directory Setup
```bash
# Create application directory
sudo mkdir -p /srv/familydoc
sudo chown ubuntu:ubuntu /srv/familydoc
cd /srv/familydoc

# Clone repository (for initial setup)
git clone https://github.com/your-username/llm_family_doctor.git .
```

## 🔧 Configuration

### 1. Environment Variables
```bash
# Copy environment template
cp env.template .env

# Edit .env with your production values
nano .env
```

Required environment variables:
```bash
# OpenAI Configuration
OPENAI_API_KEY=your_production_openai_key
OPENAI_MODEL=gpt-4.1-mini

# Redis Configuration
REDIS_URL=redis://cache:6379/0

# AWS & ECR Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
ECR_REPOSITORY=familydoc
ECR_REGISTRY=your_account_id.dkr.ecr.us-east-1.amazonaws.com

# Traefik & Domain Configuration
TRAEFIK_DOMAIN=your-domain.com
TAG=latest

# EC2 Deployment Configuration
EC2_HOST=your-ec2-host
EC2_USER=ubuntu
EC2_SSH_KEY=your_ssh_private_key
```

### 2. GitHub Secrets
Configure the following secrets in your GitHub repository:
- Go to Settings → Secrets and variables → Actions
- Add each secret from the table in README.md

## 🚀 Deployment

### Automatic Deployment (Recommended)
1. Push to `main` branch
2. GitHub Actions automatically:
   - Builds Docker image
   - Pushes to ECR
   - Deploys to EC2
   - Runs health checks

### Manual Deployment
```bash
# Trigger deployment manually
make deploy-ci

# Or build and push manually
make docker-build IMAGE=your-ecr-repo:tag
make docker-push TAG=your-tag
```

### Local Testing
```bash
# Test deployment locally
make docker-run

# Run smoke tests
python tests/test_smoke.py
```

## 📊 Monitoring & Maintenance

### View Logs
```bash
# Production logs
make logs-prod

# Local logs
docker compose logs -f familydoc
```

### Health Checks
```bash
# Check application health
curl http://your-domain/health

# Check Traefik dashboard
curl http://your-domain:8080
```

### Scaling
```bash
# Scale application
docker compose up -d --scale familydoc=3

# Check service status
docker compose ps
```

## 🔄 Updates

### Application Updates
- Push changes to `main` branch
- CI/CD automatically deploys updates
- No manual intervention required

### Infrastructure Updates
```bash
# Update Docker Compose
docker compose pull
docker compose up -d

# Update system packages
sudo apt update && sudo apt upgrade -y
```

## 🛠️ Troubleshooting

### Common Issues

#### Health Check Fails
```bash
# Check container status
docker compose ps

# Check application logs
docker compose logs familydoc

# Restart services
docker compose restart
```

#### ECR Login Issues
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your_account_id.dkr.ecr.us-east-1.amazonaws.com
```

#### Permission Issues
```bash
# Fix file permissions
sudo chown -R ubuntu:ubuntu /srv/familydoc
chmod 600 .env
```

### Debug Commands
```bash
# Check Docker status
docker system df
docker ps -a

# Check network connectivity
docker network ls
docker network inspect familydoc_web

# Check volume mounts
docker volume ls
docker volume inspect familydoc_redis_data
```

## 🔒 Security

### Best Practices
- Use IAM roles instead of access keys when possible
- Regularly rotate SSH keys and API keys
- Keep system packages updated
- Monitor logs for suspicious activity
- Use HTTPS in production

### SSL/TLS Setup
```bash
# For production, configure SSL certificates
# Add to Traefik configuration in docker-compose.yml
```

## 📈 Performance

### Optimization Tips
- Use appropriate EC2 instance size
- Monitor memory and CPU usage
- Configure Redis persistence
- Use CDN for static assets
- Implement caching strategies

### Monitoring
- Set up CloudWatch alarms
- Monitor application metrics
- Track API response times
- Monitor error rates 