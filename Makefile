.PHONY: help install start-streamlit start-api start-bot test clean data-prep build-index

# Default target
help:
	@echo "LLM Family Doctor - Available Commands:"
	@echo ""
	@echo "📦 Setup:"
	@echo "  install        Install Python dependencies"
	@echo "  setup-env      Copy environment template and create .env"
	@echo "  local-setup    Set up local development directories"
	@echo ""
	@echo "🚀 Start Services:"
	@echo "  start-streamlit    Start Streamlit web interface"
	@echo "  start-api          Start API server"
	@echo "  start-api-debug    Start API server in DEBUG mode"
	@echo "  start-bot          Start Telegram bot (local)"
	@echo "  start-bot-docker   Start Telegram bot (Docker)"
	@echo "  stop-bot-docker    Stop Telegram bot (Docker)"
	@echo "  redis-start        Start Redis cache container"
	@echo "  redis-stop         Stop Redis cache container"
	@echo "  cache-reset        Reset ALL cache layers (Exact + Semantic + DB)"
	@echo "  semantic-reset     Reset semantic cache only"
	@echo "  semantic-clear     Clear semantic cache completely"
	@echo ""
	@echo "🐳 Docker & Deployment:"
	@echo "  docker-build   Build Docker image"
	@echo "  docker-push    Tag & push to ECR manually"
	@echo "  docker-run     Run with Docker Compose (uses DEBUG_MODE from .env)"
	@echo "  docker-test    Test Docker deployment"
	@echo "  deploy-ci      Trigger CI/CD workflow"
	@echo "  deploy-ec2     Deploy to EC2 manually"
	@echo "  logs-prod      View production logs via SSH"
	@echo ""
	@echo "📊 Data & Index:"
	@echo "  data-prep      Ingest PDF protocols to markdown"
	@echo "  build-index    Build FAISS index from protocols"
	@echo "  local-update   Update protocols and rebuild index (local workflow)"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  test           Run all tests"
	@echo "  test-index     Test vector index functionality"
	@echo "  test-cache     Test cache functionality"
	@echo "  debug-cache    Debug cache without Redis"
	@echo "  test-langchain Test LangChain integration"
	@echo "  test-smoke     Run smoke tests for CI/CD"
	@echo ""
	@echo "🗄️  Database:"
	@echo "  db-init        Create empty SQLite schema (alembic upgrade head if DB absent)"
	@echo "  db-revision    Autogenerate a new Alembic revision (use MESSAGE=\"...\")"
	@echo "  db-upgrade     Apply all pending migrations (alembic upgrade head)"
	@echo "  db-downgrade   Roll back one revision (alembic downgrade -1)"
	@echo "  db-seed        Seed demo clinic & doctor rows"
	@echo ""
	@echo "🧹 Maintenance:"
	@echo "  clean          Clean up generated files"
	@echo "  logs           View recent logs"
	@echo "  logs-bot       View Telegram bot logs"

# Setup commands
install:
	@echo "📦 Installing Python dependencies..."
	pip install -r requirements.txt

setup-env:
	@echo "🔧 Setting up environment..."
	@if [ ! -f .env ]; then \
		cp env.template .env; \
		echo "✅ Created .env from template"; \
		echo "⚠️  Please edit .env with your API keys"; \
	else \
		echo "✅ .env already exists"; \
	fi

# Start services
start-streamlit:
	@echo "🚀 Starting Streamlit app..."
	@echo "📱 Available at: http://localhost:8501"
	python start_streamlit.py

start-api:
	@echo "🚀 Starting API server..."
	@echo "🌐 Available at: http://localhost:8000"
	@echo "📚 API docs at: http://localhost:8000/docs"
	python start_api_server.py

start-api-debug:
	@echo "🐛 Starting API server in DEBUG mode..."
	@echo "🌐 Available at: http://localhost:8000"
	@echo "📚 API docs at: http://localhost:8000/docs"
	@echo "🔧 Debug port: 5678"
	DEBUG_MODE=true python -m debugpy --listen 0.0.0.0:5678 --wait-for-client api_server.py

start-bot:
	@echo "🤖 Starting Telegram bot..."
	python telegram_bot.py

start-bot-docker:
	@echo "🤖 Starting Telegram bot in Docker..."
	docker compose up telegram-bot -d

stop-bot-docker:
	@echo "🤖 Stopping Telegram bot in Docker..."
	docker compose stop telegram-bot

redis-start:
	@echo "🔴 Starting Redis cache..."
	docker run --rm -d -p 6379:6379 --name redis-cache redis:7
	@echo "✅ Redis running on localhost:6379"

redis-stop:
	@echo "🔴 Stopping Redis cache..."
	docker stop redis-cache 2>/dev/null || echo "Redis not running"

cache-reset:
	@echo "🧹 Resetting ALL cache layers (Exact + Semantic)..."
	@echo "🔴 Clearing Redis exact cache..."
	docker exec redis-cache redis-cli FLUSHALL 2>/dev/null || echo "Redis not running"
	@echo "🗄️  Clearing approved answers from database..."
	sqlite3 data/clinic.db "DELETE FROM doctor_answer WHERE approved = 1;" 2>/dev/null || echo "Database not accessible"
	@echo "🧠 Resetting semantic cache..."
	@echo "🔄 Restarting application to reload empty semantic index..."
	docker compose restart familydoc-app 2>/dev/null || echo "Docker compose not running"
	@echo "✅ ALL cache layers reset complete!"
	@echo "📊 Cache status:"
	@echo "   • Redis exact cache: EMPTY"
	@echo "   • Semantic cache: EMPTY"
	@echo "   • Database approved answers: CLEARED"

semantic-reset:
	@echo "🧠 Resetting semantic cache..."
	@echo "🔄 Restarting application to reload semantic index..."
	docker compose restart familydoc-app 2>/dev/null || echo "Docker compose not running"
	@echo "✅ Semantic cache reset complete!"

semantic-clear:
	@echo "🧠 Clearing semantic cache..."
	@echo "🗄️  Clearing approved answers from database..."
	sqlite3 data/clinic.db "DELETE FROM doctor_answer WHERE approved = 1;" 2>/dev/null || echo "Database not accessible"
	@echo "🔄 Restarting application to reload empty semantic index..."
	docker compose restart familydoc-app 2>/dev/null || echo "Docker compose not running"
	@echo "✅ Semantic cache cleared!"

semantic-stats:
	@echo "📊 Getting semantic cache statistics..."
	python scripts/reset_semantic_cache.py --stats

cache-stats:
	@echo "📊 Getting all cache statistics..."
	python scripts/reset_all_cache.py --stats

# Data preparation
data-prep:
	@echo "📊 Ingesting PDF protocols..."
	@if [ -d "data/raw_pdfs" ]; then \
		python scripts/ingest_protocol.py --dir data/raw_pdfs --recursive; \
	else \
		echo "❌ data/raw_pdfs directory not found"; \
		echo "💡 Please add PDF files to data/raw_pdfs/ first"; \
	fi

build-index:
	@echo "🔍 Building FAISS index..."
	@if [ -d "data/protocols" ]; then \
		python -c "from src.indexing.build_index import build_index; from src.config.settings import settings; build_index(settings.model_id)"; \
		echo "✅ Index built successfully"; \
	else \
		echo "❌ data/protocols directory not found"; \
		echo "💡 Please run 'make data-prep' first"; \
	fi

# Local workflow helpers
local-update:
	@echo "🔄 Updating local protocols and rebuilding index..."
	@make data-prep
	@make build-index
	@echo "✅ Local update complete!"

local-setup:
	@echo "🚀 Setting up local development environment..."
	@mkdir -p data/raw_pdfs data/protocols logs
	@echo "✅ Directories created"
	@echo "💡 Next steps:"
	@echo "   1. Add PDF files to data/raw_pdfs/"
	@echo "   2. Run 'make local-update' to process PDFs and build index"
	@echo "   3. Run 'make start-streamlit' to start the app"

# Testing
test:
	@echo "🧪 Running all tests..."
	python -m pytest tests/ -v

test-index:
	@echo "🔍 Testing vector index..."
	python tests/test_index.py

test-cache:
	@echo "🔍 Testing cache functionality..."
	python -m pytest tests/test_cache.py -v

debug-cache:
	@echo "🔍 Debugging cache functionality..."
	python tests/debug_cache.py

test-langchain:
	@echo "🔗 Testing LangChain integration..."
	python tests/test_langchain_integration.py

test-smoke:
	@echo "🧪 Running smoke tests..."
	python tests/test_smoke.py

# Maintenance
clean:
	@echo "🧹 Cleaning up generated files..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete"

logs:
	@echo "📋 Recent logs:"
	@if [ -d "logs" ]; then \
		ls -la logs/ | head -10; \
	else \
		echo "No logs directory found"; \
	fi

logs-bot:
	@echo "🤖 Telegram bot logs:"
	docker compose logs -f telegram-bot

# Development helpers
dev-setup: install setup-env
	@echo "✅ Development environment setup complete"
	@echo "💡 Next steps:"
	@echo "   1. Edit .env with your API keys"
	@echo "   2. Add PDF files to data/raw_pdfs/"
	@echo "   3. Run 'make data-prep' to process PDFs"
	@echo "   4. Run 'make start-streamlit' to start the app"

full-setup: dev-setup data-prep build-index
	@echo "✅ Full setup complete!"
	@echo "🚀 Ready to start with 'make start-streamlit'"

# -------------------------------------------------------------------------
# 🗄️  DATABASE TARGETS
# -------------------------------------------------------------------------
.PHONY: db-init db-revision db-upgrade db-downgrade db-seed

db-init:
	@echo "🗄️  Creating / upgrading SQLite schema..."
	alembic upgrade head

# Usage: make db-revision MESSAGE="add phone column"
db-revision:
	@if [ -z "$(MESSAGE)" ]; then \
		echo "❌  Please supply MESSAGE=\"your note\""; exit 1; \
	fi
	alembic revision --autogenerate -m "$(MESSAGE)"

db-upgrade:
	alembic upgrade head

db-downgrade:
	alembic downgrade -1

# Very lightweight seed script (Python one-liner)
db-seed:
	python - <<'PY' \
from sqlmodel import Session, select; from src.db import engine; from src.db.models import Clinic, Doctor; \
with Session(engine) as s: \
    if not s.exec(select(Clinic)).first(): \
        c = Clinic(address="Kyiv, Main St 10", opening_hours="Mon-Sat 08-20", services="Терапія, Педіатрія"); \
        s.add(c); \
    if not s.exec(select(Doctor)).first(): \
        d = Doctor(full_name="д-р Іван Петренко", position="Сімейний лікар", schedule="Пн-Пт 09-17"); \
        s.add(d); \
    s.commit(); \
print("✅ Demo rows inserted") \
PY

# -------------------------------------------------------------------------
# 🐳 DOCKER & DEPLOYMENT TARGETS
# -------------------------------------------------------------------------
.PHONY: docker-build docker-push docker-run deploy-ci logs-prod

# Build Docker image (accepts IMAGE arg, defaults to local)
docker-build:
	@echo "🐳 Building Docker image..."
	@if [ -z "$(IMAGE)" ]; then \
		docker build -t familydoc:dev .; \
	else \
		docker build -t $(IMAGE) .; \
	fi

# Tag and push to ECR manually
docker-push:
	@echo "🐳 Tagging and pushing to ECR..."
	@if [ -z "$(TAG)" ]; then \
		echo "❌ Please provide TAG=your_tag"; \
		exit 1; \
	fi
	@if [ -z "$(ECR_REGISTRY)" ] || [ -z "$(ECR_REPOSITORY)" ]; then \
		echo "❌ Please set ECR_REGISTRY and ECR_REPOSITORY in .env"; \
		exit 1; \
	fi
	docker tag familydoc:dev $(ECR_REGISTRY)/$(ECR_REPOSITORY):$(TAG)
	docker push $(ECR_REGISTRY)/$(ECR_REPOSITORY):$(TAG)
	@echo "✅ Pushed $(ECR_REGISTRY)/$(ECR_REPOSITORY):$(TAG)"

docker-run:
	@echo "🐳 Running with Docker Compose..."
	docker compose up

docker-run-build:
	@echo "🐳 Running with Docker Compose (rebuild)..."
	docker compose up --build

docker-test:
	@echo "🧪 Testing Docker deployment..."
	python test_deployment.py

# Trigger CI/CD workflow manually
deploy-ci:
	@echo "🚀 Triggering CI/CD deployment..."
	gh workflow run "Deploy to EC2"

# Deploy to EC2 manually
deploy-ec2:
	@echo "🚀 Deploying to EC2..."
	@if [ -z "$(EC2_HOST)" ] || [ -z "$(EC2_USER)" ] || [ -z "$(EC2_SSH_KEY)" ]; then \
		echo "❌ Please set EC2_HOST, EC2_USER, and EC2_SSH_KEY in .env"; \
		exit 1; \
	fi
	scp -i $(EC2_SSH_KEY) scripts/deploy_ec2.sh $(EC2_USER)@$(EC2_HOST):/srv/familydoc/
	ssh -i $(EC2_SSH_KEY) $(EC2_USER)@$(EC2_HOST) "cd /srv/familydoc && chmod +x deploy_ec2.sh && ./deploy_ec2.sh"

# View production logs via SSH
logs-prod:
	@echo "📋 Viewing production logs..."
	@if [ -z "$(EC2_HOST)" ] || [ -z "$(EC2_USER)" ] || [ -z "$(EC2_SSH_KEY)" ]; then \
		echo "❌ Please set EC2_HOST, EC2_USER, and EC2_SSH_KEY in .env"; \
		exit 1; \
	fi
	ssh -i $(EC2_SSH_KEY) $(EC2_USER)@$(EC2_HOST) "cd /srv/familydoc && docker compose logs -f familydoc" 