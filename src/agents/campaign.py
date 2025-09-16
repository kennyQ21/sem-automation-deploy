"""
Campaign designer agent for creating ad campaigns and bid strategies.
"""
from typing import List, Dict, Any
import logging
from .base import BaseAgent
from src.schemas.state import GlobalState
from src.schemas.campaign import Campaign, AdGroupBids, Bid

class CampaignDesignerAgent(BaseAgent):
    """Agent for designing campaigns and bid strategies."""
    
    def __init__(self, openai_client):
        self.client = openai_client
    
    def __call__(self, state: GlobalState) -> Dict[str, Any]:
        """
        Designs campaigns, allocates budget, and sets the final report.
        Returns a dictionary of state updates for LangGraph.
        """
        from datetime import datetime
        start_time = datetime.now()
        print(f"🎨 [CampaignDesigner] Starting campaign generation at {start_time.strftime('%H:%M:%S')}")
        
        # Graceful handling if prior steps failed to produce ad groups
        if not state.ad_groups:
            print(f"⚠️ [CampaignDesigner] No ad groups found, skipping campaign generation")
            return {"campaigns": [], "final_report": {"summary": "No ad groups to process."}}

        campaigns = []
        
        # --- Budget Allocation Strategy ---
        total_budget = state.initial_request.get("monthly_budget", 0.0)
        search_budget = total_budget * 0.5
        shopping_budget = total_budget * 0.3
        pmax_budget = total_budget * 0.2

        # Create Search campaign
        search_campaign = self._create_search_campaign(state, search_budget)
        campaigns.append(search_campaign)
        
        # Create Shopping campaign
        shopping_campaign = self._create_shopping_campaign(state, shopping_budget)
        campaigns.append(shopping_campaign)
        
        # Create Performance Max campaign
        pmax_campaign = self._create_pmax_campaign(state, pmax_budget)
        campaigns.append(pmax_campaign)
        
        # Create comprehensive final report with all required deliverables
        final_report = {
            "summary": f"Generated {len(campaigns)} campaigns with {self._count_total_keywords(state)} keywords.",
            "search_campaign": self._format_search_campaign(search_campaign, state),
            "shopping_campaign": self._format_shopping_campaign(shopping_campaign, state),
            "pmax_campaign": self._format_pmax_campaign(pmax_campaign, state),
            "budget_allocation": {
                "total_budget": total_budget,
                "search_budget": search_budget,
                "shopping_budget": shopping_budget,
                "pmax_budget": pmax_budget
            }
        }

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"✅ [CampaignDesigner] Generated {len(campaigns)} campaigns in {duration:.1f} seconds")
        
        return {
            "campaigns": campaigns,
            "final_report": final_report
        }
        
    def _create_search_campaign(self, state: GlobalState, budget: float) -> Campaign:
        """Create search campaign with match types."""
        ad_groups_with_bids = []
        
        # CORRECTION 4: Pre-process lists into dictionaries for safe and efficient O(1) lookups
        enriched_keywords_map = {k.keyword_id: k for k in state.enriched_keywords or []}
        raw_keywords_map = {k.keyword: k for k in state.raw_keywords or []}
        
        for group in state.ad_groups:
            keywords = []
            
            for keyword_id in group.keywords:
                enriched = enriched_keywords_map.get(keyword_id)
                raw = raw_keywords_map.get(keyword_id)
                
                # Skip if keyword data is missing for any reason
                if not enriched or not raw:
                    continue
                
                # CORRECTION 3: Use the _get_match_types helper method with the correct intent
                match_types = self._get_match_types(enriched.intent)
                
                # Calculate bids based on competition and budget
                target_cpa = state.initial_request.get("target_cpa", 50.0)
                conversion_rate = 0.02  # Default 2% conversion rate
                
                bid_multiplier = 1.0 + (raw.competition * 0.2)
                
                base_bid = target_cpa * conversion_rate
                conservative_bid = round(base_bid * bid_multiplier * 0.8, 2)
                aggressive_bid = round(base_bid * bid_multiplier * 1.2, 2)
                
                keywords.append(Bid(
                    keyword=keyword_id,
                    match_types=match_types,
                    bid_low=conservative_bid,
                    bid_high=aggressive_bid,
                    target_cpa=target_cpa
                ))
                
            ad_groups_with_bids.append(AdGroupBids(
                ad_group_id=group.id,
                ad_group_name=group.name,
                keywords=keywords,
                target_cpa=state.initial_request.get("target_cpa", 50.0)
            ))
        
        # CORRECTION 5: Use the allocated budget
        return Campaign(
            name="Search Campaign",
            campaign_type="search",
            budget=budget,
            target_roas=state.initial_request.get("target_roas", 3.0),
            ad_groups=ad_groups_with_bids,
            smart_bidding={
                "strategy": "TARGET_ROAS",
                "target_roas": state.initial_request.get("target_roas", 3.0)
            }
        )
    
    # CORRECTION 1: Fixed indentation and added budget parameter
    def _create_shopping_campaign(self, state: GlobalState, budget: float) -> Campaign:
        """Creates a placeholder for a shopping campaign."""
        # TODO: This logic should be expanded to create product groups based on a product feed.
        return Campaign(
            name="Shopping Campaign",
            campaign_type="shopping",
            ad_groups=[],  # Shopping campaigns use product groups, not keyword-based ad groups.
            budget=budget,
            target_roas=state.initial_request.get("target_roas", 3.0),
            smart_bidding={
                "strategy": "TARGET_ROAS",
                "target_roas": state.initial_request.get("target_roas", 3.0)
            }
        )
        
    def _create_pmax_campaign(self, state: GlobalState, budget: float) -> Campaign:
        """Create Performance Max campaign with asset themes."""
        return Campaign(
            name="Performance Max Campaign",
            campaign_type="pmax",
            budget=budget,
            target_roas=state.initial_request.get("target_roas", 3.0),
            ad_groups=[],  # PMax uses asset groups, not ad groups
            smart_bidding={
                "strategy": "MAXIMIZE_CONVERSION_VALUE",
                "target_roas": state.initial_request.get("target_roas", 3.0)
            }
        )
    
    def _format_search_campaign(self, campaign: Campaign, state: GlobalState) -> Dict[str, Any]:
        """Format search campaign for frontend display."""
        enriched_keywords_map = {k.keyword_id: k for k in state.enriched_keywords or []}
        raw_keywords_map = {k.keyword: k for k in state.raw_keywords or []}
        
        ad_groups = []
        for group in state.ad_groups or []:
            keywords = []
            for keyword_id in group.keywords:
                enriched = enriched_keywords_map.get(keyword_id)
                raw = raw_keywords_map.get(keyword_id)
                
                if enriched and raw:
                    keywords.append({
                        "keyword": keyword_id,
                        "intent": enriched.intent,
                        "search_volume": raw.avg_monthly_searches,
                        "suggested_bid": raw.suggested_bid,
                        "match_types": self._get_match_types(enriched.intent)
                    })
            
            if keywords:
                ad_groups.append({
                    "name": group.name,
                    "keywords": keywords
                })
        
        return {
            "budget": campaign.budget,
            "target_roas": campaign.target_roas,
            "ad_groups": ad_groups
        }
    
    def _format_shopping_campaign(self, campaign: Campaign, state: GlobalState) -> Dict[str, Any]:
        """Format shopping campaign for frontend display."""
        # Generate shopping bids based on keywords
        product_bids = []
        raw_keywords_map = {k.keyword: k for k in state.raw_keywords or []}
        
        # Use top keywords for shopping campaign
        top_keywords = sorted(
            state.raw_keywords or [], 
            key=lambda x: x.avg_monthly_searches, 
            reverse=True
        )[:20]  # Top 20 keywords for shopping
        
        for keyword in top_keywords:
            target_cpa = 50.0  # Default target CPA
            conversion_rate = 0.02
            computed_cpc = target_cpa * conversion_rate * (1 + keyword.competition * 0.3)
            expected_roas = state.initial_request.get("target_roas", 3.0)
            
            product_bids.append({
                "keyword": keyword.keyword,
                "search_volume": keyword.avg_monthly_searches,
                "competition": keyword.competition,
                "target_cpa": target_cpa,
                "computed_cpc": round(computed_cpc, 2),
                "expected_roas": expected_roas
            })
        
        return {
            "budget": campaign.budget,
            "target_roas": campaign.target_roas,
            "product_bids": product_bids
        }
    
    def _format_pmax_campaign(self, campaign: Campaign, state: GlobalState) -> Dict[str, Any]:
        """Format Performance Max campaign for frontend display."""
        # Generate themes based on ad groups
        themes = []
        
        for group in state.ad_groups or []:
            # Create theme based on ad group
            theme_keywords = group.keywords[:10]  # Top 10 keywords per theme
            
            themes.append({
                "name": f"{group.name} Theme",
                "description": f"Performance Max asset group targeting {group.name.lower()} related searches and audiences.",
                "keywords": theme_keywords
            })
        
        # Add default themes if no ad groups
        if not themes:
            themes = [
                {
                    "name": "Brand Awareness Theme",
                    "description": "Broad reach campaign targeting brand awareness and consideration.",
                    "keywords": []
                },
                {
                    "name": "Product Category Theme", 
                    "description": "Product-focused campaign targeting high-intent shoppers.",
                    "keywords": []
                }
            ]
        
        return {
            "budget": campaign.budget,
            "target_roas": campaign.target_roas,
            "themes": themes
        }
    
    def _count_total_keywords(self, state: GlobalState) -> int:
        """Count total keywords across all ad groups."""
        if not state.ad_groups:
            return 0
        return sum(len(group.keywords) for group in state.ad_groups)
    
    def _get_match_types(self, intent: str) -> List[str]:
        """Determine match types based on keyword intent."""
        intent = intent.lower()
        if intent == "brand":
            return ["EXACT", "PHRASE"]
        elif intent == "competitor":
            return ["PHRASE", "EXACT"]
        elif intent in ["transactional", "commercial", "high_intent"]:
            return ["BROAD", "PHRASE"]
        else:  # "informational" or other
            return ["PHRASE"]