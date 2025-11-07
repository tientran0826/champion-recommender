# Champion Recommender System For League of Legends

## Overview

This project is based on the algorithm from **["Champion Recommender System for League of Legends"](https://courses.cs.washington.edu/courses/cse547/21sp/old_projects/kim_etal.pdf)** by the University of Washington.  

For more details, you can explore the algorithm implementation in the [`exploration`](./exploration) folder, where I have also included the original research paper.  

The purpose of this project is to build an **end-to-end pipeline** covering **data ingestion**, **model training**, and **model serving** through a simple user interface.

---

## Prerequisites

- [Poetry](https://python-poetry.org/)
- [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/)

---

## Architecture Overview
#### 1. Data Layer

Handles data ingestion, storage, and access.

- Dagster – orchestrates the data pipelines and schedules tasks.
- Riot APIs – source of raw match and champion data.
- Minio (S3-compatible) – stores raw & transformed data, as well as MLFlow artifacts.
- Trino + Hive Metastore – provides queryable data warehouse built over Minio.

#### 2.ML Layer

Handles training, model registry, and inference logic.

- FastAPI (Model API) – endpoints for training & serving models.
- MLFlow – experiment tracking, model versioning, and registry (uses Minio as backend).

#### 3.Application Layer

Provides UI and interaction for users.

- Dash – frontend UI for champion recommendation.
- Trino – provides champion metadata and history for visualization.
- FastAPI (Serving) – provides live recommendations.

![System Diagram](images/system_diagram.jpg)

## Running the Project

To start the project, simply run:

```bash
make start_app
```

This command will:
- Check and set up the Poetry virtual environment.
- Install pre-commit hooks if available.
- Start all Docker containers in detached mode.

## Pipeline Overview

The pipeline runs automatically on a schedule once both the **ingestion** and **training** pipelines are completed.  

In **testing mode**, you can manually execute it by following these steps:

1. **Ensure all Docker containers are running properly.**  
2. **Access Dagster**, then:  
   - Trigger the **`match_crawler_job`** in the *Jobs* tab — this will automatically trigger the **`load_data_to_warehouse`** job to sync data so it can be viewed in Trino.  
   - Run the **`champion_crawler_job`** to fetch the latest information about all champions in the game (used to support the UI).  
3. **Trigger the training job:**  
   - Run **`trigger_training_job`** in Dagster to train the model and assign the production tag, **or**  
   - Access the **FastAPI docs** of the `model_pipeline` service to manually trigger training through the API.  
     *(All default configurations are already set.)*  
4. Once all the steps above are completed, you can start using the **UI**.

---

## Open Points

- The **evaluation metrics** are implemented in the `exploration` folder, but they are not yet integrated into the model pipeline. Currently, only the **latest trained model** is tagged for production and served.  
- **Model monitoring** (e.g., with Grafana or similar frameworks) still needs to be set up.  
- The **Dash-based UI** is a simple experimental interface for testing user interactions — it can be further improved for production use.
  
