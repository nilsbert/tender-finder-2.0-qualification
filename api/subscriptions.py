from fastapi import APIRouter, Depends, HTTPException, Query
from core.database import db
from sqlalchemy import select, delete, func
from core.models import Keyword as ORMKeyword
from core.models import UserSubscription as ORMSubscription
from pydantic import BaseModel
from typing import List, Optional
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class SubscriptionItem(BaseModel):
    entity_id: str
    frequency: str


class SubscriptionUpdatePayload(BaseModel):
    items: List[SubscriptionItem]


@router.get("/master-data")
async def get_master_data():
    """
    Returns distinct taxonomy sub_types grouped by type (Sector / Service).
    Each item represents a high-level practice or sector that users can subscribe to.
    Exclusions are intentionally excluded from the subscription UI.
    """
    try:
        async with db.get_session() as session:
            result = await session.execute(select(ORMKeyword))
            keywords = result.scalars().all()

            # Collect distinct sub_types per top-level type
            seen: dict[str, set] = {"Sector": set(), "Service": set()}
            for kw in keywords:
                if kw.type in seen and kw.sub_type:
                    seen[kw.type].add(kw.sub_type)

            data = {
                "sectors": [
                    {
                        "id": sub_type,          # stable, human-readable ID
                        "name": sub_type,
                        "description": "",
                        "category": "sectors",
                    }
                    for sub_type in sorted(seen["Sector"])
                ],
                "services": [
                    {
                        "id": sub_type,
                        "name": sub_type,
                        "description": "",
                        "category": "services",
                    }
                    for sub_type in sorted(seen["Service"])
                ],
            }

            return data
    except Exception as e:
        logger.error(f"Error fetching master data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch master data: {str(e)}")


@router.get("/subscriptions/me")
async def get_my_subscriptions(email: str = Query(..., description="Email of the user")):
    """Retrieve active subscriptions for the specified email."""
    try:
        async with db.get_session() as session:
            result = await session.execute(
                select(ORMSubscription).where(ORMSubscription.email == email)
            )
            subs = result.scalars().all()
            return [
                {
                    "entity_id": s.entity_id,
                    "frequency": s.frequency
                }
                for s in subs
            ]
    except Exception as e:
        logger.error(f"Error fetching subscriptions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch subscriptions: {str(e)}")


@router.put("/subscriptions/me")
async def update_my_subscriptions(email: str, payload: SubscriptionUpdatePayload):
    """Replace all subscriptions for the specified email."""
    try:
        async with db.get_session() as session:
            # Delete existing subscriptions
            await session.execute(
                delete(ORMSubscription).where(ORMSubscription.email == email)
            )
            
            # Add new ones
            for item in payload.items:
                sub = ORMSubscription(
                    id=str(uuid.uuid4()),
                    email=email,
                    entity_id=item.entity_id,
                    frequency=item.frequency
                )
                session.add(sub)
                
            await session.commit()
            return {"status": "success", "message": f"Updated {len(payload.items)} subscriptions."}
    except Exception as e:
        logger.error(f"Error updating subscriptions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update subscriptions: {str(e)}")
