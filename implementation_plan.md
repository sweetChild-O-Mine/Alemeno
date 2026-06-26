# Alemeno Internship Task: AI-Powered Transaction Processing Pipeline

This task requires building a backend API that can asynchronously process a CSV file of transactions, clean the data, detect anomalies, and use an LLM (Gemini 1.5 Flash) to classify transactions and generate a summary. The entire stack needs to be containerized using Docker Compose.

Since you are new to this stack, here is a quick primer on the technologies we will use:
- **FastAPI**: A modern, fast Python web framework for building APIs. It's great because it's fast to write, easy to understand, and automatically generates documentation for your API.
- **PostgreSQL**: A powerful, open-source relational database where we will store the jobs, transactions, and summaries.
- **Redis**: An in-memory data structure store. We'll use it as a "message broker".
- **Celery**: An asynchronous task queue/job queue. When someone uploads a CSV, FastAPI will tell Celery (via Redis) to process it in the background so the user doesn't have to wait. (Analogy: BullMQ or Agenda in Node.js).
- **Docker & Docker Compose**: Docker packages our application and its dependencies into "containers". Docker Compose allows us to define and run multi-container Docker applications (API, Worker, Database, Redis) with a single command.

### MERN Stack to Python/FastAPI Mental Model
- **Express.js -> FastAPI**: Both are web frameworks. FastAPI is heavily type-hinted and generates Swagger docs automatically.
- **Node.js -> Python 3**: The runtime environment.
- **Mongoose/Prisma -> SQLAlchemy**: Your ORM (Object-Relational Mapper) to interact with the database.
- **Zod/Joi -> Pydantic**: Schema validation library. FastAPI uses Pydantic natively for request/response validation.
- **BullMQ -> Celery**: For background jobs and queues.
- **MongoDB -> PostgreSQL**: Moving from NoSQL to a robust SQL relational database.

## User Review Required

> [!IMPORTANT]
> Since we need to use the Gemini 1.5 Flash model for the LLM classification, you will need a **Gemini API Key**. Please let me know if you have one, or I can guide you on how to get it (it's free and requires no spend).

## Proposed Changes

We will build the project in the following phases, and I will explain the code step-by-step as we write it:

### Phase 1: Infrastructure & The DevOps Skeleton (Docker & DB Setup)
- `docker-compose.yml`: Defines the services (API, Celery Worker, PostgreSQL, Redis). We will ensure resource limits and network isolation for production readiness.
- `Dockerfile`: Instructions to build a lightweight, production-ready Python environment (using slim images).
- `requirements.txt`: Python dependencies.
- `.env`: Environment variables for secrets (DB credentials, Gemini API key) so they aren't hardcoded.
- `app/database.py`: PostgreSQL connection setup (we'll use connection pooling for scalability).
- `app/models.py`: SQLAlchemy database models (`Job`, `Transaction`, `JobSummary`).

### Phase 2: The API Endpoints (FastAPI)
- `app/main.py`: The core FastAPI application.
- `app/schemas.py`: Pydantic models for request/response validation.
- Endpoints to implement:
  - `POST /jobs/upload`: Accepts CSV, saves job to DB as pending, sends task to Celery.
  - `GET /jobs/{job_id}/status`: Returns job status.
  - `GET /jobs/{job_id}/results`: Returns cleaned transactions and summary.
  - `GET /jobs`: Lists all jobs.

### Phase 3: The Heavy Lifting (Celery Worker Pipeline)
- `app/worker.py`: Celery tasks and configuration.
- `app/processor.py`: The logic for:
  - **Data Cleaning**: Normalizing dates, stripping currency symbols, uppercase status, removing exact duplicates.
  - **Anomaly Detection**: Flagging amounts > 3x median, USD currency with domestic merchants.
- `app/llm.py`: Integration with Gemini 1.5 Flash for categorization and narrative summary, including retry logic and batch processing.

### Phase 4: Video Presentation Prep
- I will help you create a visual diagram of the architecture.
- I will provide a script/outline for your 3-minute video covering the data flow and how to answer the scaling/bottleneck questions so you can impress your reviewers.

## Verification Plan

### Manual Verification
- We will test the single `docker compose up` command.
- We will test the API endpoints using the built-in FastAPI Swagger UI documentation page.
- We will upload the `transactions.csv` and ensure the pipeline correctly cleans data, calls Gemini, and stores the results in the PostgreSQL database.
