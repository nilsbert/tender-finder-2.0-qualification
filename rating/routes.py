from fastapi import APIRouter, HTTPException, status, Depends
import logging
from typing import List
from .models import Keyword, KeywordCreate
from .core.database import db, DuplicateKeywordError
from sqlalchemy import text

# Local logger
logger = logging.getLogger(__name__)

# Simple Admin Auth stub - in a real microservice, this would be handled by a shared security lib or API Gateway
async def get_admin_user():
    # Placeholder for actual admin check (e.g. JWT roles)
    return {"role": "admin"}

router = APIRouter(prefix="/keywords", tags=["Keywords"])

from .analysis_service import keyword_analysis_service
from pydantic import BaseModel
from typing import Optional

class AnalyzeRequest(BaseModel):
    prompt: Optional[str] = None

class StatelessRateRequest(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    full_text: Optional[str] = None
    enrichment_locked: bool = False

@router.get("/", response_model=List[Keyword])
async def list_keywords():
    """Retrieve all keywords."""
    return await db.get_all_keywords()

@router.get("/categories", response_model=List[str])
async def list_categories():
    """Retrieve all unique keyword categories."""
    return await db.get_categories()

@router.get("/tree")
async def get_keyword_tree():
    """Retrieve keyword tree structure (type -> sub_type hierarchy)."""
    keywords = await db.get_all_keywords()
    
    # Build tree structure
    tree = {}
    for kw in keywords:
        kw_type = kw.type or "Service"
        sub_type = kw.sub_type or "Unassigned"
        
        if kw_type not in tree:
            tree[kw_type] = set()
        tree[kw_type].add(sub_type)
    
    # Convert sets to sorted lists
    result = {
        type_name: sorted(list(subtypes))
        for type_name, subtypes in tree.items()
    }
    
    return result

    return result


@router.get("/distribution")
async def get_score_distribution(
    search: Optional[str] = None,
    website: Optional[str] = None,
    keyword: Optional[str] = None,
    rating_category: Optional[str] = None
):
    """Retrieve score distribution for the dashboard."""
    return await db.get_score_distribution(
        search_text=search,
        website=website,
        keyword=keyword,
        rating_category=rating_category
    )

@router.post("/", response_model=Keyword, status_code=status.HTTP_201_CREATED)
async def create_keyword(keyword: KeywordCreate):
    """Create a new keyword."""
    try:
        return await db.create_keyword(keyword)
    except DuplicateKeywordError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{keyword_id}", response_model=Keyword)
async def update_keyword(keyword_id: str, keyword_input: KeywordCreate):
    """Update an existing keyword."""
    # Auto-correct weight based on type (for drag-and-drop feature)
    if keyword_input.type == 'Exclusion' and keyword_input.weight > 0:
        keyword_input.weight = -keyword_input.weight
    elif keyword_input.type in ['Service', 'Sector'] and keyword_input.weight < 0:
        keyword_input.weight = -keyword_input.weight
    
    updated = await db.update_keyword(keyword_id, keyword_input)
    if not updated:
        raise HTTPException(status_code=404, detail="Keyword not found")
    return updated

@router.delete("/{keyword_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_keyword(keyword_id: str):
    """Delete a keyword."""
    success = await db.delete_keyword(keyword_id)
    if not success:
        raise HTTPException(status_code=404, detail="Keyword not found")
    return

@router.delete("/admin/purge-all", status_code=status.HTTP_204_NO_CONTENT)
async def purge_all_keywords():
    """Delete ALL keywords. Use with caution."""
    # Simplified SQL purge for local MS
    async with db.get_session() as session:
        await session.execute(text("DELETE FROM keywords"))
    return

@router.post("/upload/initial", status_code=status.HTTP_201_CREATED)
async def upload_initial_keywords():
    """Batch upload initial set of 100+ german keywords for IT/Consulting."""
    from .initial_data import get_initial_keywords
    
    initial_keywords = get_initial_keywords()
    created_count = 0
    errors = []
    
    for kw in initial_keywords:
        try:
            # We check for duplicates inside create_keyword logic usually,
            # but here we can just try-catch.
            await db.create_keyword(kw)
            created_count += 1
        except DuplicateKeywordError:
            # Skip duplicates silently or log them
            pass
        except Exception as e:
            errors.append(f"Failed to add {kw.term}: {str(e)}")
            
    return {
        "message": f"Successfully added {created_count} keywords.",
        "skipped": len(initial_keywords) - created_count,
        "errors": errors
    }

@router.post("/rerate-all")
async def rerate_all_tenders(_ = Depends(get_admin_user)):
    """Trigger re-calculation of scores for ALL tenders in the database."""
    from .application_service import rating_service
    result = await rating_service.re_rate_all_tenders()
    return result

@router.post("/analyze/{tender_id}", response_model=List[KeywordCreate])
async def analyze_tender_keywords(tender_id: str, request: AnalyzeRequest = None):
    """
    Analyze a tender's text and suggest keywords.
    """
    prompt = request.prompt if request else None
    print(f"DEBUG: Analyzing tender_id={tender_id}")
    try:
        suggestions = await keyword_analysis_service.analyze_tender(tender_id, prompt_override=prompt)
        return suggestions
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/rate/{tender_id}")
async def rate_tender_manually(tender_id: str, _ = Depends(get_admin_user)):
    """Manually trigger scoring for a specific tender in the ACL."""
    try:
        # 1. Fetch from ACL
        tender_orm = await db.get_tender_acl(tender_id)
        if not tender_orm:
            raise HTTPException(status_code=404, detail="Tender not found in Qualification ACL")
            
        # 2. Convert to TenderACL Pydantic
        from .models import TenderACL
        tender = TenderACL(
            internal_id=tender_orm.id,
            headline=tender_orm.title,
            description=tender_orm.description,
            full_text=tender_orm.full_text,
            enrichment_locked=tender_orm.enrichment_locked
        )
        
        # 3. Rate
        from .application_service import RatingApplicationService
        rated_tender = await RatingApplicationService.rate_tender(tender)
        
        # 4. Save back to ACL
        await db.upsert_tender_acl({
            "id": rated_tender.id,
            "title": rated_tender.title,
            "description": rated_tender.description,
            "full_text": rated_tender.full_text,
            "score": rated_tender.score,
            "status": "rated"
        })
        
        return {"message": "Tender rated successfully", "tender_id": tender_id, "new_score": rated_tender.score}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to rate tender {tender_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to rate tender: {str(e)}")

@router.post("/rate-stateless")
async def rate_tender_stateless(request: StatelessRateRequest):
    """
    Stateless rating endpoint for external services (e.g. monolith crawler).
    Calculates score based on provided text without persisting anything.
    """
    try:
        # Avoid circular import by moving inside if needed, or use existing models
        from .models import TenderACL
        tender = TenderACL(
            internal_id=request.id or "stateless",
            headline=request.title or "",
            description=request.description or "",
            full_text=request.full_text or "",
            enrichment_locked=request.enrichment_locked
        )
        
        from .application_service import RatingApplicationService
        rated_tender = await RatingApplicationService.rate_tender(tender)
        
        # Return the rating results
        return {
            "id": rated_tender.id,
            "score": rated_tender.score,
            "rating_total": rated_tender.rating_total,
            "rating_title": rated_tender.rating_title,
            "matched_keywords": rated_tender.matched_keywords
        }
    except Exception as e:
        logger.error(f"Stateless rating failed: {e}")
        raise HTTPException(status_code=500, detail=f"Rating failed: {str(e)}")

# --- Import / Export ---

from fastapi import UploadFile, File, Form, Query
from fastapi.responses import Response
import json
import yaml
from .models import KeywordYamlModel, KeywordImportResult, KeywordImportSummary

@router.get("/export", response_class=Response)
async def export_keywords_yaml():
    """Download all keywords as a YAML file."""
    keywords = await db.get_all_keywords()
    
    # Convert to pure dicts for cleaner YAML
    # We strip ID and created_at for export to allow clean re-import
    export_data = {
        "keywords": [
            {
                "term": k.term,
                "weight": k.weight,
                "type": k.type,
                "sub_type": k.sub_type,
                "sub_category": k.sub_category,
                "category": k.category
            }
            for k in keywords
        ]
    }
    
    yaml_str = yaml.dump(export_data, sort_keys=False, allow_unicode=True)
    
    return Response(
        content=yaml_str,
        media_type="application/x-yaml",
        headers={"Content-Disposition": 'attachment; filename="keywords_export.yaml"'}
    )

@router.post("/import", response_model=KeywordImportResult)
async def import_keywords_file(
    file: UploadFile = File(...),
    dry_run: bool = Query(True, description="If true, only returns a diff summary without making changes."),
    delete_missing: bool = Query(False, description="If true, deletes keywords in DB that are missing from YAML (Sync mode).")
):
    """
    Import keywords from YAML or JSON file.
    Supports Dry Run and Sync/Merge modes.
    """
    filename = file.filename or ""
    if filename and not filename.endswith((".yaml", ".yml", ".json")):
        raise HTTPException(status_code=400, detail="Invalid file format. Must be .yaml, .yml, or .json")
    
    try:
        content = await file.read()
        data = None

        if filename.endswith(".json"):
            data = json.loads(content.decode("utf-8"))
        else:
            try:
                data = yaml.safe_load(content)
            except yaml.YAMLError:
                data = json.loads(content.decode("utf-8"))
        
        # Validate structure using Pydantic
        try:
            parsed = KeywordYamlModel(**data)
        except Exception as e:
             raise HTTPException(status_code=400, detail=f"Invalid keywords schema: {str(e)}")
             
        uploaded_keywords = parsed.keywords
        current_keywords = await db.get_all_keywords()
        
        # Build Maps for comparison (normalize term to lowercase for checking existence)
        current_map = {k.term.lower(): k for k in current_keywords}
        uploaded_map = {k.term.lower(): k for k in uploaded_keywords}
        
        created = []
        updated = []
        deleted = []
        
        # Identify Creates and Updates
        for up_kw in uploaded_keywords:
            term_key = up_kw.term.lower()
            if term_key not in current_map:
                created.append(up_kw)
            else:
                # Check for changes
                existing = current_map[term_key]
                if (existing.weight != up_kw.weight or 
                    existing.type != up_kw.type or 
                    existing.sub_type != up_kw.sub_type or
                    existing.sub_category != up_kw.sub_category or
                    existing.category != up_kw.category):
                    updated.append(up_kw)
        
        # Identify Deletions (only matters if delete_missing is True, but we calculate for dry_run info)
        for curr_kw in current_keywords:
            if curr_kw.term.lower() not in uploaded_map:
                deleted.append(curr_kw)
                
        summary = KeywordImportSummary(
            created=created,
            updated=updated,
            deleted=deleted,
            total_count=len(uploaded_keywords)
        )
        
        if dry_run:
            return KeywordImportResult(
                summary=summary,
                dry_run=True,
                success=True,
                message="Dry run successful. Review changes."
            )
            
        # Execute Changes
        success_count = 0
        
        # 1. Deletes (Sync Mode Only)
        if delete_missing:
            for d in deleted:
                await db.delete_keyword(d.id)
                
        # 2. Creates
        for c in created:
            # We trust Pydantic validation from parsed model
            # Re-instantiate to get fresh IDs if needed, though create_keyword might handle it
            # create_keyword expects KeywordCreate
            try:
                await db.create_keyword(c)
                success_count += 1
            except DuplicateKeywordError:
                # Should not happen since we checked current_map, but concurrency could cause it
                pass

        # 3. Updates
        for u in updated:
            existing = current_map[u.term.lower()]
            await db.update_keyword(existing.id, u)
            success_count += 1
            
        return KeywordImportResult(
            summary=summary, # Return the diff of what was done
            dry_run=False,
            success=True,
            message=f"Import completed. {len(created)} created, {len(updated)} updated, {len(deleted) if delete_missing else 0} deleted."
        )

    except (yaml.YAMLError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid import file syntax: {str(e)}")
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
