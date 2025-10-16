.PHONY: install check_env install_hooks start_app stop_app

install:
	@echo Installing dependencies...
	poetry install --no-root

check_env:
	@echo Checking Poetry virtualenv...
	@poetry env info --path >NUL 2>&1 && ( \
		echo Virtual environment found. \
	) || ( \
		echo No venv found — running 'poetry install --no-root'... && poetry install --no-root \
	)

install_hooks:
	@echo Checking pre-commit installation...
	@poetry run pre-commit --version >NUL 2>&1 && ( \
		echo Installing pre-commit hooks... && poetry run pre-commit install \
	) || ( \
		echo pre-commit not available — skipping hook installation. \
	)

start_app: check_env install_hooks
	@echo Starting Docker containers...
	docker compose up -d

stop_app:
	@echo Stopping Docker containers...
	docker compose down
