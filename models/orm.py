from sqlalchemy.orm import declarative_base
Base = declarative_base()
from datetime import datetime
from typing import Optional, List, Any
import uuid

from sqlalchemy import String, Float, DateTime, Text, JSON, Boolean, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func





class AdminListORM(Base):
    """SQL model for the persistent admin email list."""
    __tablename__ = "admin_list"
    
    email: Mapped[str] = mapped_column(String(255), primary_key=True)

    def __repr__(self) -> str:
        return f"AdminList(email={self.email!r})"

class UserORM(Base):
    """SQL model for MSAL-captured users."""
    __tablename__ = "users"

    oid: Mapped[str] = mapped_column(String(255), primary_key=True) # Microsoft Immutable ID
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="user", nullable=False)
    
    last_login_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    def __repr__(self) -> str:
        return f"User(email={self.email!r}, oid={self.oid!r}, role={self.role!r})"

class WhitelistDomainORM(Base):
    """SQL model for approved email domains."""
    __tablename__ = "whitelist_domains"
    domain: Mapped[str] = mapped_column(String(255), primary_key=True)

class WhitelistEmailORM(Base):
    """SQL model for explicitly approved individual email addresses."""
    __tablename__ = "whitelist_emails"
    email: Mapped[str] = mapped_column(String(255), primary_key=True)

class ApprovalRequestORM(Base):
    """SQL model for users who attempted login and are pending approval."""
    __tablename__ = "approval_requests"
    email: Mapped[str] = mapped_column(String(255), primary_key=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="PENDING") # PENDING, APPROVED, DECLINED
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

# Backwards-compat alias for older imports.



class TenderORM(Base):
    __tablename__ = "tenders"

    def __init__(self, **kwargs):
        """
        Robust constructor that filters out keys not present in the model schema.
        Prevents 'invalid keyword argument' errors during backward compatibility phases.
        """
        # Get all valid attribute names from the mapper
        from sqlalchemy import inspect
        mapper = inspect(self.__class__)
        allowed_keys = {c.key for c in mapper.attrs}
        
        # Filter kwargs
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in allowed_keys}
        
        super().__init__(**filtered_kwargs)


    # Tender IDs can come from external sources (e.g. Tender24) and exceed UUID length.
    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    full_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True, nullable=True)
    deadline_at: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True, nullable=True)
    
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
    ai_status: Mapped[str] = mapped_column(String(50), default="open", index=True, nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0)

    
    
    contact_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # For extra contact fields
    
    source_system: Mapped[str] = mapped_column(String(50), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    source_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # enrichment_data moved to EnrichmentStateORM (or TenderEnrichmentORM if strictly separate)
    # matched_keywords moved to TenderRatingORM


class TenderRatingORM(Base):
    """
    Decoupled storage for Tender Ratings (Scores & Keywords).
    Linked to TenderORM via tender_id.
    """
    __tablename__ = "tender_ratings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tender_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    
    score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    title_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    matched_keywords: Mapped[Optional[list]] = mapped_column(JSON, nullable=True) # List of dicts: {"term": str, "score": float}
    feedback_given: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class EnrichmentStateORM(Base):
    """
    Decoupled storage for AI Enrichment results.
    Linked to TenderORM via tender_id but stored separately 
    to facilitate future microservice extraction.
    """
    __tablename__ = "tender_enrichment"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Logical link to TenderORM.id
    tender_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    
    status: Mapped[str] = mapped_column(String(50), default="PENDING", index=True)
    
    # The actual AI results (EnrichmentResult)
    result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Metadata about the process (cost, tokens, model version)
    service_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class CrawlerJobORM(Base):
    __tablename__ = "crawler_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    crawler_id: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    tenders_found: Mapped[int] = mapped_column(Integer, default=0)
    tenders_processed: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class KeywordORM(Base):
    __tablename__ = "keywords"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    term: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False) # Sector, Service, Exclusion
    sub_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sub_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class BidDecisionORM(Base):
    __tablename__ = "bid_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Intentionally not a FK: tenders live in the crawler database for future microservice extraction.
    tender_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    decision: Mapped[str] = mapped_column(String(50), nullable=False) # bid, no_bid, defer, needs_info
    reason_codes: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decided_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    decided_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class ConfigORM(Base):
    __tablename__ = "configs"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class TenderOwnershipORM(Base):
    __tablename__ = "tender_ownership"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Intentionally not a FK: tenders live in the crawler database for future microservice extraction.
    tender_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="UNCLAIMED")
    driver: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # Person object
    co_drivers: Mapped[Optional[list]] = mapped_column(JSON, nullable=True) # List of Person objects
    claimed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    released_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class TenderCommentORM(Base):
    __tablename__ = "tender_comments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Intentionally not a FK: tenders live in the crawler database for future microservice extraction.
    tender_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    author: Mapped[dict] = mapped_column(JSON, nullable=False) # Person object
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class ManualUploadORM(Base):
    __tablename__ = "manual_uploads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tender_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True) # Loose link (no FK across DBs)
    
    file_id: Mapped[str] = mapped_column(String(36), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    
    status: Mapped[str] = mapped_column(String(50), default="queued")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extraction_method: Mapped[str] = mapped_column(String(50), default="ai")
    
    extracted_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    user_overrides: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    uploaded_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class ReferenceORM(Base):
    __tablename__ = "references"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    
    sector_tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    service_tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    capability_tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    team_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    markdown: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    markdown_status: Mapped[str] = mapped_column(String(50), default="pending")
    document: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # FileMetadata
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class ProfileORM(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type: Mapped[str] = mapped_column(String(50), nullable=False) # team, expert, department
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Person specific fields
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    position: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    practice: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cluster: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    full_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    capability_tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    certifications: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    markdown: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    markdown_status: Mapped[str] = mapped_column(String(50), default="pending")
    document: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())



class DistributionLabelORM(Base):
    __tablename__ = "distribution_labels"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(String(50), default="CUSTOM")  # SECTOR, SERVICE, CUSTOM
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class DistributionOfficeORM(Base):
    __tablename__ = "distribution_offices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Address fields for better AI matching
    city: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class DistributionWebhookORM(Base):
    __tablename__ = "distribution_webhooks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    webhook_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    
    # New Relations
    label_id: Mapped[Optional[str]] = mapped_column(String(36), index=True, nullable=True)
    office_id: Mapped[Optional[str]] = mapped_column(String(36), index=True, nullable=True)
    match_threshold: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Legacy / Deprecated Scope Configuration
    scope_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # ALL, SECTOR, SERVICE
    scope_value: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # e.g. "Information Technology"
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_failure_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class DistributionLogORM(Base):
    __tablename__ = "distribution_logs"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tender_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    webhook_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    
    status: Mapped[str] = mapped_column(String(50), nullable=False) # SENT, FAILED
    response_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

# Backward compatibility aliases
LabelORM = DistributionLabelORM
OfficeORM = DistributionOfficeORM
WebhookORM = DistributionWebhookORM
