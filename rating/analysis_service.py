from typing import List, Optional
import logging
import json
from .models import KeywordCreate, TenderACL
from .core.database import db

logger = logging.getLogger(__name__)

class KeywordAnalysisService:
    """Service to analyze tenders and suggest keywords using AI (Independent Microservice version)."""

    def __init__(self):
        self.llm_service = None

    async def analyze_tender(self, tender_id: str, prompt_override: Optional[str] = None) -> List[KeywordCreate]:
        """
        Analyze a tender's text and extract relevant keywords.
        Uses local database to fetch tender (via ACL/Sync) or handles it via prompt.
        """
        # 1. Fetch Tender Data from local DB
        # Note: In the decoupled world, we fetch the TenderACL record.
        from .core.database import db
        tender_orm = await db.get_tender_acl(tender_id)
        if not tender_orm:
             # Fallback: if not in local DB, maybe it was just synced or we need to fail gracefully
            raise ValueError(f"Tender {tender_id} not found in local qualification database.")

        # Combine headline and description for analysis
        text_content = f"Headline: {tender_orm.title}\n\nDescription: {tender_orm.description}"

        # 2. Fetch Existing Keywords
        existing_keywords = await db.get_all_keywords()
        existing_terms = [k.term for k in existing_keywords]
        
        # 3. Construct Prompt
        existing_terms_str = ", ".join(existing_terms)
        
        default_prompt = f"""
        You are an expert in public procurement and tender analysis.
        Your task is to extract the most important keywords from the following tender text that are NOT already in the existing keyword list.
        
        Target Output:
        - Extract up to 10 highly relevant keywords.
        - Assign a 'weight' between 0.1 (low relevance) and 2.0 (high relevance).
        - Assign a 'type' (Sector, Service, or Exclusion). usually 'Sector' or 'Service'.
        - Do not include generic stop words.
        - Do not include words present in the "Existing Keywords" list.
        
        Existing Keywords (DO NOT SUGGEST THESE):
        [{existing_terms_str}]
        
        Tender Text:
        {text_content}
        
        Respond ONLY with a valid JSON array of objects.
        """

        prompt = prompt_override if prompt_override else default_prompt
        
        # 4. Get active AI Configuration
        if self.llm_service is None:
            from ..ai.services import LLMService
            self.llm_service = LLMService()
            
        ai_config = await self.llm_service.get_active_provider_config()
        if not ai_config:
            raise ValueError("No active AI provider configured.")

        # 5. Call AI Service
        try:
            response_text = await self.llm_service.generate_text(
                config=ai_config,
                system_prompt="Extract information from text in JSON format.",
                user_prompt=prompt,
                json_mode=True
            )
            
            # Clean response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            data = json.loads(response_text)
            
            suggestions = []
            if isinstance(data, list):
                for item in data:
                    try:
                        term = item.get('term', '').replace(' ', '-')
                        if term and term not in existing_terms:
                            suggestions.append(KeywordCreate(
                                term=term,
                                weight=float(item.get('weight', 1.0)),
                                type=item.get('type', 'Service')
                            ))
                    except Exception as e:
                        logger.warning(f"Skipping invalid suggestion {item}: {e}")
            elif isinstance(data, dict) and "keywords" in data: # Handle common AI deviation
                 for item in data["keywords"]:
                     # ... similar logic ...
                     pass
            
            return suggestions

        except Exception as e:
            logger.error(f"Keyword analysis failed: {e}")
            raise e

keyword_analysis_service = KeywordAnalysisService()
