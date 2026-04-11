# ⚖️ Qualification Microservice

The **Qualification** microservice determines if a Sourced Tender is worth pursuing based on its content and predefined sector-specific rules.

## 🎯 Responsibility
- Evaluate Tenders against threshold criteria.
- Assign a "Qualified" status to promising opportunities.
- Trigger the transition from the Sourcing domain to the Distribution domain.

## 🛠️ Tech Stack
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Logic**: Rule-based qualification engine.

## 🏁 Getting Started

### 👤 Human Path
1. **Navigate**: `cd qualification`
2. **Setup Venv**: `python -m venv .venv && source .venv/bin/activate`
3. **Install**: `pip install -r requirements.txt`
4. **Run Standalone**:
   ```bash
   python main.py
   ```
   The service will be available at `http://localhost:8002`. *(Note: Potential port conflict with Taxonomy)*.

### 🤖 Agent Path
1. **Entry Point**: `qualification/main.py`.
2. **Rules**: Check `qualification/core/rules.py` for qualification logic.
3. **Criteria**: Check `qualification/models/` for qualification threshold definitions.

## 📡 API Reference
- **OpenAPI Docs**: `http://localhost:8002/docs`
- **Health Check**: `GET /health`

## 🔗 Dependencies
- **Tender Core**: To update the qualification status of a tender.
