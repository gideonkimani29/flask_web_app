# 🚀 M-Pesa Daraja API — FastAPI Service

A **production-ready** FastAPI microservice for the **Safaricom M-Pesa Daraja API** with:
structured request handling, full error management, async DB persistence, and OAuth token caching.

## ✨ Features

- **STK Push** — Lipa Na M-Pesa Online (customer PIN prompts)
- **C2B** — Customer-to-Business URL registration & inbound payment processing
- **B2C** — Business-to-Customer disbursements (salaries, refunds, rewards)
- **Transaction Status** — Query any M-Pesa transaction
- **Account Balance** — Query shortcode account balance
- **OAuth Token Caching** — Async-safe, automatic refresh before expiry
- **Transaction Ledger** — SQLite/PostgreSQL audit trail for all transactions
- **Structured Logging** — JSON logs with correlation IDs per request
- **API Key Auth** — `X-API-Key` header middleware
- **Retry Logic** — Exponential backoff on Daraja network errors (tenacity)
- **OpenAPI Docs** — Swagger UI at `/docs`
- **Health Checks** — `/health` liveness + `/health/ready` readiness
- **Docker Ready** — Multi-stage Dockerfile + docker-compose

## 🗂️ Project Structure

```
mpesa_service/
├── app/
│   ├── api/v1/
│   │   ├── endpoints/
│   │   │   ├── stk.py          # STK Push endpoints
│   │   │   ├── c2b.py          # C2B endpoints
│   │   │   ├── b2c.py          # B2C endpoints
│   │   │   ├── query.py        # Status & balance queries
│   │   │   └── health.py       # Health checks
│   │   └── router.py
│   ├── core/
│   │   ├── config.py           # Pydantic-settings
│   │   ├── logging.py          # Structlog JSON logging
│   │   └── security.py         # API key auth
│   ├── db/
│   │   ├── models.py           # SQLAlchemy ORM models
│   │   └── session.py          # Async session factory
│   ├── services/
│   │   ├── auth.py             # OAuth token cache
│   │   ├── mpesa_client.py     # Daraja HTTP client
│   │   ├── stk.py              # STK business logic
│   │   ├── c2b.py              # C2B business logic
│   │   ├── b2c.py              # B2C business logic
│   │   └── query.py            # Query logic
│   ├── schemas/                # Pydantic request/response models
│   ├── middleware/             # Request logging, correlation IDs
│   └── main.py                 # FastAPI application factory
├── tests/
├── .env.example
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## ⚙️ Setup

### 1. Install
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure
```bash
cp .env.example .env
# Edit .env with your Daraja credentials
```

### 3. Run (Development)
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Run (Production Docker)
```bash
docker-compose up --build -d
```

## 🌐 API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/stk/push` | ✅ | Initiate STK Push |
| `POST` | `/api/v1/stk/callback` | ❌ | Safaricom STK callback |
| `POST` | `/api/v1/c2b/register-urls` | ✅ | Register C2B URLs |
| `POST` | `/api/v1/c2b/simulate` | ✅ | Simulate C2B (sandbox) |
| `POST` | `/api/v1/c2b/validate` | ❌ | Safaricom C2B validate |
| `POST` | `/api/v1/c2b/confirm` | ❌ | Safaricom C2B confirm |
| `POST` | `/api/v1/b2c/payment` | ✅ | Initiate B2C payment |
| `POST` | `/api/v1/b2c/result` | ❌ | Safaricom B2C result |
| `POST` | `/api/v1/query/transaction-status` | ✅ | Query transaction |
| `POST` | `/api/v1/query/account-balance` | ✅ | Query balance |
| `GET`  | `/api/v1/health` | ❌ | Liveness check |
| `GET`  | `/api/v1/health/ready` | ❌ | Readiness check |

## 🔐 Authentication
```
X-API-Key: your-api-key-here
```

## 🧪 Testing
```bash
pytest tests/ -v
```

## 📖 Docs
Navigate to `http://localhost:8000/docs` for the interactive Swagger UI.

## 🔧 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MPESA_CONSUMER_KEY` | ✅ | Daraja consumer key |
| `MPESA_CONSUMER_SECRET` | ✅ | Daraja consumer secret |
| `MPESA_LIPA_NA_MPESA_PASSKEY` | ✅ | STK Push passkey |
| `API_KEY` | ✅ | Service API key |
| `MPESA_ENVIRONMENT` | ✅ | `sandbox` or `production` |
| `DATABASE_URL` | ✅ | SQLAlchemy DB URL |
| `MPESA_STK_CALLBACK_URL` | ✅ | Public HTTPS callback |
| `MPESA_B2C_SECURITY_CREDENTIAL` | B2C | Encrypted initiator credential |
