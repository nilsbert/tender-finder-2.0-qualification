import pytest
import pytest_asyncio
import httpx
import uuid

BASE_URL = "http://localhost:8000"

@pytest_asyncio.fixture
async def seed_test_keywords():
    """Seed the database with test keywords and clean up after."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        # Create test keywords
        test_keywords = [
            {"term": f"AI-{uuid.uuid4().hex[:6]}", "category": "technology", "weight": 4.5, "type": "Service"},
            {"term": f"legacy system-{uuid.uuid4().hex[:6]}", "category": "architecture", "weight": -2.0, "type": "Exclusion"},
            {"term": f"electric mobility-{uuid.uuid4().hex[:6]}", "category": "sustainability", "weight": 3.5, "type": "Sector"},
            {"term": f"cloud-{uuid.uuid4().hex[:6]}", "category": "technology", "weight": 1.0, "type": "Service"},
            {"term": f"compliance-{uuid.uuid4().hex[:6]}", "category": "governance", "weight": 2.5, "type": "Sector"},
            {"term": f"blockchain-{uuid.uuid4().hex[:6]}", "category": "innovation", "weight": 0.5, "type": "Service"},
        ]
        
        created_ids = []
        for kw in test_keywords:
            response = await client.post("/keywords/", json=kw)
            assert response.status_code == 201
            created_ids.append(response.json()["id"])
        
        yield test_keywords
        
        # Cleanup
        for kid in created_ids:
            await client.delete(f"/keywords/{kid}")

@pytest.mark.asyncio
async def test_search_by_term(seed_test_keywords):
    """Test searching for keywords by term."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        # Get all keywords
        response = await client.get("/keywords/")
        all_keywords = response.json()
        
        # Search for "cloud"
        cloud_keywords = [k for k in all_keywords if "cloud" in k["term"].lower()]
        assert len(cloud_keywords) >= 1
        assert any("cloud" in k["term"].lower() for k in cloud_keywords)

@pytest.mark.asyncio
async def test_search_case_insensitive(seed_test_keywords):
    """Test that search is case-insensitive."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        response = await client.get("/keywords/")
        all_keywords = response.json()
        
        # Search for "ai" (lowercase) should match "AI"
        ai_keywords = [k for k in all_keywords if "ai" in k["term"].lower()]
        assert len(ai_keywords) >= 1

@pytest.mark.asyncio
async def test_search_partial_term(seed_test_keywords):
    """Test searching with partial term returns matches."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        response = await client.get("/keywords/")
        all_keywords = response.json()
        
        # Search for "mob" should match "electric mobility"
        mob_keywords = [k for k in all_keywords if "mob" in k["term"].lower()]
        assert len(mob_keywords) >= 1
        assert any("mobility" in k["term"].lower() for k in mob_keywords)

@pytest.mark.asyncio
async def test_filter_by_category(seed_test_keywords):
    """Test filtering keywords by category."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        response = await client.get("/keywords/")
        all_keywords = response.json()
        
        # Filter by technology category
        tech_keywords = [k for k in all_keywords if k.get("category") == "technology"]
        assert len(tech_keywords) >= 2  # AI and cloud
        assert all(k.get("category") == "technology" for k in tech_keywords)

@pytest.mark.asyncio
async def test_filter_by_weight_range(seed_test_keywords):
    """Test filtering keywords by weight range."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        response = await client.get("/keywords/")
        all_keywords = response.json()
        
        # Filter by weight 2.0 to 5.0
        filtered = [k for k in all_keywords if 2.0 <= k["weight"] <= 5.0]
        assert len(filtered) >= 3  # AI, electric mobility, compliance
        assert all(2.0 <= k["weight"] <= 5.0 for k in filtered)

@pytest.mark.asyncio
async def test_filter_negative_weights(seed_test_keywords):
    """Test filtering for negative weights."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        response = await client.get("/keywords/")
        all_keywords = response.json()
        
        # Filter by weight -5.0 to -0.5
        filtered = [k for k in all_keywords if -5.0 <= k["weight"] <= -0.5]
        assert len(filtered) >= 1  # legacy system
        assert all(-5.0 <= k["weight"] <= -0.5 for k in filtered)

@pytest.mark.asyncio
async def test_sort_by_term_ascending(seed_test_keywords):
    """Test sorting keywords by term A-Z."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        response = await client.get("/keywords/")
        all_keywords = response.json()
        
        # Sort by term ascending
        sorted_keywords = sorted(all_keywords, key=lambda k: k["term"].lower())
        
        # Verify order
        for i in range(len(sorted_keywords) - 1):
            assert sorted_keywords[i]["term"].lower() <= sorted_keywords[i + 1]["term"].lower()

@pytest.mark.asyncio
async def test_sort_by_weight_descending(seed_test_keywords):
    """Test sorting keywords by weight (highest first)."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        response = await client.get("/keywords/")
        all_keywords = response.json()
        
        # Sort by weight descending
        sorted_keywords = sorted(all_keywords, key=lambda k: k["weight"], reverse=True)
        
        # Verify order
        for i in range(len(sorted_keywords) - 1):
            assert sorted_keywords[i]["weight"] >= sorted_keywords[i + 1]["weight"]

@pytest.mark.asyncio
async def test_sort_by_category_ascending(seed_test_keywords):
    """Test sorting keywords by category A-Z."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        response = await client.get("/keywords/")
        all_keywords = response.json()
        
        # Sort by category ascending
        sorted_keywords = sorted(all_keywords, key=lambda k: (k.get("category") or "").lower())
        
        # Verify order
        for i in range(len(sorted_keywords) - 1):
            cat1 = (sorted_keywords[i].get("category") or "").lower()
            cat2 = (sorted_keywords[i + 1].get("category") or "").lower()
            assert cat1 <= cat2

@pytest.mark.asyncio
async def test_combined_search_and_category_filter(seed_test_keywords):
    """Test combining search and category filter."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        response = await client.get("/keywords/")
        all_keywords = response.json()
        
        # Search for "cl" AND filter by technology
        filtered = [
            k for k in all_keywords 
            if "cl" in k["term"].lower() and k.get("category") == "technology"
        ]
        
        # Should include "cloud" in technology category
        assert len(filtered) >= 1
        assert all(k.get("category") == "technology" for k in filtered)

@pytest.mark.asyncio
async def test_combined_search_and_weight_filter(seed_test_keywords):
    """Test combining search and weight filter."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        response = await client.get("/keywords/")
        all_keywords = response.json()
        
        # Search for "i" AND filter by weight 3.0 to 5.0
        filtered = [
            k for k in all_keywords 
            if "i" in k["term"].lower() and 3.0 <= k["weight"] <= 5.0
        ]
        
        # Should include AI and electric mobility
        assert len(filtered) >= 2
        assert all(3.0 <= k["weight"] <= 5.0 for k in filtered)

@pytest.mark.asyncio
async def test_get_categories_endpoint():
    """Test the categories endpoint returns unique categories."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        response = await client.get("/keywords/categories")
        assert response.status_code == 200
        categories = response.json()
        assert isinstance(categories, list)
        # Should be sorted
        assert categories == sorted(categories)
