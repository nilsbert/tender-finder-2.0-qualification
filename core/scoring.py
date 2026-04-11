from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum

@dataclass(frozen=True)
class Keyword:
    term: str
    weight: float
    type: str = "Service"
    sub_type: Optional[str] = None
    sub_category: Optional[str] = None
    category: Optional[str] = None
    
    def __post_init__(self):
        # Validation Logic - Minimal for ACL
        pass

    def matches(self, text: str) -> bool:
        return self.term.lower() in text.lower()

class MatchLocation(Enum):
    HEADLINE = "headline"
    DESCRIPTION = "description"
    FULL_TEXT = "full_text"

@dataclass(frozen=True)
class Match:
    keyword_term: str
    location: MatchLocation
    score_impact: float

@dataclass(frozen=True)
class ScoringResult:
    total_score: float
    title_score: float
    matches: List[Match]
    type_scores: Dict[str, float] = field(default_factory=dict)
    subtype_scores: Dict[str, float] = field(default_factory=dict)
    subcategory_scores: Dict[str, float] = field(default_factory=dict)

class ScoringPolicy:
    MULTIPLIERS = {
        MatchLocation.HEADLINE: 5.0,
        MatchLocation.DESCRIPTION: 3.0,
        MatchLocation.FULL_TEXT: 1.0
    }

    @staticmethod
    def calculate_score(tender_title: str, tender_description: str, tender_full_text: str, keywords: List[Keyword]) -> ScoringResult:
        total_score = 0.0
        title_score = 0.0
        matches = []
        type_scores = {}
        subtype_scores = {}
        subcategory_scores = {}
        
        # Normalize Data
        headline = (tender_title or "").lower()
        description = (tender_description or "").lower()
        full_text = (tender_full_text or "").lower()
        
        for kw in keywords:
            impact = 0.0
            location = None
            
            # --- Title Score Calculation ---
            if kw.matches(headline):
                title_score += kw.weight

            # --- Overall Score Calculation ---
            if kw.matches(headline):
                location = MatchLocation.HEADLINE
                impact = kw.weight * ScoringPolicy.MULTIPLIERS[MatchLocation.HEADLINE]
            elif kw.matches(description):
                location = MatchLocation.DESCRIPTION
                impact = kw.weight * ScoringPolicy.MULTIPLIERS[MatchLocation.DESCRIPTION]
            elif kw.matches(full_text):
                 location = MatchLocation.FULL_TEXT
                 impact = kw.weight * ScoringPolicy.MULTIPLIERS[MatchLocation.FULL_TEXT]
            
            if location:
                total_score += impact
                matches.append(Match(kw.term, location, impact))
                type_scores[kw.type] = type_scores.get(kw.type, 0.0) + impact
                if kw.sub_type:
                    subtype_scores[kw.sub_type] = subtype_scores.get(kw.sub_type, 0.0) + impact
                if kw.sub_category:
                    subcategory_scores[kw.sub_category] = subcategory_scores.get(kw.sub_category, 0.0) + impact

        # Rounding
        total_score = round(total_score, 2)
        title_score = round(title_score, 2)
        type_scores = {k: round(v, 2) for k, v in type_scores.items()}
        subtype_scores = {k: round(v, 2) for k, v in subtype_scores.items()}
        subcategory_scores = {k: round(v, 2) for k, v in subcategory_scores.items()}

        return ScoringResult(
            total_score=total_score, 
            title_score=title_score,
            matches=matches,
            type_scores=type_scores,
            subtype_scores=subtype_scores,
            subcategory_scores=subcategory_scores
        )
