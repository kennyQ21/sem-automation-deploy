"""
Core state schemas for the SEM automation system.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from .campaign import Campaign

class WebsiteAnalysis(BaseModel):
    """Analysis of a website's content and structure."""
    url: str
    products_services: List[Any]  # Allow strings or dicts
    target_audience: Any  # Allow strings, lists, or dicts
    brand_positioning: Optional[Dict[str, Any]] = None
    commercial_signals: Any = Field(default_factory=list)  # Allow any format

class CompetitorAnalysis(WebsiteAnalysis):
    """Extended analysis for competitor websites."""
    market_position: Dict[str, Any]
    overlap_score: float
    competitive_gaps: List[str]

class RawKeyword(BaseModel):
    """Keyword data from Google Ads API."""
    keyword: str
    avg_monthly_searches: int
    competition: float
    suggested_bid: float
    search_intent: Optional[str] = None
    opportunity_score: Optional[float] = None # Added for consistency

class EnrichedKeyword(BaseModel):
    """Keyword with Gemini 2.0 Flash-generated enrichments."""
    keyword_id: str
    expansions: List[str]
    intent: str
    headlines: List[str]
    descriptions: List[str]
    landing_candidate: str
    confidence: float
    vector: Optional[List[float]] = None
    opportunity_score: Optional[float] = None

class AdGroup(BaseModel):
    """Semantically clustered ad group."""
    id: str
    name: str
    keywords: List[str]
    # intent_type: str # This field was in one definition but not used consistently. Removed for clarity.
    centroid: List[float]
    score: float
    theme: Optional[Dict[str, Any]] = None

class ShoppingBid(BaseModel):
    """Shopping campaign bid strategy."""
    keyword: str
    search_volume: int
    competition: float
    target_cpa: float
    computed_cpc: float
    confidence: float

class PMaxCampaignTheme(BaseModel):
    """Performance Max campaign theme and assets."""
    name: str
    description: str
    signals: List[str]
    asset_groups: List[str]

class GlobalState(BaseModel):
    """LangGraph workflow state."""
    # Input and tracking
    initial_request: Dict[str, Any]
    job_id: str
    error_log: List[str] = Field(default_factory=list)
    clustering_attempts: int = Field(default=0)
    
    # Analysis results
    brand_analysis: Optional[WebsiteAnalysis] = None
    competitor_analysis: Optional[List[CompetitorAnalysis]] = None
    
    # Keyword processing
    seed_keywords: Optional[List[str]] = None
    raw_keywords: Optional[List[RawKeyword]] = None
    enriched_keywords: Optional[List[EnrichedKeyword]] = None
    
    # Vector operations
    embeddings: Dict[str, List[float]] = Field(default_factory=dict)
    
    # Campaign structures
    ad_groups: Optional[List[AdGroup]] = None
    pmax_campaign: Optional[PMaxCampaignTheme] = None # Adjusted for consistency
    shopping_campaign: Optional[Dict] = None # Placeholder for shopping strategy
    campaigns: Optional[List[Campaign]] = None
    search_campaign: Optional[Dict] = None # Added for clarity
    
    # Final output
    final_report: Optional[Dict[str, Any]] = None
    
    class Config:
        arbitrary_types_allowed = True