# AuraPronounce - AI English Pronunciation Assessment Web Application

AuraPronounce is a complete, production-ready, clean-architecture web application built to help non-native English speakers assess and improve their pronunciation, pacing, rhythm, stress placements, and fluency.

---

## Features

- **Microphone Recorder & File Uploads**: Record directly in-browser or upload files.
- **Audio Sound Diagnostics**: Validates length (30-45s), detects flatlines/corrupted audio, measures background noise ratios, and rejects silences.
- **Phoneme Alignment Map**: Translates speech into phonetic representations (CMUDict/G2P) and highlights sound substitutions (e.g., TH sound replaced with T).
- **Acoustic scoring engine**: Evaluates Overall, Accuracy, Fluency, Completeness, Stress patterns, Rhythm (durational variances), and Pauses.
- **AI Coach Feedback**: Generates detailed physical articulation guidelines (tongue placements) and custom practice tasks using LLM reasoning.
- **DPDP Compliant**: Enforces explicit consent checkboxes, logs encrypted consent audits, stores data in India, and immediately deletes voice recordings from the server.
- **Prometheus Monitoring**: Exposes a standard Prometheus `/metrics` endpoint and `/health` connection diagnostics.

---

## Tech Stack

- **Frontend**: Next.js 14 (App Router), TypeScript, TailwindCSS, Axios, TanStack Query, Framer Motion, Lucide React, Chart.js
- **Backend**: FastAPI (Python 3.12+), SQLAlchemy, Celery, Redis, PostgreSQL, librosa, soundfile, g2p_en
- **DevOps**: Docker, Docker Compose, GitHub Actions CI/CD

---

## Project Structure

```
Assignment_SWE/
├── backend/
│   ├── app/
│   │   ├── api/             # Routes (Auth, Upload, Analysis, Monitoring)
│   │   ├── core/            # Config, DB connections, Security, Encryption
│   │   ├── models/          # SQLAlchemy schemas
│   │   ├── repositories/    # Database query abstraction & encryption
│   │   ├── services/        # Audio validators, scoring formulas, G2P, LLM
│   │   ├── worker/          # Celery configurations and worker tasks
│   │   ├── main.py          # FastAPI application entrypoint
│   │   └── db_init.py       # SQL table initializer with retry logic
│   ├── tests/               # Backend Pytest suites
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js App Router (Landing, Upload, Results, Privacy)
│   │   ├── lib/             # Axios API integration
│   │   └── globals.css      # Core styles & dark theme guidelines
│   ├── Dockerfile
│   └── package.json
├── docs/
│   └── architecture.md      # Detailed system & compliance report
├── docker-compose.yml
└── README.md
```

---

## Getting Started

### Prerequisites

Make sure you have [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/) installed on your machine.

### Configuration (Environment Variables)

Create a `.env` file in the root workspace to configure API keys:

```env
# API Keys for Live AI features. AuraPronounce prioritizes the free Groq API,
# falling back to OpenAI/Gemini. If omitted entirely, it defaults to a
# deterministic high-fidelity phonetic simulator.
GROQ_API_KEY=your-groq-api-key
OPENAI_API_KEY=your-openai-api-key
GEMINI_API_KEY=your-gemini-api-key
```

### Running with Docker Compose (Recommended)

To launch PostgreSQL, Redis, the FastAPI backend, the Celery background worker, and the Next.js frontend in container environments, run:

```bash
docker-compose up --build
```

- **Next.js Frontend**: [http://localhost:3000](http://localhost:3000)
- **FastAPI API Server**: [http://localhost:8000](http://localhost:8000)
- **Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Prometheus Metrics**: [http://localhost:8000/metrics](http://localhost:8000/metrics)
- **Health Checks**: [http://localhost:8000/health](http://localhost:8000/health)

### Running Locally (Manual Development)

#### 1. Start Redis & PostgreSQL
Ensure local instances of Redis (port 6379) and PostgreSQL (port 5432) are active.

#### 2. Start the Backend API & Worker
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Run database setup
python app/db_init.py

# Launch FastAPI
uvicorn app.main:app --reload --port 8000

# In a separate terminal session, start Celery
celery -A app.worker.celery_app worker --loglevel=info
```

#### 3. Start Next.js Frontend
```bash
cd frontend

# Install dependencies
npm install

# Launch Development Server
npm run dev
```

---

## Running Automated Tests

To execute the Pytest suite covering API routes, the scoring engine, and validation constraints:

```bash
cd backend
pytest -v
```

---

## DPDP Compliance & Right to Erasure

- **Raw Audio Purges**: Audio recordings are processed in-memory or saved temporarily to disk, then wiped from storage inside the Celery task immediately after analysis.
- **Encrypted Audit Logs**: The database encrypts user identifiers using AES-256 before logging audit logs or consent checkboxes.
- **Requesting Erasure**: Visit `/privacy#deletion` on the web interface, enter your email, and click "Submit Purge Request". The backend will instantly delete all matching account records, consent trails, and score reports.
