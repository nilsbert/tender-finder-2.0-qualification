# Architecture Definition: Qualification Service

## Architectural Style: Workflow & Orchestration
The Qualification service manages the transition from data to decision:
- **State Machine Architecture**: Tenders progress through defined states (Pending, In Review, Qualified, Disqualified).
- **Consensus Integration**: Aggregates feedback from multiple stakeholders before final status change.
- **Sovereign Evidence**: Owns the `qualification_decisions`, `risk_assessments`, and `review_comments` tables.

## Technology Stack
- **Framework**: FastAPI (Async)
- **Workflow Engine**: Custom State Machine / Logic Layer
- **Database**: SQLite (Development) / MSSQL (Production)
- **Integration**: Consumes scores from the **Rating** service.

## Core Logic: The Qualification Workflow
1.  **Selection**: A user (Sascha) selects a high-rated tender for review.
2.  **Assessment**: Users perform structured risk and opportunity assessments based on AI insights.
3.  **Review Loop**: Optional phase for large bids requiring **Björn's** approval.
4.  **Decision**: Final status is set to `QUALIFIED` or `DISQUALIFIED`.
5.  **Handoff**: Notifies the **Dashboard** and **Distributing** services of the outcome.

## Decision Gates
- **Initial Filter**: Automatically flags tenders with scores < threshold as "Low Relevance".
- **Risk Gate**: Mandatory sign-off for tenders involving new technologies or high financial risk.
- **Capacity Gate**: Validation against current team utilization data (provided via Dashboard integration).

## UI Integration
Provides a **Qualification Workspace** (PDS-based) focused on deep-dive analysis, risk scoring, and comment threads for **Sascha**, **Björn**, and **Daniel**.
