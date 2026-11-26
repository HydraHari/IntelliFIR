# IntelliFIR

> **Turning citizen complaints into evidence-grounded FIR drafts.**

IntelliFIR is an AI-assisted complaint-to-FIR drafting and investigation-support platform. It accepts unstructured citizen complaints and transforms them into structured case information and a draft First Information Report (FIR), with full evidence provenance, independent factual validation, and human review workflows.

> ⚠️ **Important**: IntelliFIR generates AI-assisted *draft* documents only. It does not autonomously determine guilt, make final legal decisions, or officially register FIRs. All generated drafts require authorized human review before any official action.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start (Docker)](#quick-start-docker)
- [Local Development](#local-development)
- [Environment Configuration](#environment-configuration)
- [Database Migrations](#database-migrations)
- [AI Model Setup](#ai-model-setup)
- [Demo Mode](#demo-mode)
- [API Documentation](#api-documentation)
- [Research Evaluation](#research-evaluation)
- [Troubleshooting](#troubleshooting)
- [Production Deployment](#production-deployment)
- [Privacy and Security](#privacy-and-security)

---

## Features

| Feature | Description |
|---------|-------------|
| 📄 Complaint Ingestion | PDF, DOCX, TXT, JPG, PNG upload + manual entry + OCR |
| 🔍 NER Pipeline | BERT-based named entity recognition (configurable checkpoint) |
| 🔗 Evidence Provenance | Every extracted fact linked to source text spans |
| 📝 FIR Draft Generation | Template-based + optional LLM narrative generation |
| ✅ Independent Validation | Automated draft-vs-complaint verification |
| 🔎 Similar Case Retrieval | Sentence Transformers + FAISS semantic search |
| ⚖️ Legal Information | Semantic search over verified legal documents |
| 🕵️ AI Investigation Agent | Autonomous multi-step tool-using agent (Analysis, Provenance, Validation, Legal, Similar Cases, Reports) |
| 🤖 RAG Assistant | Retrieval-augmented investigation support with citations |
| 👨‍💼 Review Workflow | Human reviewer decision capture with audit trail |
| 📊 Research Evaluation | Reproducible metric comparison across three systems |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  React Frontend (Vite + TypeScript + Tailwind + shadcn)  │
└──────────────────────────┬──────────────────────────────┘
                           │ REST API
┌──────────────────────────▼──────────────────────────────┐
│  FastAPI Backend (Python 3.11+)                          │
│  ┌────────────┐ ┌──────────┐ ┌───────────────────────┐  │
│  │  REST APIs │ │ Services │ │   AI/ML Pipeline      │  │
│  │  (v1)      │ │          │ │  NER → IE → Draft     │  │
│  │            │ │          │ │  Validation → RAG     │  │
│  └────────────┘ └──────────┘ └───────────────────────┘  │
└──────────────────────────┬──────────────────────────────┘
                           │
       ┌───────────────────┼──────────────────┐
       ▼                   ▼                  ▼
 PostgreSQL 15        FAISS Index        File Storage
 (Users, Cases,     (Embeddings,        (Uploaded
  Drafts, etc.)      Similar Cases)      Documents)
```

---

## AI Investigation Agent

IntelliFIR includes an autonomous, tool-using **AI Investigation Agent** that upgrades standard RAG assistance into an active investigative co-pilot.

### Core Agent Capabilities
- **Natural-Language Understanding:** Decomposes complex investigator queries into structured execution plans.
- **Dynamic Tool Calling:** Invokes only the necessary tools required to answer the query.
- **Multi-Step Workflows:** Sequentially chains complaint analysis, character-level provenance checks, factual contradiction validation, legal research, similar-case retrieval, and structured reporting.
- **Strict Evidence Grounding:** Verifies every fact against the original complaint via Unicode character offsets `raw_text[start:end] == span_text`.
- **Statutory Grounding:** Maps offences directly to the **Bharatiya Nyaya Sanhita, 2023 (BNS)**, BNSS 2023, and BSA 2023, cross-referencing historical IPC sections without hallucinating non-existent provisions.
- **Consequential Action Safeguard:** Automatically blocks attempts to autonomously register FIRs, order arrests, or declare guilt, enforcing mandatory human officer authorization under the law.

### The 6 Agent Tools
| Tool Name | Key Function | Output Artifact |
|-----------|--------------|-----------------|
| `analyze_complaint` | Extracts parties, dates, locations, property, weapons, and distinguishes allegations from established facts | `ComplaintAnalysisOutput` |
| `verify_evidence_provenance` | Audits character-level offsets against raw text; preserves Unicode invariants and flags unsupported facts | `EvidenceProvenanceOutput` |
| `validate_complaint_facts` | Identifies contradictions, timeline inconsistencies, missing statutory elements, and ambiguous claims | `FactualValidationOutput` |
| `research_legal_provisions` | Searches verified BNS 2023 / IPC statutes, cognizable/bailable classifications, and penal ingredients | `LegalResearchOutput` |
| `retrieve_similar_cases` | FAISS semantic search for similar case dockets and precedent modus operandi with legal disclaimers | `SimilarCaseOutput` |
| `generate_investigation_report` | Synthesizes an end-to-end investigation report formatted in Markdown with human review controls | `InvestigationReportOutput` |

### Agent API Endpoints
- `POST /api/v1/assistant/agent/run`: Run autonomous investigation workflows with conversational history and case context.
- `GET /api/v1/assistant/tools`: Inspect available tool metadata, parameters, and descriptions.
- `GET /api/v1/assistant/cases`: Search and list indexed case dockets for the agent interface.
- `POST /api/v1/assistant/query`: Legacy single-turn RAG query endpoint (fully backward-compatible).

---

## Prerequisites

- **Docker Desktop** 24+ and **Docker Compose** v2
- Or for local dev:
  - Python 3.11+
  - Node.js 20+
  - PostgreSQL 15+
  - Tesseract OCR (`brew install tesseract` / `apt install tesseract-ocr`)
- For LLM features: [Ollama](https://ollama.ai) with a compatible model

---

## Quick Start (Docker)

```bash
# 1. Clone the repository
git clone <repo-url>
cd Intelli_Fir

# 2. Set up environment variables
cp .env.example .env
# Edit .env — set POSTGRES_PASSWORD and SECRET_KEY at minimum

# 3. Build and start all services
docker compose up --build

# 4. Access the application
#    Frontend:   http://localhost:80
#    Backend API: http://localhost:8000
#    API Docs:   http://localhost:8000/docs
```

The first run will:
- Pull PostgreSQL 15 Docker image
- Build the backend (downloads ~2–4 GB of Python + ML dependencies)
- Build the frontend
- Run database migrations automatically
- Start all services

> Model downloads (NER, embeddings) happen on first use, not at startup.

---

## Local Development

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model (needed for text processing)
python -m spacy download en_core_web_sm

# Configure environment
cp ../.env.example .env
# Edit .env to set DATABASE_URL to your local PostgreSQL

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
echo "VITE_API_URL=http://localhost:8000" > .env.local
echo "VITE_DEMO_MODE=false" >> .env.local

# Start dev server
npm run dev
# → http://localhost:5173
```

---

## Environment Configuration

Copy `.env.example` to `.env` and configure:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ | — | PostgreSQL connection URL |
| `SECRET_KEY` | ✅ | — | JWT signing key (generate randomly) |
| `NER_MODEL_CHECKPOINT` | ❌ | `dslim/bert-base-NER` | HuggingFace NER checkpoint |
| `EMBEDDING_MODEL` | ❌ | `all-MiniLM-L6-v2` | Sentence Transformers model |
| `LLM_PROVIDER` | ❌ | `none` | `none` or `ollama` |
| `OLLAMA_BASE_URL` | ❌ | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | ❌ | `llama3.1:8b` | Ollama model name |
| `DEMO_MODE` | ❌ | `false` | Load fictional demo data |
| `SIMILARITY_THRESHOLD` | ❌ | `0.5` | Minimum FAISS similarity score |

Generate a secure SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Database Migrations

```bash
cd backend

# Apply all migrations
alembic upgrade head

# Check current migration
alembic current

# Create a new migration
alembic revision --autogenerate -m "description"

# Rollback one step
alembic downgrade -1
```

---

## AI Model Setup

### NER Model

The NER model is downloaded from HuggingFace on first use. To pre-download:

```bash
cd backend
python -c "
from transformers import pipeline
pipe = pipeline('token-classification', model='dslim/bert-base-NER')
print('NER model ready')
"
```

To use **IndicBERT** for Indian language complaints:
```env
NER_MODEL_CHECKPOINT=ai4bharat/IndicBERTv2-SS-ner
```

### Fine-tuning (Optional)

If you have labeled complaint data in BIO format:

```bash
cd backend
python -m app.ml.training.trainer \
  --data-path /path/to/labeled_data.json \
  --model-checkpoint dslim/bert-base-NER \
  --output-dir ./models_cache/finetuned_ner \
  --epochs 3
```

After fine-tuning, update `NER_MODEL_CHECKPOINT` to point to your checkpoint.

### Embedding Model

Downloaded automatically on first similar-case search.

### LLM via Ollama

```bash
# Install Ollama: https://ollama.ai

# Pull a model
ollama pull llama3.1:8b

# Start Ollama (runs on port 11434)
ollama serve

# Then set in .env:
# LLM_PROVIDER=ollama
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_MODEL=llama3.1:8b
```

---

## Demo Mode

Enable demo mode to load fictional sample complaints without any real data:

```env
DEMO_MODE=true
```

Demo data includes 5 fictional complaints with pre-computed extractions, drafts, and validation results. All demo data is clearly labeled as fictional and contains no real personal information.

```bash
# Seed demo data manually
cd backend
python -c "from app.core.demo_data import seed_demo_data; import asyncio; asyncio.run(seed_demo_data())"
```

---

## API Documentation

After starting the backend, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Authentication

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password123","full_name":"Admin","role":"administrator"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=admin@example.com&password=password123"
# → Returns: {"access_token": "...", "token_type": "bearer"}
```

---

## Research Evaluation

Compare three systems (Baseline A: direct LLM, Baseline B: template, IntelliFIR):

```bash
cd backend

# Run full evaluation (requires evaluation dataset)
python evaluation/run_evaluation.py \
  --dataset evaluation/sample_dataset.json \
  --output evaluation_results.json

# View results
cat evaluation_results.json | python -m json.tool
```

Metrics reported:
- Entity extraction: Precision, Recall, F1 per entity type
- Supported/unsupported claim rates
- Evidence-link correctness
- Missing information detection P/R/F1
- Contradiction detection P/R/F1

> **Note**: Results are computed from actual outputs. No accuracy values are hardcoded.

---

## Testing and Verification

### Backend Automated Test Suite
Run all unit, integration, and AI Investigation Agent tests:

```bash
# From repository root
PYTHONPATH=backend python3 -m pytest backend/tests

# Run specifically the AI Investigation Agent tests
PYTHONPATH=backend python3 -m pytest backend/tests/test_investigation_agent.py -v
PYTHONPATH=backend python3 -m pytest backend/tests/test_investigation_agent_api.py -v
```

### Frontend Production Build
Verify TypeScript compilation and client asset bundle build:

```bash
cd frontend
npm run build
```

---

## Troubleshooting

### Database connection refused
```bash
# Check PostgreSQL is running
docker compose ps postgres
docker compose logs postgres
```

### NER model fails to load
```bash
# Check available memory (BERT requires ~1–2 GB RAM)
# Use a smaller model:
NER_MODEL_CHECKPOINT=dslim/bert-base-NER  # ~400MB
```

### Tesseract not found (OCR)
```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt install tesseract-ocr tesseract-ocr-eng

# Then restart the backend
```

### FAISS index error on startup
```bash
# Delete and rebuild the index
rm -rf faiss_index/*
# Index is rebuilt on next similar-case ingest
```

### Ollama connection refused
```bash
# Ensure Ollama is running
ollama serve

# Check the model is downloaded
ollama list

# Test connection
curl http://localhost:11434/api/tags
```

### Upload fails with 413
```bash
# Increase MAX_UPLOAD_SIZE_MB in .env
MAX_UPLOAD_SIZE_MB=50
```

---

## Production Deployment

1. **Secrets**: Generate strong `SECRET_KEY` and `POSTGRES_PASSWORD`
2. **HTTPS**: Put Nginx or a cloud load balancer with TLS in front
3. **CORS**: Set `CORS_ORIGINS` to your production domain only
4. **LLM Privacy**: Set `LLM_PROVIDER=none` or use a local Ollama instance — do not send complaint data to external APIs
5. **Backups**: Configure PostgreSQL backup for `postgres_data` volume
6. **Monitoring**: Set `LOG_LEVEL=WARNING` in production
7. **Role Restriction**: Create administrator accounts and disable open registration if needed
8. **Model Cache**: Mount `models_cache` volume to persist downloaded models across restarts

```bash
# Production compose
docker compose -f docker-compose.yml up -d --build
```

---

## Privacy and Security

IntelliFIR handles **sensitive personal and legal information**.

- Complaint text is stored in PostgreSQL, encrypted at rest if the host OS/cloud provider supports it
- Uploaded files are stored with UUID filenames — not accessible via public URLs
- JWT tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES`
- Complaint content is **not** written to application logs
- All significant user actions are recorded in an audit log
- Role-based access control restricts data to authorized users
- When using LLM features, review your LLM provider's data retention policies
- For sensitive deployments, use `LLM_PROVIDER=none` and local Ollama

See `PRIVACY.md` for the full privacy notice.

---

## License

This project is a research prototype. See `LICENSE` for details.

---

*IntelliFIR — Turning citizen complaints into evidence-grounded FIR drafts.*
