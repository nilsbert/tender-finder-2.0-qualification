import pytest
import httpx
import uuid

BASE_URL = "http://localhost:8000"

@pytest.mark.asyncio
async def test_keyword_lifecycle():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        # 1. Scenario: Add a new keyword
        term = f"test-mobility-{uuid.uuid4().hex[:6]}" # Unique term for test run
        payload = {
            "term": term,
            "category": "sustainability",
            "weight": 3.5
        }
        response = await client.post("/keywords/", json=payload)
        assert response.status_code == 201
        data = response.json()
        keyword_id = data["id"]
        assert data["term"] == term
        assert data["category"] == "sustainability"
        assert data["weight"] == 3.5

        # 2. Scenario: Prevent duplicate keyword creation
        response_dup = await client.post("/keywords/", json=payload)
        assert response_dup.status_code == 400
        assert "already exists" in response_dup.json()["detail"]

        # 3. Scenario: Update the weight of an existing keyword
        update_payload = {
            "term": term,
            "category": "sustainability",
            "weight": 2.5
        }
        response_update = await client.put(f"/keywords/{keyword_id}", json=update_payload)
        assert response_update.status_code == 200
        assert response_update.json()["weight"] == 2.5

        # 4. Scenario: Change keyword category
        cat_update_payload = {
            "term": term,
            "category": "innovation",
            "weight": 2.5
        }
        response_cat = await client.put(f"/keywords/{keyword_id}", json=cat_update_payload)
        assert response_cat.status_code == 200
        assert response_cat.json()["category"] == "innovation"

        # 5. Scenario: Rename keyword term
        new_term = f"e-mobility-{uuid.uuid4().hex[:6]}"
        rename_payload = {
            "term": new_term,
            "category": "innovation",
            "weight": 2.5
        }
        response_rename = await client.put(f"/keywords/{keyword_id}", json=rename_payload)
        assert response_rename.status_code == 200
        assert response_rename.json()["term"] == new_term

        # Verify old term is gone from search (this is implicitly tested by the fact that we can create it again if we wanted, 
        # but let's check the list)
        list_response = await client.get("/keywords/")
        terms = [k["term"] for k in list_response.json()]
        assert new_term in terms
        assert term not in terms

        # 6. Scenario: Delete a keyword
        response_delete = await client.delete(f"/keywords/{keyword_id}")
        assert response_delete.status_code == 204

        # Verify it's gone
        response_get = await client.get(f"/keywords/{keyword_id}")
        assert response_get.status_code == 404
