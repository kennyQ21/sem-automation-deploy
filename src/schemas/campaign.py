"""
Campaign structures for SEM automation.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class Bid(BaseModel):
    """Bid settings for a keyword."""
    keyword: str
    match_types: List[str]
    bid_low: float
    bid_high: float
    target_cpa: Optional[float] = None

class AdGroupBids(BaseModel):
    """Bids for an ad group."""
    ad_group_id: str
    ad_group_name: str
    keywords: List[Bid]
    target_cpa: Optional[float] = None

class Campaign(BaseModel):
    """Campaign structure."""
    name: str
    campaign_type: str  # search, shopping, pmax
    budget: float
    target_roas: float
    ad_groups: List[AdGroupBids]
    smart_bidding: Dict[str, Any]