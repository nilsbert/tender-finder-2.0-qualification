from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from domains.rating.analysis_service import KeywordAnalysisService
from domains.rating.models import KeywordCreate

@pytest.mark.asyncio
async def test_analyze_tender_success():
    """Test successful keyword analysis."""
    # Mock DB
    mock_db = MagicMock()
    mock_db.get_tender = AsyncMock(return_value={
        "headline": "Test Tender",
        "description": "We need Machine Learning services."
    })
    mock_db.get_all_keywords = AsyncMock(return_value=[
        MagicMock(term="Existing")
    ])

    # Mock OpenAI
    mock_openai = MagicMock()
    mock_openai.generate_text = MagicMock(return_value='[{"term": "Machine Learning", "weight": 1.5, "type": "Service"}]')

    # Initialize Service manually with mocks patched
    with patch("domains.rating.analysis_service.db", mock_db), \
         patch("domains.rating.analysis_service.azure_openai_service", mock_openai):
        
        service = KeywordAnalysisService()
        suggestions = await service.analyze_tender("123")
        
        
        assert len(suggestions) == 1
        assert suggestions[0].term == "Machine-Learning"
        assert suggestions[0].weight == 1.5
        assert suggestions[0].type == "Service"

@pytest.mark.asyncio
async def test_analyze_tender_not_found():
    """Test analysis when tender is missing."""
    mock_db = MagicMock()
    mock_db.get_tender = AsyncMock(return_value=None)
    
    with patch("domains.rating.analysis_service.db", mock_db):
        service = KeywordAnalysisService()
        with pytest.raises(ValueError, match="Tender .* not found"):
            await service.analyze_tender("123")
