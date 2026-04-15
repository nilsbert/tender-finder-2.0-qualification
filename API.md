# 🛠️ Public Interface: Qualification API

> **Base Path:** `/api/qualification`
> **Port:** 8002
> **OpenAPI Docs:** `http://localhost:8002/docs`

The Qualification MS provides the **decision gate** for tender evaluation and status assignment.

---

## 📡 Endpoints

### 1. GET /health
Health check endpoint.

#### Response (200)
```json
{ "status": "healthy" }
```

### 2. POST /api/qualification/evaluate
Evaluate a tender against qualification rules.

#### Request Body
```json
{
  "tender_id": "string",
  "sector": "IT",
  "scores": {
    "overall_score": 85.5,
    "title_score": 42.0
  }
}
```

#### Response (200)
```json
{
  "tender_id": "string",
  "status": "QUALIFIED",
  "passed_rules": 3,
  "failed_rules": 0,
  "confidence": 0.92
}
```

### 3. GET /api/qualification/status/{tender_id}
Fetch the qualification status of a specific tender.

### 4. POST /api/qualification/feedback
Submit human feedback on a qualification decision.

#### Request Body
```json
{
  "tender_id": "string",
  "decision": "confirm",
  "comment": "Looks like a strong opportunity"
}
```

---
*Maintained by the Tender Finder Architectural Board*
