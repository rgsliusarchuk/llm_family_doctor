#!/bin/bash
# EC2 Deployment Script for LLM Family Doctor
# This script ensures all services (API + Telegram Bot) are running in Docker

set -e

echo "🚀 Deploying LLM Family Doctor to EC2..."

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found. Please run this script from the project root."
    exit 1
fi

# Check if .env exists or create from SSM
if [ ! -f ".env" ]; then
    echo "📝 .env file not found. Checking for SSM parameters..."
    
    # Check if we're using AWS Parameter Store
    if command -v aws &> /dev/null && aws sts get-caller-identity &> /dev/null; then
        echo "🔐 Using AWS Parameter Store for environment variables..."
        chmod +x scripts/fetch_ssm_params.sh
        ./scripts/fetch_ssm_params.sh
    else
        echo "❌ Error: .env file not found and AWS CLI not configured."
        echo "💡 Please either:"
        echo "   1. Create .env file from env.template"
        echo "   2. Configure AWS CLI and store parameters in SSM"
        exit 1
    fi
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker compose down

# Pull latest changes (if using git)
if [ -d ".git" ]; then
    echo "📥 Pulling latest changes..."
    git pull origin main
fi

# Build and start all services
echo "🔨 Building and starting services..."
docker compose up -d --build

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check service status
echo "📊 Service status:"
docker compose ps

# Check health endpoints
echo "🏥 Checking API health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API server is healthy"
else
    echo "❌ API server health check failed"
fi

# Check Telegram bot logs
echo "🤖 Checking Telegram bot status..."
if docker compose logs telegram-bot | grep -q "Starting LLM Family Doctor Telegram Bot"; then
    echo "✅ Telegram bot started successfully"
else
    echo "⚠️  Telegram bot may not be running properly"
fi

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📋 Service URLs:"
echo "   • API Server: http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs"
echo "   • Health Check: http://localhost:8000/health"
echo ""
echo "🔧 Useful commands:"
echo "   • View logs: docker compose logs -f"
echo "   • Bot logs: docker compose logs -f telegram-bot"
echo "   • Stop all: docker compose down"
echo "   • Restart: docker compose restart"
echo ""
echo "📱 Telegram bot should now be responding to messages!" 