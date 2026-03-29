# LLM Gateway — LLM-as-a-Service Platform

A production-ready, scalable LLM-as-a-Service platform that provides unified access to GPT-4, Llama 3, and Mistral models through a single OpenAI-compatible API with built-in authentication, rate limiting, usage tracking, billing, and streaming support.

## ✨ Features

- **Multi-Model Support**: OpenAI GPT-4/3.5, Meta Llama 3 (via Together AI), Mistral AI
- **OpenAI-Compatible API**: Drop-in replacement — same request/response format as OpenAI API
- **API Key Authentication**: Per-user API keys with JWT session support
- **Rate Limiting**: Configurable per-minute and per-day limits
- **Token Usage Tracking**: Per-user, per-model token and cost tracking
- **Streaming Responses**: Real-time SSE streaming for all supported models
- **Prompt Caching**: Redis-based caching for identical requests (saves tokens)
- **Model Fallback**: Automatic failover to next available model on errors
- **Request Logging**: Full logging of prompts, responses, tokens, and latency
- **Stripe Billing**: Pay-per-token billing with balance management
- **Dashboard**: Next.js frontend with usage charts, API key management, and playground
- **Docker**: Full Docker Compose setup with PostgreSQL, Redis, and Nginx

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│   Browser   │────▶│    Nginx    │────▶│  Next.js (3000) │
└─────────────┘     │  (80/443)   │     └─────────────────┘
                    │             │
                    │             │────▶┌─────────────────┐
                    └─────────────┘     │ FastAPI (8000)  │
                                        │                 │
                                        │ ┌─────────────┐ │
                                        │ │ LLM Router  │ │
                                        │ │ ┌─────────┐ │ │
                                        │ │ │ OpenAI  │ │ │
                                        │ │ │ Llama   │ │ │
                                        │ │ │ Mistral │ │ │
                                        │ │ └─────────┘ │ │
                                        │ └─────────────┘ │
                                        └────────┬────────┘
                                                 │
                                    ┌────────────┴────────────┐
                                    │                         │
                               ┌────▼─────┐         ┌────────▼──────┐
                               │PostgreSQL│         │  Redis Cache  │
                               └──────────┘         └───────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- API keys for: OpenAI, Together AI, Mistral (at least one)
- Stripe account (for billing)

### 1. Clone and configure

```bash
git clone https://github.com/yadavanujkumar/LLM-Gateway.git
cd LLM-Gateway
cp .env.example .env
```

Edit `.env` and fill in your API keys:

```env
SECRET_KEY=your-very-long-random-secret-key
OPENAI_API_KEY=sk-...
TOGETHER_API_KEY=...
MISTRAL_API_KEY=...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### 2. Start the platform

```bash
docker-compose up -d
```

This starts:
- PostgreSQL database on port 5432
- Redis on port 6379
- FastAPI backend on port 8000
- Next.js frontend on port 3000
- Nginx reverse proxy on port 80

### 3. Access the platform

- **Dashboard**: http://localhost
- **API Docs**: http://localhost/docs
- **ReDoc**: http://localhost/redoc

## 📡 API Reference

### Authentication

All API requests require an `Authorization` header:

```bash
Authorization: Bearer sk-your-api-key
```

### Endpoints

#### `POST /v1/chat/completions`

Create a chat completion (OpenAI-compatible).

```bash
curl http://localhost/v1/chat/completions \
  -H "Authorization: Bearer sk-your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Hello!"}
    ],
    "temperature": 0.7,
    "max_tokens": 512
  }'
```

**Streaming:**

```bash
curl http://localhost/v1/chat/completions \
  -H "Authorization: Bearer sk-your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Tell me a joke"}], "stream": true}'
```

#### `POST /v1/embeddings`

Create text embeddings.

```bash
curl http://localhost/v1/embeddings \
  -H "Authorization: Bearer sk-your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"model": "text-embedding-ada-002", "input": "The food was great!"}'
```

#### `GET /v1/models`

List all available models.

```bash
curl http://localhost/v1/models \
  -H "Authorization: Bearer sk-your-api-key"
```

#### `GET /v1/usage`

Get token usage and cost statistics.

```bash
curl "http://localhost/v1/usage?page=1&page_size=20" \
  -H "Authorization: Bearer sk-your-api-key"
```

#### `POST /auth/register`

Register a new user.

```bash
curl http://localhost/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepassword"}'
```

#### `POST /auth/login`

Login and get a JWT token.

```bash
curl http://localhost/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepassword"}'
```

### Available Models

| Model | Provider | Context | Input $/1K | Output $/1K |
|-------|----------|---------|------------|-------------|
| `gpt-4` | OpenAI | 8K | $0.030 | $0.060 |
| `gpt-4-turbo` | OpenAI | 128K | $0.010 | $0.030 |
| `gpt-3.5-turbo` | OpenAI | 16K | $0.0005 | $0.0015 |
| `llama-3.1-70b-instruct` | Meta (Together) | 131K | $0.0009 | $0.0009 |
| `llama-3.1-8b-instruct` | Meta (Together) | 131K | $0.0002 | $0.0002 |
| `mistral-large` | Mistral AI | 32K | $0.008 | $0.024 |
| `mistral-small` | Mistral AI | 32K | $0.002 | $0.006 |

## 🗂️ Project Structure

```
LLM-Gateway/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py             # App entry point, middleware setup
│   │   ├── config.py           # Settings via pydantic-settings
│   │   ├── database.py         # SQLAlchemy engine & session
│   │   ├── models/             # SQLAlchemy ORM models
│   │   │   ├── user.py         # users table
│   │   │   ├── usage.py        # usage table
│   │   │   └── log.py          # logs table
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   │   ├── chat.py         # Chat/embedding schemas
│   │   │   ├── user.py         # User/auth schemas
│   │   │   └── usage.py        # Usage/log schemas
│   │   ├── routers/            # FastAPI routers
│   │   │   ├── auth.py         # /auth endpoints
│   │   │   ├── chat.py         # /v1/chat/completions
│   │   │   ├── embeddings.py   # /v1/embeddings
│   │   │   ├── usage.py        # /v1/usage, /v1/logs
│   │   │   ├── models.py       # /v1/models
│   │   │   └── billing.py      # /billing endpoints
│   │   ├── services/           # Business logic
│   │   │   ├── auth.py         # Auth & JWT service
│   │   │   ├── cache.py        # Redis caching
│   │   │   ├── usage.py        # Usage tracking & cost calculation
│   │   │   ├── billing.py      # Stripe integration
│   │   │   └── llm/            # LLM provider services
│   │   │       ├── router.py   # Model routing + fallback
│   │   │       ├── openai_service.py
│   │   │       ├── llama_service.py
│   │   │       └── mistral_service.py
│   │   └── middleware/
│   │       ├── auth.py         # API key / JWT auth dependency
│   │       ├── logging.py      # Request logging middleware
│   │       └── rate_limit.py   # SlowAPI rate limiting
│   ├── migrations/
│   │   └── init.sql            # PostgreSQL schema
│   ├── alembic/                # Alembic migration files
│   ├── tests/
│   │   └── test_api.py         # Pytest tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # Next.js dashboard
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx        # Landing page
│   │   │   ├── auth/
│   │   │   │   ├── login/      # Login page
│   │   │   │   └── register/   # Registration page
│   │   │   └── dashboard/
│   │   │       ├── layout.tsx  # Dashboard sidebar layout
│   │   │       ├── page.tsx    # Overview + API key
│   │   │       ├── models/     # Model catalog
│   │   │       ├── playground/ # Prompt testing UI
│   │   │       ├── usage/      # Usage stats table
│   │   │       └── settings/   # Account settings
│   │   ├── lib/
│   │   │   ├── api.ts          # Axios client
│   │   │   ├── auth.ts         # Auth functions
│   │   │   └── llm.ts          # LLM API calls
│   │   └── types/index.ts      # TypeScript types
│   └── Dockerfile
├── nginx/
│   └── nginx.conf              # Reverse proxy config
├── docker-compose.yml
├── .env.example
└── README.md
```

## ⚙️ Configuration

All configuration is via environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing secret | ⚠️ Required |
| `DATABASE_URL` | PostgreSQL connection string | Auto-built from POSTGRES_* |
| `REDIS_URL` | Redis connection string | `redis://redis:6379` |
| `OPENAI_API_KEY` | OpenAI API key | — |
| `TOGETHER_API_KEY` | Together AI API key (for Llama) | — |
| `MISTRAL_API_KEY` | Mistral API key | — |
| `STRIPE_SECRET_KEY` | Stripe secret key | — |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret | — |
| `RATE_LIMIT_PER_MINUTE` | API requests per minute | `60` |
| `CACHE_TTL` | Cache TTL in seconds | `3600` |

## 🔧 Local Development

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # configure your .env

# Start with auto-reload
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local  # set NEXT_PUBLIC_API_URL

npm run dev   # starts on http://localhost:3000
```

### Run Tests

```bash
cd backend
python -m pytest tests/ -v
```

## 🐳 Docker

```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f backend

# Run database migrations manually
docker-compose exec backend alembic upgrade head

# Stop all services
docker-compose down

# Remove all data volumes
docker-compose down -v
```

## ☁️ Deployment

### AWS / GCP

1. **Build and push images** to ECR/Artifact Registry:

```bash
docker build -t llm-gateway-backend ./backend
docker build -t llm-gateway-frontend ./frontend
docker tag llm-gateway-backend <registry>/llm-gateway-backend:latest
docker push <registry>/llm-gateway-backend:latest
```

2. **Deploy** on ECS / GKE using the `docker-compose.yml` as a reference.

3. **Set up managed services**:
   - AWS RDS / Cloud SQL for PostgreSQL
   - AWS ElastiCache / Memorystore for Redis

4. **Configure SSL** via AWS ACM / Let's Encrypt and update Nginx config.

5. **Set environment variables** in your container platform's secrets manager.

## 🛡️ Security

- All API keys are hashed in the database (using bcrypt)
- API keys and JWT tokens expire appropriately
- Rate limiting prevents abuse
- CORS is configured to only allow frontend origins
- Security headers are set in Nginx
- Non-root Docker users
- Stripe webhook signature verification

## 📊 Monitoring

The platform exposes:
- `GET /health` — Health check endpoint
- Structured JSON logs via structlog
- Per-request latency in response headers (`X-Response-Time`)
- Request IDs (`X-Request-ID`)

## 📄 License

MIT
