from fastapi import APIRouter, BackgroundTasks, HTTPException
from rating.models import Keyword, KeywordCreate
from core.database import db
from core.feedback_service import FeedbackService

router = APIRouter(prefix="/qualification", tags=["qualification"])
feedback_service = FeedbackService()

@router.post("/rerate-not-enriched")
async def rerate_not_enriched(background_tasks: BackgroundTasks):
    """
    Triggers a background process to re-rate all tenders that have not been enriched/rated yet.
    """
    background_tasks.add_task(rerate_not_enriched_worker)
    return {"message": "Rerate process started in background"}

@router.post("/feedback/{tender_id}")
async def give_feedback(tender_id: str, direction: str):
    """
    Apply manual feedback (up/down) to a tender.
    """
    try:
        result = await feedback_service.apply_feedback(tender_id, direction)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
