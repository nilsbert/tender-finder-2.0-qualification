import asyncio
import os
import sys
from datetime import datetime
from sqlalchemy import text, select

# Add the parent directory to sys.path to allow imports from .core, rating, etc.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from .core.database import db
from .core.models import QualificationScore, TenderACL

async def seed():
    print("Seeding demo data into Qualification Microservice...")
    await db.init_db()
    
    # 1. Seed Keywords
    from rating.initial_data import get_initial_keywords
    keywords = get_initial_keywords()
    for kw in keywords[:20]: # Just first 20 for demo
        try:
            await db.create_keyword(kw)
            print(f"Added keyword: {kw.term}")
        except Exception:
             # Skip duplicates
             pass
            
    # 2. Seed Tenders ACL
    demo_tenders = [
        {
            "id": "tender_001",
            "title": "Cloud Migration for Public Sector",
            "description": "Large scale cloud migration project using Azure and AWS.",
            "full_text": "Detailed requirements for cloud migration...",
            "score": 85.5,
            "status": "rated",
            "source_system": "TED Europe"
        },
        {
            "id": "tender_002",
            "title": "AI-Driven Logistics Optimization",
            "description": "Implementing machine learning models for supply chain efficiency.",
            "full_text": "Supply chain optimization using Python and TensorFlow...",
            "score": 92.0,
            "status": "rated",
            "source_system": "Bund.de"
        },
        {
            "id": "tender_003",
            "title": "Cybersecurity Audit",
            "description": "Annual security audit and penetration testing.",
            "full_text": "Audit requirements for ISO 27001...",
            "score": 45.0,
            "status": "rated",
            "source_system": "SIMAP"
        }
    ]
    
    for t in demo_tenders:
        await db.upsert_tender_acl(t)
        print(f"Upserted Tender ACL: {t['id']}")
        
        # Also seed scores table
        async with db.get_session() as session:
            stmt = select(QualificationScore).where(QualificationScore.tender_id == t["id"])
            res = await session.execute(stmt)
            existing = res.scalar_one_or_none()
            if not existing:
                session.add(QualificationScore(tender_id=t["id"], score=t["score"], matched_keywords=[]))
            else:
                existing.score = t["score"]
            await session.commit()
            print(f"Updated Score for: {t['id']}")

    print("Seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed())
