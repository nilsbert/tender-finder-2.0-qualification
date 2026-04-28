"""
LEGACY COMPATIBILITY LAYER & AGGREGATE SERVICES
Now strictly independent (Option B).
"""
import logging
import asyncio
from typing import List, Tuple, Dict
from .models import Keyword, TenderACL
from core.database import db
from .application_service import RatingApplicationService

logger = logging.getLogger(__name__)

class RatingService:
    """
    Legacy service class maintained for backward compatibility.
    Delegates to RatingApplicationService.
    """
    
    @staticmethod
    async def rate_tender(tender: TenderACL) -> TenderACL:
        return await RatingApplicationService.rate_tender(tender)

    async def re_rate_all_tenders(self) -> dict:
        """
        Iterates over ALL tenders in the LOCAL ACL database, recalculates their score.
        To resync with monolith, a different sync process should be used.
        """
        try:
            keywords = await db.get_all_keywords()
            if not keywords:
                return {"status": "skipped", "message": "No keywords defined"}
            
            async with db.get_session() as session:
                from sqlalchemy import select
                from core.models import TenderACL as ORMTender
                result = await session.execute(select(ORMTender))
                tenders = result.scalars().all()
                
            sem = asyncio.Semaphore(10) # Process max 10 tenders at once
            
            async def process_one(t_orm):
                async with sem:
                    try:
                        # Convert ORM to Pydantic for the application service
                        tender = TenderACL(
                            internal_id=t_orm.id,
                            headline=t_orm.title or "",
                            description=t_orm.description or "",
                            full_text=t_orm.full_text,
                            score=t_orm.score
                        )
                        
                        if tender.enrichment_locked:
                            return False

                        # Use new application service
                        rated_tender = await RatingApplicationService.rate_tender(tender)
                        
                        # Update back to local ACL
                        await db.upsert_tender_acl({
                            "id": rated_tender.id,
                            "title": rated_tender.title,
                            "description": rated_tender.description,
                            "full_text": rated_tender.full_text,
                            "score": rated_tender.score,
                            "status": "rated"
                        })
                        return True
                    except Exception as loop_e:
                        logger.error(f"Error re-rating tender {t_orm.id}: {loop_e}")
                        return False

            tasks = [process_one(t_orm) for t_orm in tenders]
            results = await asyncio.gather(*tasks)
            
            updated_count = sum(1 for r in results if r)
            count = len(tenders)
            
            return {
                "status": "completed", 
                "total_processed": count, 
                "total_updated": updated_count
            }
            
        except Exception as e:
            logger.error(f"Failed to re-rate all tenders: {e}")
            raise e

# Singleton instance
rating_service = RatingService()
