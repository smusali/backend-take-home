.PHONY: env venv install unittest clean migrate-up migrate-down migrate-create migrate-history migrate-current

env:
	@if [ -f .env ]; then \
		echo ".env file already exists. Skipping..."; \
	else \
		cp .env.example .env; \
		echo ".env file created from .env.example"; \
		echo "Please update .env with your actual configuration values."; \
	fi

venv:
	@if [ -d venv ]; then \
		echo "Virtual environment already exists. Skipping..."; \
	else \
		python3 -m venv venv; \
		echo "Virtual environment created successfully."; \
		echo "Activate it with: source venv/bin/activate"; \
	fi

install:
	@if [ ! -d venv ]; then \
		echo "Error: Virtual environment not found. Run 'make venv' first."; \
		exit 1; \
	fi
	@echo "Installing dependencies..."
	@. venv/bin/activate && pip install --upgrade pip
	@. venv/bin/activate && pip install -r requirements.txt
	@echo "Dependencies installed successfully."

test:
	@if [ ! -d venv ]; then \
		echo "Error: Virtual environment not found. Run 'make venv' and 'make install' first."; \
		exit 1; \
	fi
	@echo "Running tests..."
	@. venv/bin/activate && pytest tests/ -v --tb=short

unit-test:
	@if [ ! -d venv ]; then \
		echo "Error: Virtual environment not found. Run 'make venv' and 'make install' first."; \
		exit 1; \
	fi
	@echo "Running unit tests..."
	@. venv/bin/activate && pytest tests/unit/ -v --tb=short

integration-test:
	@if [ ! -d venv ]; then \
		echo "Error: Virtual environment not found. Run 'make venv' and 'make install' first."; \
		exit 1; \
	fi
	@echo "Running integration tests..."
	@. venv/bin/activate && pytest tests/integration/ -v --tb=short

migrate-up:
	@if [ ! -d venv ]; then \
		echo "Error: Virtual environment not found. Run 'make venv' and 'make install' first."; \
		exit 1; \
	fi
	@echo "Running database migrations..."
	@. venv/bin/activate && alembic upgrade head
	@echo "Migrations applied successfully."

migrate-down:
	@if [ ! -d venv ]; then \
		echo "Error: Virtual environment not found. Run 'make venv' and 'make install' first."; \
		exit 1; \
	fi
	@echo "Reverting last migration..."
	@. venv/bin/activate && alembic downgrade -1

migrate-create:
	@if [ ! -d venv ]; then \
		echo "Error: Virtual environment not found. Run 'make venv' and 'make install' first."; \
		exit 1; \
	fi
	@if [ -z "$(MSG)" ]; then \
		echo "Error: Migration message required. Usage: make migrate-create MSG='description'"; \
		exit 1; \
	fi
	@echo "Creating new migration: $(MSG)"
	@. venv/bin/activate && alembic revision --autogenerate -m "$(MSG)"

migrate-history:
	@if [ ! -d venv ]; then \
		echo "Error: Virtual environment not found. Run 'make venv' and 'make install' first."; \
		exit 1; \
	fi
	@. venv/bin/activate && alembic history --verbose

migrate-current:
	@if [ ! -d venv ]; then \
		echo "Error: Virtual environment not found. Run 'make venv' and 'make install' first."; \
		exit 1; \
	fi
	@. venv/bin/activate && alembic current --verbose

clean:
	@echo "Cleaning up generated files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name "*.db" -delete 2>/dev/null || true
	@rm -rf .coverage htmlcov/ 2>/dev/null || true
	@echo "Cleanup completed."
