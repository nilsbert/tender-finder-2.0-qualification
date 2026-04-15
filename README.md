# ⚖️ Qualification Microservice

> **Domain Type:** Supporting Domain
> **Port:** 8002 *(Note: shares port with Enriching in standalone mode — use Docker for isolation)*
> **Owner:** Tender Finder Team

---

## 1. Purpose

The Qualification Microservice determines if a sourced tender is **worth pursuing** based on its content and predefined sector-specific rules. It bridges the gap between raw scoring (Rating MS) and actionable distribution (Dispatching MS), applying rule-based qualification logic and AI-assisted analysis.

## 2. 🤖 Agent Context (CRITICAL)

- **Role**: Qualification Gate & Rule Engine.
- **Rules**:
  - Evaluates tenders against threshold criteria.
  - Assigns a "Qualified" status to promising opportunities.
  - Triggers the transition from the Scoring domain to the Distribution domain.
  - Contains its own embedded rating logic for backward compatibility.
- **Boundary**: Rule-based evaluation, qualification status management, and feedback collection.

## 3. Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Backend** | FastAPI (Python 3.11+) |
| **ORM** | SQLAlchemy 2.0 |
| **Database** | SQLite (Local) / Azure MSSQL (Prod) |
| **Frontend** | React + Vite (Qualification UI) |
| **AI** | Embedded AI analysis service |
| **Container** | Dockerfile included |

## 4. Getting Started

```bash
# 1. Navigate
cd qualification

# 2. Create & activate virtual environment
python -m venv .venv && source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Seed demo data (optional)
PYTHONPATH=. python scripts/seed_demo.py

# 5. Run the service
PYTHONPATH=. python main.py
```
The service will be available at `http://localhost:8002`.

## 5. API Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Health check |
| `POST` | `/api/qualification/evaluate` | Evaluate a tender against rules |
| `GET` | `/api/qualification/status/{id}` | Get qualification status |
| `POST` | `/api/qualification/feedback` | Submit qualification feedback |

→ Full details in [API.md](./API.md)

## 6. Project Structure

```
qualification/
├── main.py                     # FastAPI entry point
├── api/
│   └── routes.py               # REST endpoints
├── core/
│   ├── database.py             # DB engine & session
│   ├── scoring.py              # Qualification scoring
│   ├── worker.py               # Background processing
│   ├── feedback_service.py     # User feedback logic
│   └── models.py               # Core domain models
├── ai/
│   ├── models.py               # AI request/response models
│   └── services.py             # AI analysis service
├── rating/                     # Embedded rating subsystem
│   ├── routes.py               # Rating-specific endpoints
│   ├── services.py             # Rating orchestration
│   ├── analysis_service.py     # Rating analysis
│   ├── application_service.py  # Application layer
│   ├── initial_data.py         # Seed data
│   └── models.py               # Rating models
├── models/
│   └── orm.py                  # SQLAlchemy ORM models
├── scripts/
│   └── seed_demo.py            # Demo data seeding
├── ui/                         # React Admin UI
├── Dockerfile
└── requirements.txt
```

## 7. Dependencies

| Direction | Service | Relationship |
| :--- | :--- | :--- |
| **Upstream** | Enriching MS | Receives enriched tender data |
| **Upstream** | Rating MS | Receives scoring data |
| **Downstream** | Dispatching MS | Pushes qualified tenders for distribution |

→ Consumer contracts in [CONTRACTS.md](./CONTRACTS.md)

---
*Maintained by the Tender Finder Architectural Board*
