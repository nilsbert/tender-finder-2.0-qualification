import logging
import json
from datetime import datetime
from typing import List, Dict, Any

from .core.database import db
from .core.models import QualificationScore
import httpx
import os

logger = logging.getLogger(__name__)

class FeedbackService:
    def __init__(self):
        self.backend_url = os.getenv("BACKEND_URL", "http://backend:8000")

    async def apply_feedback(self, tender_id: str, direction: str) -> Dict[str, Any]:
        if direction not in ['up', 'down']:
            raise ValueError("Direction must be 'up' or 'down'")

        async with db.get_session() as session:
            score_entry = await session.get(QualificationScore, tender_id)
            if not score_entry:
                score_entry = QualificationScore(tender_id=tender_id, score=0.0, matched_keywords=[])
                session.add(score_entry)

            keywords = score_entry.matched_keywords or []
            new_keywords = []
            shift = 0.5 if direction == 'up' else -0.5
            
            for kw in keywords:
                if isinstance(kw, str):
                    kw = {"term": kw, "score": 0.0}
                
                old_score = kw.get('score', 0.0)
                new_score = max(-5.0, min(5.0, old_score + shift))
                new_keywords.append({"term": kw['term'], "score": new_score})
            
            # AI logic from backend currently omitted or we can call backend AI endpoint
            
            score_entry.matched_keywords = new_keywords
            score_entry.score = sum(k['score'] for k in new_keywords)
            
            # Flush changes
            await session.commit()
            
            # Push back to backend
            async with httpx.AsyncClient() as client:
                try:
                    await client.post(f"{self.backend_url}/api/debug/update_score/{tender_id}", json={"score": score_entry.score})
                except Exception as e:
                    logger.warning(f"Failed to sync score for {tender_id}")

            return {
                "tender_id": tender_id,
                "new_score": score_entry.score,
                "keywords_count": len(new_keywords),
                "feedback_given": True
            }
