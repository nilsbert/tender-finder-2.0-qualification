"""
Application Service for Rating.
Orchestrates domain logic and infrastructure.
Now strictly independent (Option B).
"""
import logging
from typing import List, Dict, Optional
from .models import Keyword as LocalKeyword, TenderACL
from .core.database import db
from .core.scoring import ScoringPolicy, Keyword as DomainKeyword, MatchLocation

logger = logging.getLogger(__name__)

class RatingApplicationService:
    """
    Application Service for the Qualification Microservice.
    Uses local scoring logic and database persistence.
    """
    
    @staticmethod
    async def rate_tender(tender: TenderACL) -> TenderACL:
        """
        Calculate rating for a single tender using domain logic.
        """
        try:
            if tender.enrichment_locked:
                return tender
                
            # 1. Get Keywords from local DB
            local_keywords = await db.get_all_keywords()
            
            if not local_keywords:
                logger.warning(f"No keywords found in DB while rating tender {tender.id}. Score will be 0.0.")
                return tender
            
            # 2. Convert to Domain Keywords for the ScoringPolicy
            domain_keywords = []
            for kw in local_keywords:
                domain_keywords.append(DomainKeyword(
                    term=kw.term,
                    weight=kw.weight,
                    type=kw.type,
                    sub_type=kw.sub_type,
                    sub_category=kw.sub_category,
                    category=kw.category
                ))
            
            # 3. Use local Scoring Logic
            logger.debug(f"Rating tender {tender.id} with {len(domain_keywords)} keywords")
            scoring_result = ScoringPolicy.calculate_score(
                tender_title=tender.title,
                tender_description=tender.description,
                tender_full_text=tender.full_text or "",
                keywords=domain_keywords
            )
            
            # 4. Apply results back to TenderACL
            tender.rating_total = float(scoring_result.total_score)
            tender.rating_title = float(scoring_result.title_score)
            tender.score = tender.rating_total # Local alias for scoring compatibility
            
            # Convert matches to local format
            tender.matched_keywords = [
                {
                    "term": m.keyword_term,
                    "location": m.location.value,
                    "score": m.score_impact
                }
                for m in scoring_result.matches
            ]
            
            return tender
            
        except Exception as e:
            import traceback
            logger.error(f"Failed to rate tender {tender.id}: {e}\n{traceback.format_exc()}")
            return tender

# Singleton instance
rating_service = RatingApplicationService()
