#!/bin/bash
# Fetch environment variables from AWS Systems Manager Parameter Store

set -e

echo "🔐 Fetching environment variables from AWS Parameter Store..."

# Create .env file from SSM parameters
cat > .env << EOF
# OpenAI Configuration
OPENAI_API_KEY=$(aws ssm get-parameter --name "/familydoc/openai_api_key" --with-decryption --query "Parameter.Value" --output text)
OPENAI_MODEL=gpt-4o-mini

# Model & Vector Store Configuration
MODEL_ID=intfloat/multilingual-e5-base
INDEX_PATH=data/faiss_index
MAP_PATH=data/doc_map.pkl

# Database Configuration
DATABASE_URL=sqlite:///data/clinic.db

# Redis Configuration
REDIS_URL=redis://cache:6379/0
REDIS_TTL_DAYS=30

# API Configuration
API_BASE_URL=http://familydoc:8000
API_BASE=http://familydoc

# Debug Configuration
DEBUG_MODE=false

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=$(aws ssm get-parameter --name "/familydoc/telegram_token" --with-decryption --query "Parameter.Value" --output text)
DOCTOR_GROUP_ID=$(aws ssm get-parameter --name "/familydoc/doctor_group_id" --query "Parameter.Value" --output text)

# AWS & ECR Configuration
AWS_ACCESS_KEY_ID=$(aws ssm get-parameter --name "/familydoc/aws_access_key_id" --with-decryption --query "Parameter.Value" --output text)
AWS_SECRET_ACCESS_KEY=$(aws ssm get-parameter --name "/familydoc/aws_secret_access_key" --with-decryption --query "Parameter.Value" --output text)
AWS_REGION=$(aws ssm get-parameter --name "/familydoc/aws_region" --query "Parameter.Value" --output text)

# Traefik & Domain Configuration
TRAEFIK_DOMAIN=$(aws ssm get-parameter --name "/familydoc/traefik_domain" --query "Parameter.Value" --output text)
TAG=latest
EOF

echo "✅ Environment variables fetched and .env file created"
echo "🔒 Sensitive values are securely stored in AWS Parameter Store" 