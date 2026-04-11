
import pytest
import httpx
import uuid
import asyncio

BASE_URL = "http://localhost:8000"

@pytest.mark.asyncio
async def test_import_export_flow():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # Generate unique prefix for this test run
        run_id = uuid.uuid4().hex[:6]
        prefix = f"TEST_{run_id}_"
        print(f"Running test with prefix: {prefix}")
        
        kw1_term = f"{prefix}alpha"
        kw2_term = f"{prefix}beta"
        kw3_term = f"{prefix}gamma"
        
        # 1. Setup: Import Initial Set
        # We import 2 keywords: alpha, beta
        payload_1 = {
            "keywords": [
                {"term": kw1_term, "weight": 1.0, "type": "Sector"},
                {"term": kw2_term, "weight": 2.0, "type": "Sector"}
            ],
            "mode": "merge"
        }
        res = await client.post("/keywords/import", json=payload_1)
        assert res.status_code == 200, f"Import failed: {res.text}"
        summary = res.json()["summary"]
        assert summary["created"] >= 2
        
        # Verify Listing
        res_list = await client.get("/keywords/", params={"search": prefix})
        assert res_list.status_code == 200
        items = res_list.json()
        assert len(items) == 2
        terms = sorted([k["term"] for k in items])
        assert terms == sorted([kw1_term, kw2_term])
        
        # 2. Test Filters and Export
        # Filter by specific search (alpha) and export
        res_export = await client.get("/keywords/export", params={"search": f"{prefix}alpha"})
        assert res_export.status_code == 200
        export_data = res_export.json()
        assert len(export_data["keywords"]) == 1
        assert export_data["keywords"][0]["term"] == kw1_term
        
        # 3. Import Merge (Update + Add)
        # Update alpha weight to 5.0, Add gamma
        payload_2 = {
            "keywords": [
                {"term": kw1_term, "weight": 5.0, "type": "Sector"},
                {"term": kw3_term, "weight": 3.0, "type": "Sector"} # New
            ],
            "mode": "merge"
        }
        res = await client.post("/keywords/import", json=payload_2)
        assert res.status_code == 200
        summary = res.json()["summary"]
        # Alpha updated, Gamma created. Beta untouched (still in DB).
        assert summary["updated"] >= 1
        assert summary["created"] >= 1
        
        # Verify
        res_list = await client.get("/keywords/", params={"search": prefix})
        items = res_list.json()
        assert len(items) == 3 # alpha, beta, gamma
        alpha = next(k for k in items if k["term"] == kw1_term)
        assert alpha["weight"] == 5.0
        
        # 4. Import Sync (Delete)
        # Input only beta. Alpha and Gamma (matching search prefix?) - NO.
        # Sync deletes ANYTHING in DB that is not in the JSON.
        # DANGER: We cannot run "sync" mode safely on a shared DB if it deletes *everything* else.
        # The logic was:
        # for kw in existing_keywords: if kw not in input -> delete
        # This will wipe the ENTIRE database of keywords except what we upload.
        # We should NOT run this in a shared environment/integration test unless we are okay with wiping data.
        
        # SKIPPING SYNC TEST to protect user data.
        # Ideally, we should mock DB or have a "dry-run" flag.
        print("Skipping SYNC test to avoid wiping DB.")
        
        # Cleanup
        for k in items:
            await client.delete(f"/keywords/{k['id']}")
