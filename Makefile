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
	@echo "  start-bot          Start Telegram bot"
	@echo "  redis-start        Start Redis cache container"
	@echo "  redis-stop         Stop Redis cache container"
	@echo ""
	@echo "🐳 Docker & Deployment:"
	@echo "  docker-build   Build Docker image"
	@echo "  docker-run     Run with Docker Compose"
	@echo "  docker-test    Test Docker deployment"
	@echo "  deploy-prod    Deploy to production via GitHub Actions"
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

start-bot:
	@echo "🤖 Starting Telegram bot..."
	python telegram_bot_example.py

redis-start:
	@echo "🔴 Starting Redis cache..."
	docker run --rm -d -p 6379:6379 --name redis-cache redis:7
	@echo "✅ Redis running on localhost:6379"

redis-stop:
	@echo "🔴 Stopping Redis cache..."
	docker stop redis-cache 2>/dev/null || echo "Redis not running"

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
.PHONY: docker-build docker-run deploy-prod

docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t familydoc:dev .

docker-run:
	@echo "🐳 Running with Docker Compose..."
	docker compose up

docker-run-build:
	@echo "🐳 Running with Docker Compose (rebuild)..."
	docker compose up --build

docker-test:
	@echo "🧪 Testing Docker deployment..."
	python test_deployment.py

deploy-prod:
	@echo "🚀 Triggering production deployment..."
	gh workflow run deploy.yml 