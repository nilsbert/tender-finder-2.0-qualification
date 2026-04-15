# 🤝 Interaction Contracts

> **Service:** Qualification MS
> **Role:** Consumer & Provider
> **Last Updated:** 2026-04-15

---

## As Provider

### [Consumer] Dispatching MS
The Dispatching MS queries qualification status to determine which tenders to relay.

| Field | Contract |
| :--- | :--- |
| `tender_id` | Non-empty string. |
| `status` | One of: `PENDING`, `QUALIFIED`, `REJECTED`. |
| `confidence` | Float (0.0–1.0). |

---

## As Consumer

### [Provider] Enriching MS
Qualification receives enriched tender data.

| Expectation | Detail |
| :--- | :--- |
| `tender_id` | Non-empty, stable string. |
| `title` | Non-empty string. |

### [Provider] Rating MS
Qualification receives scoring data.

| Expectation | Detail |
| :--- | :--- |
| `total_score` | Float (0.0–100.0). |
| `title_score` | Float (0.0–100.0). |

---
*Maintained by the Tender Finder Architectural Board*
