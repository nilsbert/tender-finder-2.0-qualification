from sqlalchemy import Column, String, Float, JSON, MetaData, DateTime, func
from sqlalchemy.orm import declarative_base

metadata = MetaData(schema="qualification")
QualificationBase = declarative_base(metadata=metadata)

class Keyword(QualificationBase):
    __tablename__ = "keywords"
    
    id = Column(String(50), primary_key=True)
    term = Column(String(255), nullable=False)
    weight = Column(Float, nullable=False, default=1.0)
    type = Column(String(50), nullable=False, default="Sector")
    sub_type = Column(String(255), nullable=True)
    sub_category = Column(String(255), nullable=True)
    category = Column(String(255), nullable=True) # Keeping for compatibility
    created_at = Column(String(50), nullable=True) # Storing as string for simplicity in ACL

class TenderACL(QualificationBase):
    """
    Anti-Corruption Layer (ACL) for Tenders.
    Only stores fields required for the Qualification domain.
    """
    __tablename__ = "tenders_acl"
    
    id = Column(String(50), primary_key=True)
    title = Column(String(500), nullable=True)
    description = Column(String, nullable=True)
    full_text = Column(String, nullable=True)
    score = Column(Float, nullable=False, default=0.0)
    status = Column(String(50), nullable=True)
    source_system = Column(String(100), nullable=True)
    
class QualificationScore(QualificationBase):
    __tablename__ = "scores"
    
    tender_id = Column(String(50), primary_key=True)
    score = Column(Float, nullable=False, default=0.0)
    matched_keywords = Column(JSON, nullable=True) # Stores list of matched keywords

class ConfigORM(QualificationBase):
    __tablename__ = "configs"

    key = Column(String(255), primary_key=True)
    value = Column(JSON, nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
