# FlowPilot AI — Autonomous AI Workflow Automation Platform

[![CI/CD Pipeline](https://github.com/flowpilot-ai/flowpilot/actions/workflows/ci.yml/badge.svg)](https://github.com/flowpilot-ai/flowpilot/actions)
[![Python 3.13](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Next.js 16](https://img.shields.io/badge/Next.js-16.4+-black.svg)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17%20with%20pgvector-336791.svg)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **"Describe your workflow. Let AI design it. Review it. Execute it. Monitor everything."**

FlowPilot AI is a production-grade autonomous AI workflow automation platform that unifies natural-language workflow generation, visual drag-and-drop DAG editing, multi-agent AI runtime, asynchronous execution with human-in-the-loop approvals, and live telemetry observability.

---

## 🌟 Key Features

1. **Natural-Language Workflow Generation**
   - Translate high-level prompts into strictly validated Directed Acyclic Graphs (DAGs) $G=(V, E)$.
   - Decomposes user goals, selects authorized capability registry nodes, and outputs structured plans.

2. **Visual Workflow Studio (React Flow / XYFlow)**
   - Three-panel visual orchestrator with node palette, infinite canvas, and right-hand inspector.
   - 12+ custom node types: Triggers (Manual, Schedule, Gmail), AI Agents, LLM Completion, Classifiers, Condition Branches, Transformers, Human Approval, HTTP Integrations, Delays, Notifications, and Outputs.

3. **Multi-Agent AI Runtime**
   - Provider-independent architecture: Google Gemini 1.5, Ollama local models, and deterministic test mocks.
   - Specialized agents: **Planner Agent**, **Analyst Agent**, **Executor Agent**, **Validator Agent**, and **Supervisor**.

4. **Resilient DAG Execution Engine**
   - Kahn's algorithm for topological sorting and cycle detection.
   - Transactional state machine: `PENDING` $\rightarrow$ `QUEUED` $\rightarrow$ `RUNNING` $\rightarrow$ `WAITING_APPROVAL` $\rightarrow$ `COMPLETED` / `FAILED`.
   - Dual execution modes: Distributed Celery/Redis workers or in-process FastAPI async background runner.

5. **Human-in-the-Loop Approval Center**
   - Durable pause-and-resume: pauses workflow execution at sensitive action nodes.
   - Review proposed action payloads (e.g. drafted emails), edit parameters directly in the UI, and approve or reject.

6. **Gmail & External Integrations**
   - Google OAuth2 flow, unread email fetching, priority triaging, and verified email dispatch.
   - Built-in sandbox inbox for offline testing without requiring live Google cloud credentials.

7. **RAG Knowledge Base & pgvector**
   - Ingestion and chunking for PDF, DOCX, and TXT documents.
   - Cosine similarity vector search with attributed citations.

8. **Live Observability & Analytics**
   - Real-time node state machine timeline, latency telemetry, raw input/output inspectors.
   - Recharts visual dashboards for execution velocity, outcome distribution, and token cost tracking.

---

## 🏗️ System Architecture

```
FlowPilotAI/
|-- backend/
|   |-- app/
|   |   |-- api/v1/          # Modular FastAPI Routers (Auth, Workflows, Approvals, etc.)
|   |   |-- core/            # Config, Security (Argon2id/JWT), Database manager
|   |   |-- database/        # 18 SQLAlchemy 2.x Models & Seed Data
|   |   |-- engine/          # Kahn's DAG Compiler, Handlers & Resilient Runner
|   |   |-- ai/              # Multi-Agent Runtime, Planner, Providers & RAG
|   |   |-- integrations/    # Gmail OAuth2 & Sandbox Service
|   |   |-- workers/         # Celery App & Async Worker Tasks
|   |   |-- schemas/         # Pydantic v2 Strict Request/Response Schemas
|   |-- tests/               # Pytest Automated Test Suite
|   |-- Dockerfile
|-- frontend/
|   |-- src/
|   |   |-- app/             # Next.js 16 App Router Pages
|   |   |-- components/      # Sidebar, Header, Shell
|   |   |-- features/        # Studio, Generator, Approvals, Inspector, Analytics
|   |   |-- services/        # Typed API Client
|   |   |-- types/           # TypeScript Domain Contracts
|   |-- Dockerfile
|-- docker-compose.yml       # Full stack: PostgreSQL 17 + pgvector, Redis, Backend, Worker
|-- .env.example
```

---

## 🚀 Quickstart Guide

### Prerequisites
- Python 3.13+
- Node.js 22+
- Docker & Docker Compose (optional for standalone mode)

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run database migration & seed demo workspace
python -m app.database.init_db

# Run automated tests
pytest -v

# Start backend server
uvicorn app.main:app --reload --port 8000
```
Backend API will be live at: `http://localhost:8000`  
Interactive OpenAPI Docs: `http://localhost:8000/docs`

### 2. Frontend Setup

```bash
cd frontend

# Install packages
npm install

# Build production bundle
npm run build

# Start Next.js server
npm run dev
```
Frontend will be live at: `http://localhost:3000`

---

## 🧪 Acceptance Test Scenario Walkthrough

### Scenario: End-to-End Autonomous Email Triaging & Approval
1. Navigate to **AI Generator** (`/generator`).
2. Enter prompt:
   > *"Analyze my unread emails, classify urgent messages, summarize important emails, and prepare responses for my approval."*
3. Click **Generate Workflow**:
   - The AI Planner decomposes the request into `gmailTrigger` $\rightarrow$ `textClassifier` $\rightarrow$ `aiAgent` $\rightarrow$ `humanApproval` $\rightarrow$ `output`.
4. Click **Open in Studio**:
   - Inspect the interactive DAG canvas in **Workflow Studio** (`/studio`).
   - Click **Validate DAG** (validates acyclic topology and trigger contracts).
   - Click **Execute Workflow**.
5. Execution initiates asynchronously:
   - `gmailTrigger` retrieves unread incoming emails.
   - `textClassifier` and `aiAgent` score urgency and draft a response.
   - Execution reaches the `humanApproval` node and safely suspends (`WAITING_APPROVAL`).
6. Navigate to **Approval Center** (`/approvals`):
   - Inspect the pending card with the AI-generated draft.
   - Edit the draft text or notes.
   - Click **Approve & Dispatch**.
7. The execution resumes:
   - The authorized email is dispatched via `output` node.
   - Execution transitions to `COMPLETED`.
8. Navigate to **Executions** (`/executions`) to observe node timing, token telemetry, and raw outputs!

---

## 🔒 Security Architecture
- **Password Security**: Argon2id password hashing via `argon2-cffi` adhering to RFC 9106.
- **Session Tokens**: JWT with HTTP-only, SameSite=Strict cookie delivery.
- **Credential Protection**: OAuth tokens and API secrets encrypted at rest using Fernet AES symmetric encryption.
- **Agent Boundaries**: Strict capability registry prevents arbitrary shell execution or SSRF. Sensitive actions require explicit human authorization.

---

## 📄 License
MIT License. Built for FlowPilot AI.
