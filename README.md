# Champion Recommendation - Enhancement Version

This project uses **Poetry** for Python dependencies and **Docker Compose** for running the application.

---

## Prerequisites

- [Poetry](https://python-poetry.org/)
- [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/)
- Git

---

## Running the Project

To start the project, simply run:

```bash
make start_app
```

This command will:
- Check and set up the Poetry virtual environment.
- Install pre-commit hooks if available.
- Start all Docker containers in detached mode.

## Stopping the Project

To stop the running containers:

```bash
make stop_app
```
