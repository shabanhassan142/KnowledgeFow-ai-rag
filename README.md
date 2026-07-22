<div align="center">

# ⚡ KnowledgeFlow AI

### *Enterprise RAG Knowledge Assistant*

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-FF6F61?style=for-the-badge&logo=datadog&logoColor=white)](https://www.trychroma.com/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Celery](https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)


<p align="center">
  <b>KnowledgeFlow AI</b> is an enterprise-grade Retrieval-Augmented Generation (RAG) platform. It allows organizations to index internal company documents (PDFs, DOCX, TXT, Markdown) into a high-performance vector store and query them via an AI assistant that delivers accurate, context-aware answers with verified source citations.
</p>

[Key Features](#-features) • [Tech Stack](#-tech-stack) • [Architecture](#-architecture) • [Installation](#-installation) • [API Reference](#-api-endpoints)

</div>

## ✨ Features

### 🔑 Authentication & Access Control
- **JWT Security**: Access and refresh token authentication flow with bcrypt password hashing.
- **Role-Based Access Control (RBAC)**: Distinct permissions for `admin` and `employee` roles.
- **User Profiles**: Profile customization, credential updates, and session management.

### 📚 Knowledge Base Management
- **Multi-Format Ingestion**: Supports `.pdf`, `.docx`, `.txt`, and `.md` files up to 25MB.
- **Drag & Drop Upload Zone**: Interactive upload area with animated queues and indexing feedback.
- **Automated Text Extraction & Chunking**: Overlapping sliding window text chunking tailored for dense semantic retrieval.
- **Document Status Badges**: Live tracking of document states (`Ready`, `Processing`, `Pending`, `Failed`).

### 🧠 Advanced RAG Pipeline
- **Local Embedding Engine**: On-device vector embeddings using `all-MiniLM-L6-v2` (384-dimensional dense vectors).
- **Vector Search**: ChromaDB vector store integration with cosine similarity distance ranking.
- **Verified Citations**: AI responses automatically link exact source document names, page numbers, and relevance match scores.
- **Conversational Memory**: Maintains chat context across multiple prompt turns per session.

### 💬 Production AI Chat Interface
- **Claude / ChatGPT UX**: Message cards, typing animations, and response generation timers.
- **Markdown & Code Highlighting**: Renders markdown tables, lists, inline code, and dedicated code blocks with a one-click **Copy Code** button.
- **Suggested Question Chips**: Pre-loaded starter questions for rapid knowledge retrieval.
- **Auto-Scrolling**: Smooth scroll transitions as new messages arrive.

### 📈 System Analytics & Admin Dashboard
- **Visual Analytics**: Interactive Recharts bar graphs with custom gradient fills and dark tooltips.
- **Storage Metrics**: Real-time tracking of vector storage consumption and indexed chunk totals.
- **User Management**: Admins can invite, activate, deactivate, or delete platform users.

---

## 🛠️ Tech Stack

| Category | Technology | Description |
| :--- | :--- | :--- |
| **Frontend Framework** | React 18 + Vite | Fast, modular single-page application |
| **Language** | TypeScript | Full type-safety across frontend interfaces |
| **Styling** | Tailwind CSS + Radix UI | Modern utility-first CSS design system |
| **State & Data Fetching** | React Query (TanStack Query) | Efficient client-side caching and mutations |
| **Animations** | Framer Motion | Smooth page transitions and micro-interactions |
| **Charts & Metrics** | Recharts | Responsive, animated data visualizations |
| **Backend Framework** | FastAPI (Python 3.9+) | Asynchronous, high-throughput REST API |
| **Database** | PostgreSQL | Relational database for users, sessions, and metadata |
| **ORM & Migrations** | SQLAlchemy 2.0 + Alembic | Type-safe database queries and migrations |
| **Vector Store** | ChromaDB | High-speed vector database for embeddings |
| **Task Queue** | Celery + Redis | Asynchronous background processing for file chunking |
| **Embeddings** | SentenceTransformers | Local 384-dim vector embedding generation |
| **LLM Provider** | OpenRouter / Mistral / OpenAI | Flexible API integration for modern LLMs |

---

## 🏗️ Architecture

```text
               ┌────────────────────────────────────────┐
               │             User Browser               │
               │   React + TypeScript + Tailwind CSS    │
               └───────────────────┬────────────────────┘
                                   │ HTTPS / REST
                                   ▼
               ┌────────────────────────────────────────┐
               │            FastAPI Backend             │
               │         JWT Auth & API Routes          │
               └───────┬───────────┬───────────┬────────┘
                       │           │           │
         ┌─────────────┘           │           └─────────────┐
         ▼                         ▼                         ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   PostgreSQL    │       │    ChromaDB     │       │  Redis / Celery │
│ Users, Sessions │       │  Vector Store   │       │ Background Jobs │
└─────────────────┘       └─────────────────┘       └─────────────────┘
                                   ▲                         ▲
                                   │                         │
                                   └───────────┬─────────────┘
                                               │
                                               ▼
                                    ┌────────────────────┐
                                    │    LLM Provider    │
                                    │  (OpenRouter/LLM)  │
                                    └────────────────────┘
```

---

## 🔄 RAG Pipeline Workflow

```text
 📥 Upload Document (PDF, DOCX, TXT, MD)
       │
       ▼
 📄 Extract Raw Text Content
       │
       ▼
 ✂️ Chunk Text into Overlapping Segments (500 chars / 50 overlap)
       │
       ▼
 🔢 Generate Dense Embeddings (SentenceTransformers all-MiniLM-L6-v2)
       │
       ▼
 💾 Store Embeddings & Metadata in ChromaDB
       │
       ├───────────────────────── RAG RETRIEVAL ─────────────────────────┐
       ▼                                                                 ▼
 ❓ User Asks Question                                           🔎 Similarity Search
       │                                                                 │
       ▼                                                                 ▼
 🎯 Top-K Context Chunks Retrieved <──────────────────────────────────────┘
       │
       ▼
 🤖 Construct Context-Enriched Prompt for LLM
       │
       ▼
 💬 Return AI Answer with Inline Verified Citations & Relevance Scores
```

---

## 📁 Folder Structure

```text
AI company knowledge assistant (RAG)/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/            # API Endpoints (Auth, Chat, Documents, Analytics)
│   │   ├── core/              # Config, Security, JWT, Dependencies
│   │   ├── db/                # Database Sessions & Base Model
│   │   ├── models/            # SQLAlchemy Data Models
│   │   ├── rag/               # Vector Store, Embedder, Retriever, Prompt Builder
│   │   ├── schemas/           # Pydantic Request/Response Schemas
│   │   ├── services/          # Business Logic (Chat, Document, Auth Services)
│   │   └── main.py            # FastAPI Entry Point
│   ├── alembic/               # Database Migration Scripts
│   ├── requirements.txt       # Python Dependencies
│   └── alembic.ini            # Migration Config
│
├── frontend/
│   ├── src/
│   │   ├── api/               # Axios API Clients
│   │   ├── components/        # UI Components (Layout, Chat, Dashboard, Shared)
│   │   ├── contexts/           # AuthContext, ThemeContext
│   │   ├── hooks/             # Custom React Query Hooks
│   │   ├── pages/             # Page Views (Dashboard, Chat, Documents, Analytics)
│   │   ├── types/             # TypeScript Type Definitions
│   │   ├── App.tsx            # Application Router
│   │   └── main.tsx           # React DOM Root Entry
│   ├── package.json           # Frontend Dependencies
│   └── vite.config.ts         # Vite Bundler Config
│
├── docker-compose.yml         # Container Orchestration
└── .env.example               # Environment Variables Template
```

---

## 🚀 Installation & Setup

### Prerequisites
- **Python**: `3.9+`
- **Node.js**: `18.0+`
- **PostgreSQL**: `14+`
- **Redis**: `6+`

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/knowledgeflow-ai.git
cd knowledgeflow-ai
```

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Configure Environment Variables
cp ../.env.example .env

# Run Database Migrations
alembic upgrade head

# Start FastAPI Server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Frontend Setup
```bash
# Open a new terminal and navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite Development Server
npm run dev
```

The application will be accessible at:
- **Frontend Dashboard**: [http://localhost:5173](http://localhost:5173)
- **FastAPI OpenAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🔑 Environment Variables

Create a `.env` file in the root directory:

| Variable | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | String | PostgreSQL Connection URI | `postgresql://postgres:password@localhost:5432/knowledge_assistant` |
| `REDIS_URL` | String | Redis Connection String | `redis://localhost:6379/0` |
| `JWT_SECRET_KEY` | String | Secret key for signing JWT tokens | `super-secret-jwt-token-key` |
| `JWT_ALGORITHM` | String | Hashing algorithm for JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Integer | Access token expiration duration | `60` |
| `LLM_PROVIDER` | String | LLM Provider backend | `openrouter` |
| `LLM_API_KEY` | String | API Key for LLM provider | `sk-or-v1-xxxxxxxxxxxx` |
| `EMBEDDING_MODEL` | String | HuggingFace embedding model | `all-MiniLM-L6-v2` |
| `CHROMA_DIR` | String | Directory path for ChromaDB vector storage | `./chroma_data` |

---

## 📡 API Endpoints

### Authentication (`/api/v1/auth`)
| Method | Endpoint | Description | Access |
| :--- | :--- | :--- | :--- |
| `POST` | `/login` | Authenticate user & return JWT tokens | Public |
| `POST` | `/register` | Register a new user account | Public |
| `GET` | `/me` | Get current user details | Authenticated |
| `POST` | `/logout` | Invalidate current user session | Authenticated |

### Knowledge Base Documents (`/api/v1/documents`)
| Method | Endpoint | Description | Access |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | List all uploaded documents with status filters | Authenticated |
| `POST` | `/upload` | Upload & index multiple document files | Authenticated |
| `GET` | `/{doc_id}/download` | Download raw document file | Authenticated |
| `DELETE` | `/{doc_id}` | Delete document and wipe vector chunks | Admin |

### AI Chat Assistant (`/api/v1/chat`)
| Method | Endpoint | Description | Access |
| :--- | :--- | :--- | :--- |
| `POST` | `/sessions` | Create a new chat session | Authenticated |
| `GET` | `/sessions` | List user conversation history | Authenticated |
| `POST` | `/sessions/{id}/messages` | Send question and trigger RAG pipeline | Authenticated |
| `GET` | `/sessions/{id}/messages` | Retrieve conversation message history | Authenticated |
| `DELETE` | `/sessions/{id}` | Delete a chat session | Authenticated |

---

## 💡 Example Conversation Flow

```text
User: What is our company's annual leave policy?

KnowledgeFlow AI:
Based on the company handbook ("rag tester.txt"), full-time employees are entitled to:
• 18 paid annual leaves per calendar year, accrued at 1.5 days per month.
• Unused annual leave can be carried forward up to a maximum of 10 days into the following year.
• Leave requests must be submitted through the portal at least 3 working days in advance.

──────────────────────────────────────────────────────────────────
📌 Verified Source Citations:
- rag tester.txt (Page 1, Section 2.1) — 73.5% match confidence
- rag tester.txt (Page 1, Section 2.5) — 70.4% match confidence
```

---

## ⚡ Performance & Scalability

- **Local Vector Ingestion**: Eliminates third-party embedding API costs and quota limits by computing 384-dimensional embeddings on-device using SentenceTransformers.
- **Asynchronous RAG Execution**: Non-blocking document text extraction and vector chunking via FastAPI's async thread pools.
- **SQL Indexing & Caching**: Optimized PostgreSQL queries with foreign key indexing for high-speed message retrieval.

---

## 🔮 Future Roadmap

- [ ] **Multi-Tenant Support**: Isolated workspaces for enterprise organizations.
- [ ] **Hybrid Search**: Combine BM25 keyword search with dense vector similarity.
- [ ] **Streaming Responses**: Real-time token streaming for AI message generation.
- [ ] **OCR Ingestion**: Support for scanned PDFs and image documents using Tesseract OCR.
- [ ] **Agentic Tools**: Autonomous web search and calculator integration.

---


