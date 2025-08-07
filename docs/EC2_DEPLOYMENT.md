# EC2 AWS Deployment Guide

## Overview

The LLM Family Doctor application runs as a complete system in EC2 AWS with both the API server and Telegram bot running as Docker containers.

## Architecture

```
EC2 Instance
├── Docker Compose
│   ├── familydoc (API Server) - Port 8000
│   ├── telegram-bot (Telegram Bot) - No external ports
│   ├── cache (Redis) - Internal only
│   └── reverse-proxy (Traefik) - Ports 80/443
└── Systemd Service (familydoc.service)
```

## Telegram Bot in EC2

### How it Works

1. **Containerized Service**: The Telegram bot runs as a Docker container alongside the API server
2. **Internal Communication**: The bot communicates with the API server via internal Docker network (`http://familydoc:8000`)
3. **Automatic Restart**: Both services restart automatically on failure or server reboot
4. **Health Monitoring**: The bot includes health checks to ensure it's running properly

### Key Features

- **Persistent**: Runs continuously even when you disconnect from SSH
- **Monitored**: Systemd service manages the entire stack
- **Scalable**: Easy to scale or modify without affecting other services
- **Secure**: No external ports exposed for the bot

## Deployment

### Automatic Deployment (CI/CD)

```bash
# Trigger GitHub Actions deployment
make deploy-ci
```

### Manual Deployment

```bash
# Deploy directly to EC2
make deploy-ec2
```

### Local Testing

```bash
# Test the complete stack locally
make docker-run

# Start just the Telegram bot in Docker
make start-bot-docker

# View bot logs
make logs-bot
```

## Environment Variables

Ensure these are set in your `.env` file:

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
DOCTOR_GROUP_ID=your_doctor_group_id_here

# API Configuration  
API_BASE_URL=http://familydoc:8000  # Internal Docker network

# EC2 Deployment
EC2_HOST=your-ec2-instance.com
EC2_USER=ubuntu
EC2_SSH_KEY=path/to/your/key.pem
```

## Monitoring and Logs

### View All Logs
```bash
docker compose logs -f
```

### View Telegram Bot Logs
```bash
docker compose logs -f telegram-bot
```

### Check Service Status
```bash
docker compose ps
```

### Health Checks
```bash
# API Health
curl http://localhost:8000/health

# Bot Status (check logs)
docker compose logs telegram-bot | grep "Starting"
```

## Troubleshooting

### Bot Not Responding

1. **Check if bot is running**:
   ```bash
   docker compose ps telegram-bot
   ```

2. **Check bot logs**:
   ```bash
   docker compose logs telegram-bot
   ```

3. **Verify API connection**:
   ```bash
   docker compose exec telegram-bot python -c "
   import requests
   r = requests.get('http://familydoc:8000/health')
   print(f'API Status: {r.status_code}')
   "
   ```

4. **Restart the bot**:
   ```bash
   docker compose restart telegram-bot
   ```

### Common Issues

- **Token Issues**: Ensure `TELEGRAM_BOT_TOKEN` is set correctly
- **Network Issues**: Bot can't reach API server (check Docker network)
- **Memory Issues**: Bot container running out of memory
- **Permission Issues**: Docker socket access problems

### Restart Services

```bash
# Restart everything
sudo systemctl restart familydoc

# Or restart just Docker containers
docker compose restart
```

## Security Considerations

1. **No External Ports**: Telegram bot doesn't expose any external ports
2. **Internal Network**: Bot communicates only within Docker network
3. **Environment Variables**: Sensitive data stored in `.env` file
4. **Systemd Service**: Runs with appropriate permissions

## Scaling

To scale the application:

1. **Add more API instances**: Modify `docker-compose.yml` to add more `familydoc` services
2. **Load balancing**: Use Traefik for load balancing between API instances
3. **Database scaling**: Consider external database for production
4. **Monitoring**: Add Prometheus/Grafana for metrics

## Backup and Recovery

1. **Data backup**: Backup `./data` directory and database
2. **Configuration backup**: Backup `.env` and `docker-compose.yml`
3. **Recovery**: Restore from backup and restart services

```bash
# Backup data
tar -czf backup-$(date +%Y%m%d).tar.gz data/ .env docker-compose.yml

# Restore
tar -xzf backup-YYYYMMDD.tar.gz
docker compose up -d
``` 