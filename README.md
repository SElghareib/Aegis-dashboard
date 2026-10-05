# AI Workspace Platform

A production-style AI SaaS platform that connects your company's knowledge to automated workflows. Built as a comprehensive portfolio project demonstrating full-stack engineering, AI integration, and production-ready architecture.

## 🏗 Architecture

```
                    ┌────────────────────────────┐
                    │       Next.js Frontend     │
                    │                            │
                    │ Dashboard                  │
                    │ Knowledge Center           │
                    │ AI Assistant               │
                    │ Automations                │
                    │ Runs / Approvals           │
                    └──────────────┬─────────────┘
                                   │
                              REST / API
                                   │
                                   ▼
                    ┌────────────────────────────┐
                    │       Python Backend       │
                    │         FastAPI            │
                    ├────────────────────────────┤
                    │ Auth / Users / Workspaces  │
                    │ Business Logic             │
                    │ RAG API                    │
                    │ Agent API                  │
                    │ Automation API             │
                    │ Permissions                │
                    └───────┬───────────┬────────┘
                            │           │
                  ┌─────────┘           └─────────┐
                  ▼                               ▼
        ┌──────────────────┐             ┌──────────────────┐
        │ PostgreSQL       │             │ Vector Database  │
        │ Users            │             │ Documents        │
        │ Workspaces       │             │ Embeddings       │
        │ Tasks            │             │ Metadata         │
        │ Runs             │             └──────────────────┘
        │ Audit logs       │
        └──────────────────┘
```

## ✨ Features

### Core Capabilities
- **Multi-workspace architecture** with proper tenancy isolation
- **Role-based access control** (Owner, Admin, Member, Viewer)
- **Document management** with background indexing
- **RAG-powered knowledge search** with citations
- **AI agents** with tool execution
- **Automation workflows** with step-by-step execution
- **Human approval system** for sensitive actions
- **Complete audit logging** for compliance

### Technical Highlights
- JWT-based authentication
- PostgreSQL with pgvector for vector embeddings
- Redis for caching and task queues
- Async background processing
- Comprehensive API with OpenAPI docs
- Docker containerization
- CI/CD ready

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Using Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Local Development

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_workspace
export REDIS_URL=redis://localhost:6379/0
export SECRET_KEY=your-secret-key

# Run database migrations (tables are created automatically)
# Start the server
uvicorn app.main:app --reload --port 8000
```

#### Frontend Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

## 📁 Project Structure

```
/workspace
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── core/           # Config, database, security
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── routers/        # API endpoints
│   │   ├── services/       # Business logic
│   │   └── main.py         # Application entry point
│   ├── tests/              # Test suite
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile          # Backend container
├── src/                    # Next.js frontend
│   ├── app/               # App router pages
│   ├── components/        # React components
│   └── ...
├── docker-compose.yml      # Multi-container setup
├── Dockerfile.frontend    # Frontend container
└── README.md
```

## 🔑 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get token
- `GET /api/v1/auth/me` - Get current user

### Workspaces
- `GET /api/v1/workspaces/` - List user's workspaces
- `POST /api/v1/workspaces/` - Create workspace
- `GET /api/v1/workspaces/{id}` - Get workspace details
- `POST /api/v1/workspaces/{id}/documents/upload` - Upload document

### Knowledge
- `GET /api/v1/knowledge/{workspace_id}/documents` - List documents
- `DELETE /api/v1/knowledge/documents/{id}` - Delete document
- `POST /api/v1/knowledge/search` - Search knowledge base
- `POST /api/v1/knowledge/{workspace_id}/index/{document_id}` - Index document

### Agents & Runs
- `GET /api/v1/agents/{workspace_id}` - List agents
- `POST /api/v1/agents/{workspace_id}` - Create agent
- `POST /api/v1/agents/{workspace_id}/run` - Execute agent
- `GET /api/v1/agents/runs/{id}` - Get run details
- `GET /api/v1/agents/runs/{id}/steps` - Get execution trace

### Approvals
- `GET /api/v1/approvals/{workspace_id}` - List pending approvals
- `POST /api/v1/approvals/{id}/approve` - Approve/reject action

### Audit
- `GET /api/v1/audit/{workspace_id}` - Get audit logs

## 👥 Roles & Permissions

| Action | Viewer | Member | Admin | Owner |
|--------|--------|--------|-------|-------|
| Ask AI | ✓ | ✓ | ✓ | ✓ |
| View documents | ✓ | ✓ | ✓ | ✓ |
| Upload documents | — | ✓ | ✓ | ✓ |
| Create automation | — | ✓ | ✓ | ✓ |
| Approve actions | — | — | ✓ | ✓ |
| Manage members | — | — | — | ✓ |

## 🧪 Testing

```bash
cd backend

# Run unit tests
pytest

# Run with coverage
pytest --cov=app
```

## 🎯 Demo Flow

1. **Sign up** and create a workspace
2. **Upload documents** (policies, product docs, FAQs)
3. **Index documents** to make them searchable
4. **Ask questions** using the AI assistant
5. **Create an automation** workflow
6. **Execute agent** to investigate customer issues
7. **Review and approve** actions requiring human oversight
8. **View execution traces** and audit logs

## 🛠 Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** - Primary database
- **pgvector** - Vector similarity search
- **Redis** - Caching and task queues
- **Pydantic** - Data validation
- **JWT** - Authentication

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Framer Motion** - Animations

### DevOps
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **GitHub Actions** - CI/CD (configured)

## 📝 License

MIT License - see LICENSE file for details

## 🎓 Portfolio Context

This is **Project 3** in a three-part AI engineering portfolio:

1. **Project 1**: Qwen RAG Knowledge Engine - Retrieval and embeddings
2. **Project 2**: Agentic Automation Engine - Tool calling and orchestration  
3. **Project 3**: AI SaaS Platform - Full-stack production application

Together they demonstrate: AI + Backend + Frontend + Data + APIs + Systems + DevOps + Product thinking
"# Aegis-dashboard" 
