import logging
from sqlalchemy.future import select
from core.database import db
from core.models import Keyword, QualificationScore
import httpx
import os

logger = logging.getLogger(__name__)

async def rerate_not_enriched_worker():
    logger.info("Starting optimized rerate_not_enriched_worker")
    count = 0
    try:
        # 1. Fetch keywords from local DB
        async with db.get_session() as session:
            stmt = select(Keyword)
            result = await session.execute(stmt)
            keywords = result.scalars().all()
            
            if not keywords:
                logger.warning("No keywords defined. Skipping rerate.")
                return

        # 2. Fetch unrated tenders from backend API
        backend_url = os.getenv("BACKEND_URL", "http://backend:8000")
        async with httpx.AsyncClient() as client:
            # Need an endpoint on backend to fetch unrated tenders
            # Assuming /api/tenders/unrated exists or will be created
            try:
                resp = await client.get(f"{backend_url}/api/debug/tenders") # Using debug as placeholder
                tenders = resp.json() if resp.status_code == 200 else []
            except Exception as e:
                logger.error(f"Failed to fetch tenders from backend: {e}")
                tenders = []

        # 3. Score tenders
        for tender in tenders:
            if tender.get("score", 0.0) == 0.0:
                t_id = tender.get("id")
                title = tender.get("title") or ""
                description = tender.get("description") or ""
                search_text = (title + " " + description).lower()
                
                matched = []
                total_score = 0.0
                
                for kw in keywords:
                    if kw.term.lower() in search_text:
                        matched.append({"term": kw.term, "score": kw.weight})
                        total_score += kw.weight

                # 4. Save to local DB
                async with db.get_session() as session:
                    # Upsert
                    score_entry = await session.get(QualificationScore, t_id)
                    if not score_entry:
                        score_entry = QualificationScore(tender_id=t_id)
                        session.add(score_entry)
                    score_entry.score = total_score
                    score_entry.matched_keywords = matched
                
                # 5. Push score back to backend
                try:
                    # Assuming an endpoint to update tender score
                    await client.post(f"{backend_url}/api/debug/update_score/{t_id}", json={"score": total_score})
                except Exception as e:
                    logger.warning(f"Failed to push score back to backend for {t_id}: {e}")

                count += 1
                
        logger.info(f"Finished rerating. Updated {count} tenders.")
        
    except Exception as e:
        logger.error(f"Error in rerate_not_enriched_worker: {e}", exc_info=True)
