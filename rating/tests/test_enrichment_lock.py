import pytest

from domains.sourcing.tender_model import Tender
from domains.rating.models import Keyword
from domains.rating.services import RatingService, rating_service
from shared.database import db


@pytest.mark.asyncio
async def test_rate_tender_skips_locked(monkeypatch):
    tender = Tender(enrichment_locked=True, headline="cloud")

    async def fake_get_all_keywords():
        raise AssertionError("get_all_keywords should not be called for locked tenders")

    monkeypatch.setattr(db, "get_all_keywords", fake_get_all_keywords)

    result = await RatingService.rate_tender(tender)
    assert result is tender
    assert result.rating_total == 0.0


@pytest.mark.asyncio
async def test_rerate_skips_locked(monkeypatch):
    keywords = [Keyword(term="cloud", weight=2.0, category="tech")]
    updated = []

    async def fake_get_all_keywords():
        return keywords

    async def fake_upsert_tender(data):
        updated.append(data)
        return True

    def fake_iterator():
        return [
            {
                "internal_id": "t1",
                "headline": "cloud tender",
                "enrichment_locked": True
            },
            {
                "internal_id": "t2",
                "headline": "cloud tender",
                "enrichment_locked": False
            }
        ]

    monkeypatch.setattr(db, "get_all_keywords", fake_get_all_keywords)
    monkeypatch.setattr(db, "get_all_tenders_iterator", fake_iterator)
    monkeypatch.setattr(db, "upsert_tender", fake_upsert_tender)

    result = await rating_service.re_rate_all_tenders()

    assert result["total_processed"] == 2
    assert result["total_updated"] == 1
    assert len(updated) == 1
