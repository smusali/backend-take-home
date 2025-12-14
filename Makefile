.PHONY: env venv install unittest clean

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

unittest:
	@if [ ! -d venv ]; then \
		echo "Error: Virtual environment not found. Run 'make venv' and 'make install' first."; \
		exit 1; \
	fi
	@echo "Running unit tests..."
	@. venv/bin/activate && pytest tests/ -v --tb=short

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
