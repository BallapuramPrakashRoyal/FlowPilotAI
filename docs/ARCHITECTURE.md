# FlowPilot AI — Architectural Design & Specification

## 1. High-Level Architecture

FlowPilot AI is engineered as a **Modular Monolith** combining an asynchronous, recoverable directed acyclic graph (DAG) execution engine, multi-agent AI orchestration runtime, and a reactive visual workflow studio.

```mermaid
flowchart TD
    subgraph FrontendTier ["Frontend Layer (Next.js 16 + React 19)"]
        UI["Studio / Dashboard / Approvals / Integrations"]
        State["Zustand + React Flow (XYFlow)"]
        Toast["Toast Notification System"]
    end

    subgraph APITier ["API & Gateway (FastAPI)"]
        AuthMid["JWT & RBAC Middleware"]
        Router["REST API Router (/api/v1)"]
        AuditService["Audit Logging Service"]
        SecSvc["Fernet AES-256 Encryption"]
    end

    subgraph CoreEngine ["Workflow Engine & Multi-Agent Runtime"]
        DAG["DAG Validator (Kahn's Algorithm)"]
        Runner["WorkflowExecutionRunner"]
        Orchestrator["MultiAgentOrchestrator"]
        Supervisor["MultiAgentSupervisor"]
        AgentRuntime["Specialized Agents (Planner, Analyst, Researcher, Executor, Validator)"]
        ToolRegistry["Capability & Tool Registry"]
    end

    subgraph AsyncTier ["Persistence & Worker Tier"]
        PG[("PostgreSQL 17 + pgvector")]
        Redis[("Redis 7 Queue & Result Store")]
        CeleryWorker["Celery Execution Workers (solo / prefork)"]
        CeleryBeat["Celery Periodic Scheduler (Beat)"]
    end

    subgraph ExternalTier ["External Providers & Integrations"]
        Gemini["Google Gemini 1.5 / Ollama / Mock"]
        Gmail["Google OAuth 2.0 & Gmail API"]
        RAG["Vector Search (pgvector)"]
    end

    UI --> Router
    Router --> AuthMid
    AuthMid --> CoreEngine
    CoreEngine --> Runner
    Runner --> Redis
    Redis --> CeleryWorker
    CeleryWorker --> Orchestrator
    Orchestrator --> AgentRuntime
    AgentRuntime --> ToolRegistry
    ToolRegistry --> ExternalTier
    CeleryWorker --> PG
    CeleryBeat --> Redis
    Router --> AuditService
    AuditService --> PG
```

---

## 2. Database Relationship Diagram

```mermaid
erDiagram
    users ||--o{ workspaces : owns
    users ||--o{ workspace_members : belongs_to
    workspaces ||--o{ workspace_members : has
    workspaces ||--o{ workflows : contains
    workspaces ||--o{ executions : owns
    workspaces ||--o{ integrations : connects
    workspaces ||--o{ knowledge_bases : maintains
    workspaces ||--o{ audit_logs : records
    workspaces ||--o{ agent_runs : tracks

    workflows ||--o{ workflow_versions : has
    workflows ||--o{ executions : runs

    executions ||--o{ execution_nodes : contains
    executions ||--o{ execution_events : logs
    executions ||--o{ approvals : pauses_for
    executions ||--o{ agent_runs : executes

    integrations ||--o| integration_credentials : stores

    knowledge_bases ||--o{ documents : indexes
    documents ||--o{ document_chunks : splits_into

    users {
        string id PK
        string email UK
        string password_hash
        string full_name
        boolean is_active
        boolean is_superuser
    }

    workspaces {
        string id PK
        string name
        string slug UK
        string owner_id FK
    }

    workflows {
        string id PK
        string workspace_id FK
        string name
        string current_version_id
        boolean is_active
    }

    executions {
        string id PK
        string workspace_id FK
        string workflow_id FK
        string status
        string trigger_type
        int duration_ms
        json context_data
    }

    approvals {
        string id PK
        string workspace_id FK
        string execution_id FK
        string status
        string action_type
        json proposal_data
    }

    agent_runs {
        string id PK
        string workspace_id FK
        string execution_id FK
        string task_id
        string agent_role
        string status
        string idempotency_key
        int token_count
        int latency_ms
    }

    audit_logs {
        string id PK
        string workspace_id FK
        string action
        string resource_type
        string resource_id
        json details
    }
```

---

## 3. Main Workflow Execution Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User as Operator / Trigger
    participant API as FastAPI Gateway
    participant Runner as WorkflowExecutionRunner
    participant Queue as Redis & Celery
    participant Node as Node Handlers
    participant Approval as Approval Center
    participant DB as PostgreSQL

    User->>API: POST /api/v1/workflows/{id}/execute
    API->>DB: Create Execution (status: QUEUED)
    API->>Queue: Dispatch execute_workflow_task.delay(execution_id)
    API-->>User: 200 OK (execution_id, status: QUEUED)

    Queue->>Runner: Pick up task & start_execution(execution_id)
    Runner->>DB: Update Execution (status: RUNNING)
    Runner->>Runner: Topological Sort (Kahn's algorithm)

    loop For each topological node batch
        Runner->>Node: execute_node(node_type, config, inputs)
        Node-->>Runner: NodeExecutionResult(status, output)
        Runner->>DB: Persist ExecutionNode & ExecutionEvent
    end

    alt Hits Human Approval Node
        Runner->>DB: Create Approval (status: PENDING)
        Runner->>DB: Update Execution (status: WAITING_APPROVAL)
        Runner-->>User: Execution paused awaiting human review
        User->>API: POST /api/v1/approvals/{id}/decide (APPROVED / REJECTED)
        API->>DB: Synchronous commit (status: APPROVED/REJECTED)
        API->>Queue: Schedule resume_after_approval
        Queue->>Runner: Resume execution from approval node
    end

    Runner->>DB: Update Execution (status: COMPLETED / CANCELLED)
```

---

## 4. Multi-Agent Orchestration Flow

```mermaid
flowchart TD
    Start["User / Input Payload"] --> Planner["Planner Agent"]
    Planner --> Plan["Generate PlanResult (Tasks + Dependency DAG)"]
    Plan --> Supervisor["MultiAgentSupervisor"]

    subgraph OrchestrationLoop ["Durable Orchestration Loop"]
        Supervisor --> CheckTask{"Next Ready Task?"}
        CheckTask -->|Yes| Idempotency{"Check SHA-256 Idempotency Key"}
        Idempotency -->|Cached Output Exists| Skip["Skip Duplicate Execution & Reuse Output"]
        Idempotency -->|New Execution| DispatchAgent["Dispatch Assigned Agent"]

        DispatchAgent --> AgentSwitch{"Agent Role"}
        AgentSwitch -->|Analyst| Analyst["Analyst Agent (Triaging & Priority)"]
        AgentSwitch -->|Researcher| Researcher["Researcher Agent (pgvector RAG)"]
        AgentSwitch -->|Executor| Executor["Executor Agent (Tool Calling)"]
        AgentSwitch -->|Validator| Validator["Validator Agent (Safety & Policy)"]

        Analyst --> RecordRun["Persist AgentRun Telemetry"]
        Researcher --> RecordRun
        Executor --> RecordRun
        Validator --> RecordRun

        Skip --> RecordRun
        RecordRun --> PassHandoff["Propagate Task Output Handoffs"]
        PassHandoff --> CheckTask
        CheckTask -->|All Tasks Done| FinalResult["Final Aggregated Plan Outcome"]
    end

    FinalResult --> End["Complete Execution"]
```

---

## 5. Setup & Development Instructions

### Prerequisites
- Python 3.13+
- Node.js 22+ & npm 10+
- PostgreSQL 17 with `pgvector` extension
- Redis 7+

### Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Or on Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start background worker (Windows solo pool, or default on Linux)
celery -A app.workers.celery_app worker --loglevel=info -P solo

# Start scheduler
celery -A app.workers.celery_app beat --loglevel=info

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend
npm ci
npm run dev
# Browse to http://localhost:3000
```

---

## 6. Known Limitations & Production Constraints

1. **Celery Worker on Windows**:
   - Python's `prefork` process pool is unsupported on Windows. Workers on Windows must run with `--pool=solo` or `--pool=threads`. In Linux / Docker deployments, standard `prefork` or `gevent` pools should be utilized.
2. **Google OAuth Verification**:
   - Live Google token exchanges require valid `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` credentials registered in Google Cloud Console. When unconfigured, FlowPilot displays a real connection-required state rather than simulating fake email traffic.
3. **Database Concurrency in Fallback Mode**:
   - The primary storage engine is PostgreSQL with `pgvector`. In SQLite fallback mode, concurrent writes are serialized using SQLite's write-ahead log (`WAL`).
