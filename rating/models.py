from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List
from datetime import datetime
import uuid

class KeywordBase(BaseModel):
    term: str = Field(..., description="The keyword term to search for", min_length=2)
    weight: float = Field(..., description="Positive or negative weight for scoring")
    type: str = Field(default="Sector", description="Type of keyword: Service or Sector")
    sub_type: Optional[str] = Field(None, description="Sub-type of the keyword (Main Category)")
    sub_category: Optional[str] = Field(None, description="Nested category for finer granularity (Sub Category)")
    category: Optional[str] = Field(None, description="Optional category for organization (kept for compatibility)")

    @field_validator('term')
    @classmethod
    def validate_term(cls, v: str) -> str:
        clean_v = v.strip()
        if not clean_v:
            raise ValueError("Keyword cannot be blank or empty")
        if len(clean_v) < 2:
            raise ValueError("Keyword term must be at least 2 characters long")
        # Spaces are allowed in keywords for better matching (e.g. "Cloud Computing")
        return clean_v

    @model_validator(mode='after')
    def validate_weight_rule(self):
        # Access attributes directly since mode='after' provides the model instance
        t = self.term
        w = self.weight
        kw_type = self.type
        
        if kw_type == 'Exclusion':
            if w >= 0:
                raise ValueError('Exclusion keywords must have a negative weight')
        elif kw_type in ['Service', 'Sector']:
            if w <= 0:
                raise ValueError(f'{kw_type} keywords must have a positive weight')
        return self

class KeywordCreate(KeywordBase):
    pass

class Keyword(KeywordBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123-456",
                "term": "Machine Learning",
                "weight": 1.5,
                "category": "Technology",
                "created_at": "2023-10-27T10:00:00"
            }
        }

class KeywordYamlModel(BaseModel):
    keywords: List[KeywordCreate]

class KeywordImportSummary(BaseModel):
    created: List[KeywordCreate] = []
    updated: List[KeywordCreate] = []
    deleted: List[Keyword] = []
    total_count: int = 0
    errors: List[str] = []

class KeywordImportResult(BaseModel):
    summary: KeywordImportSummary
    dry_run: bool
    success: bool
    message: str

class TenderACL(BaseModel):
    """
    Minimal Pydantic model for Tender data used in Rating logic.
    Part of the Anti-Corruption Layer (ACL).
    """
    id: str = Field(..., alias="internal_id")
    title: str = Field(..., alias="headline")
    description: str
    full_text: Optional[str] = None
    published_at: Optional[datetime] = Field(None, alias="published")
    deadline_at: Optional[datetime] = Field(None, alias="due")
    
    # Rating results (populated by service)
    score: float = 0.0
    rating_total: float = 0.0
    rating_title: float = 0.0
    matched_keywords: List[dict] = []
    
    # Metadata
    enrichment_locked: bool = False
    source_system: str = "Unknown"
    
    class Config:
        populate_by_name = True
        alias_generator = None 
