#!/bin/bash
# Fetch environment variables from AWS Systems Manager Parameter Store

set -e

echo "🔐 Fetching environment variables from AWS Parameter Store..."

# Create .env file from SSM parameters
cat > .env << EOF
# OpenAI Configuration
OPENAI_API_KEY=\$(aws ssm get-parameter --name "/familydoc/openai_api_key" --with-decryption --query "Parameter.Value" --output text)
OPENAI_MODEL=gpt-4o-mini

# Model & Vector Store Configuration
MODEL_ID=intfloat/multilingual-e5-base
INDEX_PATH=data/faiss_index
MAP_PATH=data/doc_map.pkl

# LangSmith Configuration (Optional - for monitoring and debugging)
LANGSMITH_API_KEY=\$(aws ssm get-parameter --name "/familydoc/langsmith_api_key" --with-decryption --query "Parameter.Value" --output text)
LANGSMITH_PROJECT=llm-family-doctor
LANGSMITH_ENDPOINT=https://api.smith.langchain.com

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
TELEGRAM_BOT_TOKEN=\$(aws ssm get-parameter --name "/familydoc/telegram_token" --with-decryption --query "Parameter.Value" --output text)
DOCTOR_GROUP_ID=\$(aws ssm get-parameter --name "/familydoc/doctor_group_id" --query "Parameter.Value" --output text)

# AWS & ECR Configuration
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=eu-central-1
ECR_REPOSITORY=familydoc
ECR_REGISTRY=735740439208.dkr.ecr.eu-central-1.amazonaws.com

# Traefik & Domain Configuration
TRAEFIK_DOMAIN=\$(aws ssm get-parameter --name "/familydoc/traefik_domain" --query "Parameter.Value" --output text)
TAG=latest

# EC2 Deployment Configuration
EC2_HOST=18.195.119.5
EC2_USER=ubuntu
EC2_SSH_KEY=your_ssh_private_key
EOF

echo "✅ Environment variables fetched and .env file created"
echo "🔒 Sensitive values are securely stored in AWS Parameter Store" 