# 🚀 Standalone Development Guide — Qualification Microservice

> **Last Updated:** 2026-04-15
> **Port:** 8013
> **Team Isolation:** ✅ Fully independent with graceful degradation.

---

## 🎯 The Golden Rule

> *As long as the API contract does not change, you can develop this service independently.*

---

## 🏗️ Three Execution Modes

### Mode 1: Local Development (SQLite)

```bash
git clone https://github.com/nilsbert/tender-finder-2.0-qualification.git
cd tender-finder-2.0-qualification

cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. python scripts/seed_demo.py   # Optional
PYTHONPATH=. python main.py
```

✅ **Result:** `http://localhost:8013`

### Mode 2: Docker with MSSQL

```bash
docker compose up --build
# Port 8013, MSSQL on 1436
```

### Mode 3: Full Stack

```bash
# From orchestrator root:
docker compose up --build
```

---

## 🔗 Dependencies

| Provider | Purpose | Required? |
| :--- | :--- | :--- |
| **Enriching MS** | Tender data | ❌ Graceful |
| **Rating MS** | Scoring data | ❌ Graceful |

> 💡 Qualification can be developed standalone. Mock tender/scoring data via seed scripts.

---
*Maintained by the Tender Finder Architectural Board.*
