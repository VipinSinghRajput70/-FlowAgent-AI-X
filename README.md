# 📚 FlowAgent AI — Combined Project Documentation

This document combines the documentation from the root, backend, and frontend of the FlowAgent AI repository to give you a single, unified manual that you can easily share.

## 📋 Table of Contents
1. [Root Project Overview](#-flowagent-ai--multi-agent-business-operations-platform)
   - [What This Project Does](#-what-this-project-does)
   - [Architecture](#%EF%B8%8F-architecture)
   - [Tech Stack](#%EF%B8%8F-tech-stack--why-each-was-chosen)
   - [Project Structure](#-project-structure)
   - [The 6 AI Agents](#-the-6-ai-agents--in-detail)
   - [Local Machine Learning Models](#-machine-learning-models--4-local-models-zero-api-cost)
   - [RAG Knowledge Base](#-rag-knowledge-base--hybrid-search-engine)
   - [Running the Project](#-how-to-run)
   - [Docker Setup](#-docker-optional)
   - [Running Tests](#-running-tests)
   - [Key Endpoints](#-key-api-endpoints)
   - [Security & Rate Limiting](#-security-features)
2. [Backend Deep Dive](#-backend--flowagent-ai)
   - [Backend Directory Structure](#-directory-structure)
   - [Agent Manager Details](#-agent-manager-agent_managerpy)
   - [Database Schema & Tables](#%EF%B8%8F-database-databasepy)
   - [Vector Store & Hybrid Search](#-vector-store--rag-engine-vector_storepy)
   - [Custom Security Details](#-security-securitypy)
3. [Frontend & Widget Deep Dive](#-frontend--flowagent-ai-dashboard--chat-widget)
   - [Frontend Directory Structure](#-directory-structure-1)
   - [Dashboard Sections](#-dashboard-sections)
   - [Design System & Theme](#-design-system-stylescss)
   - [Embeddable Chat Widget](#-embeddable-chat-widget-widget)

---

# 🤖 FlowAgent AI X — Autonomous Multi-Agent Business Operating System

> **FlowAgent AI X is a state-of-the-art autonomous business operating system that coordinates 12 specialized AI agents, persistent Business Memory, real-world action integrations (Resend, Discord webhooks), explainable AI churn forecasting, a live digital twin simulator, and self-healing knowledge curators.**

### 🔗 Live Resources:
* 🖥️ **Live Dashboard Console**: [https://flowagent-ai-x.streamlit.app](https://flowagent-ai-x.streamlit.app)
* 💻 **GitHub Code Repository**: [https://github.com/VipinSinghRajput70/-FlowAgent-AI-X](https://github.com/VipinSinghRajput70/-FlowAgent-AI-X)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white"/>
  <img src="https://img.shields.io/badge/Google_Gemini-12_AI_Agents-4285F4?style=for-the-badge&logo=google&logoColor=white"/>
  <img src="https://img.shields.io/badge/ChromaDB-Self_Healing_RAG-7C3AED?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/scikit--learn-Local_Predictors-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white"/>
</p>

---

## ⚡ Core Operational Features (FlowAgent AI X)

FlowAgent AI X introduces enterprise-grade automation modules. The following key operational layers are fully implemented:

1. **12+ Specialized AI Agents**: Planner, Safety, Fraud, Curator, Support, Care, Finance, Marketing, Ticket, Sales, Analytics, Exec Decision, and Supervisor collaborating concurrently.
2. **Persistent Business Memory**: Multi-turn customer preferences, historical discounts, and sentiment trends stored permanently in SQLite.
3. **Company Digital Twin Simulator**: A what-if operations forecaster modeling pricing, staffing, and marketing scenario impacts.
4. **Autonomous Action Executions**: Real-world automated email outbox (Resend API) and automated critical escalation alerts (Discord).
5. **Vision AI Integration**: Multimodal Gemini capability that processes base64 uploaded invoices, damaged product images, or error screenshots.
6. **Voice AI Integration**: HTML-based Web Speech recognition and local speech synthesis supporting multilingual inputs (English, Hindi, Hinglish, Marathi).
7. **Predictive & Explainable AI**: Random Forest churn classification with model feature explainability metrics.
8. **Interactive SVG Collaboration Graph**: An animated 12-node network map showing active agents and self-correction routing in real-time.
9. **Supervisor Trust & Safety Pre-Audit Layer**: Instant sanitization block for prompt injection attacks or malicious behavior.
10. **Self-Healing Knowledge Base Curator**: Scanning unresolved negative tickets and automatically generating and indexing new FAQ help articles.
11. **CEO Analytics Desk & Copilot**: Executive Q&A desk answering strategic questions using LLM reasoning over SQLite data.
12. **Meeting Brief Report Generator**: Generates daily, weekly, or monthly executive briefing documents summarizing KPIs.

---

## 🎯 What This Project Does

When a customer sends a message, FlowAgent AI automatically:

1. **Understands the language** (English, Hindi, Hinglish, Marathi)
2. **Searches the knowledge base** semantically (RAG with ChromaDB + hybrid reranking)
3. **Detects sentiment** using a locally trained ML model (no external API)
4. **Drafts an empathetic response** tailored to the customer's mood
5. **Creates a support ticket** in the database with auto-assigned priority and category
6. **Qualifies the lead** if buying intent is detected (ML-scored: Hot / Warm / Cold)
7. **Updates customer analytics** — CLV, health score, churn risk
8. **Audits the final response** for tone, language compliance, and quality

**All 8 steps happen automatically from a single customer message.**

---

## 🏗️ Architecture

```
Customer Message (Web / Telegram / Embedded Widget)
         │
         ▼
┌─────────────────────────────────┐
│       FastAPI Backend           │  Port 8000
│  JWT Auth • Rate Limiting       │
│  REST API • WebHooks            │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────┐
│                  Agent Manager                      │
│                                                     │
│  🤖 Support Agent    → RAG Knowledge Base Search    │
│  ❤️  Customer Care   → Sentiment + Tone Drafting    │
│  🎫 Ticket Agent    → SQLite Ticket Creation        │
│  💼 Sales Agent     → Lead Scoring + Pitch          │
│  📈 Analytics Agent → CLV + Health Score Update     │
│  🕵️  Supervisor     → Final Audit + Compliance      │
└────────────────┬────────────────────────────────────┘
                 │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
┌────────┐  ┌────────┐  ┌────────────┐
│ChromaDB│  │SQLite  │  │scikit-learn│
│(Vector)│  │ (ORM)  │  │ ML Models  │
└────────┘  └────────┘  └────────────┘
         │
         ▼
┌─────────────────────────────────┐
│     Streamlit Dashboard         │  Port 8501
│  Dark-mode • Glassmorphic UI    │
│  Plotly Charts • Live Editing   │
└─────────────────────────────────┘
```

---

## 🛠️ Tech Stack — Why Each Was Chosen

| Layer | Technology | Reason |
|---|---|---|
| **AI Agent Orchestration** | Google Gemini 1.5 Flash | Fast, multimodal, supports multi-language prompts |
| **Embeddings** | Gemini `text-embedding-004` | High-quality semantic vectors for RAG |
| **Vector Database** | ChromaDB (local, persistent) | Zero-infra vector store, runs fully offline |
| **Machine Learning** | scikit-learn + joblib | 4 local models — fast inference, no API cost |
| **Relational Database** | SQLite + SQLAlchemy ORM | Zero-setup, file-based, production-ready ORM |
| **Backend API** | FastAPI + Uvicorn | Async, auto-docs (Swagger), production-grade |
| **Frontend** | Streamlit + Plotly | Rapid dashboard with interactive charts |
| **Auth** | Custom HMAC-SHA256 JWT | Zero-dependency, no JWT library needed |
| **Document Parsing** | pypdf + docx2txt | Supports PDF, Word, and plain text uploads |

---

## 📁 Project Structure

```
AI Business Operations/
│
├── run.py                   # ← START HERE: trains ML + boots backend + frontend
├── test_api.py              # Automated test suite for all components
├── requirements.txt         # All Python dependencies
├── Dockerfile               # Container build definition
├── docker-compose.yml       # App + PostgreSQL orchestration
│
├── backend/
│   ├── main.py              # All 25+ FastAPI endpoints
│   ├── agent_manager.py     # 6-agent pipeline (the core of the system)
│   ├── database.py          # SQLAlchemy models: Tickets, Leads, Customers, etc.
│   ├── vector_store.py      # ChromaDB + hybrid search + TF-IDF reranking
│   ├── security.py          # HMAC JWT, bcrypt passwords, token-bucket rate limiter
│   └── ml/
│       ├── train_models.py  # Generates synthetic data + trains all 4 models
│       ├── predictors.py    # Fast in-memory inference with rule-based fallbacks
│       ├── forecaster.py    # 7-day ticket volume forecasting
│       └── models/          # .joblib model files (auto-generated on first boot)
│
└── frontend/
    ├── app.py               # 10-section Streamlit dashboard
    ├── styles.css           # Dark-mode glassmorphic CSS
    └── widget/
        ├── chat-widget.js   # Embeddable JS chat widget (no framework needed)
        └── demo.html        # Widget demo page
```

---

## 🤖 The 6 AI Agents — In Detail

### Agent 1 — 🤖 Support Agent
- Queries the **ChromaDB knowledge base** using hybrid search (vector + keyword + TF-IDF reranking)
- Passes the retrieved context to **Gemini 1.5 Flash** to generate a factual, cited answer
- Injects the last 6 conversation turns as memory for context continuity

### Agent 2 — ❤️ Customer Care Agent
- Reads the **local sentiment prediction** (`Positive` / `Neutral` / `Negative`)
- Prompts Gemini to rewrite the response with appropriate tone:
  - Negative → empathetic apology
  - Positive → enthusiastic acknowledgment

### Agent 3 — 🎫 Ticket Agent
- Creates a **SQLite ticket** with auto-assigned:
  - **Category**: Billing / Technical / Account / Refund / General Inquiry (local ML)
  - **Priority**: High / Medium / Low (from sentiment)
  - **Escalation**: Flags for human review if risk score ≥ 75 or 3+ repeat complaints

### Agent 4 — 💼 Sales Agent
- Detects **buying intent** via keyword matching (price, demo, bulk, enterprise, etc.)
- If detected: runs the **local Lead Scorer ML model** → scores 0–100 → classifies Hot / Warm / Cold
- Generates a personalized sales pitch via Gemini with cross-sell and upsell suggestions

### Agent 5 — 📈 Analytics Agent
- Updates the **Customer 360° profile**: CLV, health score, touchpoint count
- Feeds operational metrics (ticket volume, sentiment distribution, automation rate)

### Agent 6 — 🕵️ Supervisor Agent
- Final Gemini call to audit the response for:
  - Professional tone
  - Correct language (Hinglish / Hindi / English / Marathi)
  - Compliance with company guidelines
- Returns the corrected final answer if needed

---

## 🧠 Machine Learning Models — 4 Local Models, Zero API Cost

All models are trained on **synthetically generated data** — no real user data required.

### Sentiment Classifier
- **Algorithm**: TF-IDF Vectorizer → Logistic Regression
- **Input**: Raw customer message text
- **Output**: `Positive` | `Neutral` | `Negative`
- **Used for**: Setting ticket priority, guiding Customer Care Agent tone

### Ticket Classifier
- **Algorithm**: TF-IDF Vectorizer → LinearSVC
- **Input**: Raw customer message text
- **Output**: `Billing` | `Technical` | `Account` | `Refund` | `General Inquiry`
- **Used for**: Auto-routing tickets to the correct department

### Lead Scorer
- **Algorithm**: Decision Tree Classifier
- **Input**: `page_views`, `time_on_site`, `form_submitted`, `email_type`, `interaction_count`
- **Output**: `Hot` | `Warm` | `Cold` (+ numeric score 0–100)
- **Used for**: Qualifying leads when buying intent is detected in a customer message

### Churn Predictor
- **Algorithm**: Random Forest Classifier (100 trees)
- **Input**: `negative_tickets`, `escalations`, `days_since_last_contact`, `CLV`, `health_score`
- **Output**: `High` | `Medium` | `Low` churn risk
- **Used for**: Customer 360° profile and proactive retention alerts

---

## 🌐 RAG Knowledge Base — Hybrid Search Engine

The knowledge base uses a **3-stage retrieval pipeline** for maximum accuracy:

```
Customer Query
      │
      ├─→ Stage 1: Vector Search   (ChromaDB semantic similarity via Gemini embeddings)
      │
      ├─→ Stage 2: Keyword Search  (local term-frequency matching across all chunks)
      │
      ├─→ Stage 3: Deduplication   (union of both result sets, remove duplicates)
      │
      └─→ Stage 4: TF-IDF Reranking (scikit-learn cosine similarity, pick top-N)
```

**Supported upload formats**: PDF, DOCX, TXT
**Chunk strategy**: 300-word chunks with 30-word overlap for context continuity

---

## 💻 How to Run

### Requirements
- Python 3.12+
- A Google Gemini API key (free at [aistudio.google.com](https://aistudio.google.com/app/apikey))

### Step 1 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 2 — Add your API key
Create a `.env` file in the root folder:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```
> **No API key?** The system boots in **Demo Mode** — all ML features (sentiment, lead scoring, churn) work fully. Only the Gemini LLM agents are offline.

### Step 3 — Start everything
```bash
python run.py
```

This single command:
- Trains all 4 ML models if not already trained (uses synthetic data, ~30 seconds)
- Starts the FastAPI backend on `http://localhost:8000`
- Starts the Streamlit dashboard on `http://localhost:8501`

### Step 4 — Open in your browser

| Service | URL |
|---|---|
| 🖥️ Dashboard | http://localhost:8501 |
| 📖 API Docs (Swagger) | http://localhost:8000/docs |
| ❤️ Health Check | http://localhost:8000/api/health |

---

## 🐳 Docker (Optional)

```bash
# Set your key and launch all services
GEMINI_API_KEY=your_key docker-compose up --build
```

Starts the app container + a PostgreSQL 15 database container.

---

## 🧪 Running Tests

```bash
python test_api.py
```

Tests verify:
- ✅ SQLite schema and CRUD operations
- ✅ Sentiment classification accuracy
- ✅ Ticket category classification
- ✅ Lead scoring pipeline
- ✅ ChromaDB vector queries
- ✅ FastAPI endpoint responses
- ✅ JWT authentication flow

---

## 📡 Key API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat` | Run the full 6-agent pipeline |
| `GET` | `/api/tickets` | List all support tickets |
| `PUT` | `/api/tickets/{id}` | Update a ticket |
| `GET` | `/api/leads` | List qualified leads |
| `GET` | `/api/customers/{email}` | Get customer 360° profile |
| `GET` | `/api/customers/{email}/churn-risk` | ML churn risk prediction |
| `GET` | `/api/analytics/roi` | Cost saved, hours saved, automation rate |
| `GET` | `/api/analytics/forecast` | 7-day ticket volume forecast |
| `POST` | `/api/analytics/copilot` | Ask the AI executive copilot |
| `POST` | `/api/kb/upload` | Upload a document to the knowledge base |
| `GET` | `/api/kb/search?q=` | Semantic search the knowledge base |
| `POST` | `/api/widget/chat` | Public endpoint for the embedded JS widget |
| `POST` | `/api/webhooks/telegram` | Telegram bot webhook |

Full Swagger docs available at `http://localhost:8000/docs`

---

## 🌟 What Makes This Different

| Typical Chatbot | FlowAgent AI |
|---|---|
| Single LLM call | 6 coordinated agents with specialized roles |
| No memory | Conversation history stored in SQLite |
| API-only ML | 4 local ML models — zero API cost for inference |
| Generic responses | Language-aware (English, Hindi, Hinglish, Marathi) |
| No business logic | Auto-creates tickets, scores leads, updates CRM |
| Simple keyword search | Hybrid vector + keyword + TF-IDF reranking |
| No analytics | Live ROI, churn prediction, forecasting |

---

## 🔐 Security Features

| Feature | Implementation |
|---|---|
| **Authentication** | HMAC-SHA256 signed JWT (zero external library) |
| **Password Storage** | bcrypt with auto-generated salts |
| **Authorization** | Role-based access: `Manager` vs `Agent` |
| **Rate Limiting** | Token-bucket: 5 req/sec per IP, burst of 10 |
| **Audit Logging** | All user and system actions logged to SQLite |

---

# 🔧 Backend — FlowAgent AI

The backend is a **FastAPI** application that exposes the full REST API, hosts the 6-agent AI pipeline, manages the SQLite database, and serves the ChromaDB vector knowledge base.

---

## 📁 Directory Structure

```
backend/
├── main.py              # FastAPI app entry point — all routes defined here
├── agent_manager.py     # AgentManager class — orchestrates the 6-agent pipeline
├── database.py          # SQLAlchemy models (Ticket, Lead, Customer, User, etc.)
├── vector_store.py      # ChromaDB RAG engine with hybrid search & TF-IDF reranking
├── security.py          # JWT tokens (HMAC), bcrypt password hashing, rate limiter
├── flowagent.db         # SQLite database file (auto-created)
│
├── chroma_db/           # ChromaDB persistent vector store (auto-created)
│
├── docs/                # Default knowledge base documents (auto-indexed at boot)
│   ├── company_faq.txt
│   └── refund_policy.txt
│
├── uploads/             # User-uploaded documents (stored & indexed into RAG)
│
└── ml/                  # Machine learning submodule
    ├── train_models.py
    ├── predictors.py
    ├── forecaster.py
    ├── churn_model.py
    └── models/          # Saved .joblib model files
```

---

## 🚀 Running the Backend

The backend is normally started by the root `run.py` script. To run it standalone:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

API docs (Swagger UI): [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🤖 Agent Manager (`agent_manager.py`)

The `AgentManager` class is the heart of the platform. It runs a sequential 6-agent pipeline for each customer query.

### Agent Pipeline

| Step | Agent | Technology | Action |
|---|---|---|---|
| 1 | **Support Agent** | Gemini LLM + ChromaDB RAG | Retrieves relevant KB context, generates answer |
| 2 | **Customer Care Agent** | Gemini LLM + local ML sentiment | Drafts an empathetic, tone-adjusted response |
| 3 | **Ticket Agent** | SQLite via SQLAlchemy | Creates ticket with category, priority, escalation check |
| 4 | **Sales Agent** | Keyword detection + local ML lead scorer | Qualifies leads, generates sales pitch |
| 5 | **Analytics Agent** | SQLAlchemy | Updates customer CLV, health score, and metrics |
| 6 | **Supervisor Agent** | Gemini LLM | Final audit: tone, language compliance, re-routing |

### Language Detection

The pipeline auto-detects the customer's language using a rule-based detector:

| Language | Detection Method |
|---|---|
| Hindi | Unicode range `\u0900-\u097F` |
| Marathi | Keyword pattern matching |
| Hinglish | Common Hindi-in-Latin keywords |
| English | Default fallback |

All agents receive the `detected_lang` and respond accordingly. The Supervisor Agent enforces language compliance on the final output.

### Conversation Memory

Each session maintains conversation history stored in the `ConversationTurn` SQLite table. The last 6 turns are injected as context into the Support Agent's prompt on each request.

---

## 🗄️ Database (`database.py`)

Uses **SQLAlchemy** with **SQLite** (default) or **PostgreSQL** (via Docker `DATABASE_URL`).

### Database Tables

| Table | Purpose |
|---|---|
| `users` | Platform user accounts (Agent / Manager roles) |
| `tickets` | Support tickets with sentiment, category, priority, escalation |
| `leads` | Qualified sales leads with ML scores and recommendations |
| `customers` | 360° customer profiles: CLV, health score, ticket history |
| `conversation_turns` | Full conversation history per session |
| `documents` | Metadata for files indexed into the RAG knowledge base |
| `system_config` | Key-value store for runtime configuration (API keys, etc.) |
| `audit_logs` | Full audit trail of all user and system actions |
| `system_alerts` | Active system alerts (escalations, anomalies) |
| `incoming_messages` | Omnichannel inbox (Web, Telegram, etc.) |

### Key Auto-logic in Ticket Creation

When a ticket is created via `add_ticket()`, the database layer automatically:
- Checks for repeat complaints from the same customer
- Calculates an escalation risk score
- Sets `escalated_to_human = True` if risk score ≥ 75 or 3+ repeat complaints

---

## 🧠 Vector Store — RAG Engine (`vector_store.py`)

### Embedding Model

Uses **Gemini `text-embedding-004`** for all document and query embeddings. The `FlexibleEmbeddingFunction` class implements ChromaDB's `EmbeddingFunction` interface.

### Document Ingestion

Supports three file formats:

| Format | Parser |
|---|---|
| `.txt` | Built-in Python file reader |
| `.pdf` | `pypdf` |
| `.docx` | `docx2txt` |

Documents are split into overlapping chunks (300 words, 30-word overlap) before indexing.

### Hybrid Search Pipeline

`query_knowledge_base(query, n_results=4)` executes a 4-step retrieval pipeline:

```
Query
  │
  ├─→ 1. Vector Search (ChromaDB semantic similarity)
  │
  ├─→ 2. Keyword Matching (local term-frequency search over all chunks)
  │
  ├─→ 3. Deduplication (union of both result sets)
  │
  └─→ 4. TF-IDF Cosine Reranking (scikit-learn, picks top-N)
```

This hybrid approach ensures both **semantic accuracy** and **keyword precision**, with reranking to surface the most relevant chunks to the agent.

---

## 🔐 Security (`security.py`)

### Custom JWT Tokens

Zero-dependency JWT-like tokens using Python's built-in `hmac` + `hashlib`:

- Header: `{"alg": "HS256", "typ": "JWT"}`
- Signature: HMAC-SHA256 with `SECRET_KEY`
- Expiry: 1 hour (configurable via `expires_in_seconds`)

### Password Hashing

Uses `bcrypt` with auto-generated salts. Falls back to SHA-256 comparison if bcrypt fails.

### Rate Limiter

Token-bucket algorithm implemented in `TokenBucketLimiter`:

- **Rate**: 5 tokens/second
- **Capacity**: 10 tokens (burst)
- **Scope**: Per client IP address
- **Excluded**: `/api/health`, `/docs`, `/openapi.json`

---

# 🖥️ Frontend — FlowAgent AI Dashboard & Chat Widget

The frontend consists of two parts:
1. **Streamlit Dashboard** (`app.py`) — a rich, dark-mode executive operations dashboard
2. **Embeddable JS Widget** (`widget/`) — a standalone JavaScript chat widget for embedding on any website

---

## 📁 Directory Structure

```
frontend/
├── app.py           # Streamlit multi-section dashboard application
├── styles.css       # Custom dark-mode glassmorphic CSS theme
└── widget/
    ├── chat-widget.js   # Self-contained JavaScript chat widget
    └── demo.html        # Standalone demo page for the widget
```

---

## 🚀 Running the Dashboard

The dashboard is normally started by the root `run.py` script. To run it standalone:

```bash
streamlit run frontend/app.py --server.port 8501
```

Access the dashboard at: [http://localhost:8501](http://localhost:8501)

---

## 🎨 Dashboard Sections

The Streamlit dashboard is organized into multiple tabs/sections, all connected to the FastAPI backend via REST API calls.

### 1. 🏠 Overview / Analytics
- Real-time KPI cards: Total Tickets, Open Tickets, Leads, CSAT Score
- Interactive Plotly bar charts: Ticket status distribution, sentiment breakdown
- Sentiment trend over time (line chart)

### 2. 💬 Live Agent Chat
- Chat interface to simulate a customer query
- Sends `POST /api/chat` to the backend
- Renders the **full 6-agent pipeline** as an expandable step-by-step flow:
  - Each agent's avatar, action, thoughts, and response
  - Metadata badges (sentiment, priority, lead status, etc.)
- Displays the final Supervisor-approved answer

### 3. 🎫 Ticket Manager
- Data grid of all support tickets from SQLite
- Inline editing: update Status, Priority, Assigned Agent, Response Draft
- Sends `PUT /api/tickets/{id}` on save
- Color-coded urgency indicators

### 4. 📊 Lead Pipeline
- Table of all qualified sales leads
- ML lead score displayed with Hot / Warm / Cold badges
- Cross-sell and upsell recommendations from the Sales Agent

### 5. 👥 Customer 360°
- Full customer profile view per email address
- Shows: CLV, health score, ticket history, last contact date
- Churn risk badge from the Churn Predictor ML model

### 6. 📚 Knowledge Base Manager
- Upload documents (PDF, DOCX, TXT) → auto-indexed into ChromaDB
- View KB stats: total chunks, number of unique documents
- Delete documents from the vector store
- Semantic search the knowledge base directly

### 7. 📈 ROI & Forecasting
- ROI metrics: tickets automated, hours saved, cost saved (INR)
- AI-generated ROI narrative via Gemini
- 7-day ticket volume forecast chart

### 8. 🤖 Executive Copilot
- Chat interface for the Manager to ask questions in natural language
- Powered by `POST /api/analytics/copilot`
- Example questions: *"Why is CSAT dropping?"*, *"Which department has the most escalations?"*

### 9. 📥 Omnichannel Inbox
- View incoming messages from all channels (Web Chat, Telegram)
- Process messages through the agent pipeline directly from the UI
- Filter by channel or status (Pending / Processed)

### 10. ⚙️ Settings
- Input Gemini API key (persisted to DB)
- View system configuration
- Retrain ML models with one click

---

## 🎨 Design System (`styles.css`)

The dashboard uses a custom dark-mode glassmorphic theme:

| Property | Value |
|---|---|
| **Background** | Deep dark `#0a0e1a` with subtle gradient |
| **Cards** | `rgba(255,255,255,0.05)` glass with `backdrop-filter: blur` |
| **Accent Color** | Electric blue `#00d4ff` |
| **Success** | Emerald `#00ff88` |
| **Warning** | Amber `#ffaa00` |
| **Danger** | Rose `#ff4444` |
| **Font** | System default (Streamlit) |
| **Borders** | `rgba(255,255,255,0.1)` subtle separators |

---

## 🌐 Embeddable Chat Widget (`widget/`)

### `chat-widget.js`

A self-contained JavaScript widget that can be embedded on any website (no React, no build step required).

**Features**:
- Floating chat button with pulse animation
- Smooth slide-up chat panel
- Connects to the `POST /api/widget/chat` backend endpoint
- Maintains session ID across the page session
- Auto-scrolls to latest message
- Responsive design, works on mobile

### Embedding on Your Website

Add these two lines to any HTML page:

```html
<script>
  window.FlowAgentConfig = {
    backendUrl: "http://localhost:8000"  // Change to your production URL
  };
</script>
<script src="http://localhost:8000/widget/chat-widget.js"></script>
```

The widget is also served as a static file by FastAPI at `/widget/chat-widget.js`.

### `demo.html`

A standalone demo page showing the widget integrated into a mock company website. Open directly in any browser:

```bash
# Open in your default browser (Windows)
start frontend\widget\demo.html
```

---

## 🔌 Backend Communication

The dashboard communicates exclusively with the FastAPI backend. The backend URL defaults to `http://localhost:8000` and can be configured in the Settings section.

All authenticated API calls include the JWT `Bearer` token stored in `st.session_state` after login.

### Session State Keys

| Key | Description |
|---|---|
| `st.session_state.token` | JWT access token after login |
| `st.session_state.role` | User role: `Manager` or `Agent` |
| `st.session_state.username` | Logged-in username |
| `st.session_state.chat_history` | Live chat messages list |
| `st.session_state.session_id` | Unique session ID for the conversation |
