"""
Mock agents for testing when API quotas are exceeded.
"""
import random
from typing import Dict, Any, List
from src.schemas.state import GlobalState, WebsiteAnalysis, CompetitorAnalysis, EnrichedKeyword, AdGroup
from src.agents.base import BaseAgent

class MockWebsiteAnalyzer(BaseAgent):
    """Mock website analyzer for testing."""
    
    def __call__(self, state: GlobalState) -> Dict[str, Any]:
        """Mock website analysis."""
        brand_url = state.initial_request.get('brand_url', 'https://example.com')
        
        # Mock brand analysis with flexible schema
        brand_analysis = WebsiteAnalysis(
            url=brand_url,
            products_services=[
                "Premium Products",
                "Quality Services", 
                "Customer Support"
            ],
            target_audience="Adults 25-45, Urban professionals interested in quality and value",
            brand_positioning={
                "value_props": ["High Quality", "Great Value", "Excellent Service"],
                "brand_tone": "Professional and Friendly"
            },
            commercial_signals=["Buy Now", "Shop", "Order", "Sale", "Discount"]
        )
        
        # Mock competitor analysis with flexible schema
        competitor_analysis = [
            CompetitorAnalysis(
                url="https://competitor.com",
                products_services=["Similar Products", "Competing Services"],
                target_audience="Adults 25-50, Budget-conscious shoppers",
                brand_positioning={
                    "differentiators": ["Lower Price", "Fast Delivery"],
                    "price_position": "Budget-friendly"
                },
                commercial_signals=["Sale", "Discount", "Limited Time", "Best Price"],
                market_position={"position": "competitor"},
                overlap_score=0.7,
                competitive_gaps=["Premium Features", "Customer Service"]
            )
        ]
        
        return {
            "brand_analysis": brand_analysis,
            "competitor_analysis": competitor_analysis
        }

class MockKeywordGenerator(BaseAgent):
    """Mock keyword generator for testing."""
    
    def __call__(self, state: GlobalState) -> Dict[str, Any]:
        """Generate mock seed keywords."""
        business_category = state.initial_request.get('business_category', 'E-commerce')
        
        # Generate seed keywords based on business category
        seed_keywords = [
            f"{business_category.lower()} products",
            f"buy {business_category.lower()}",
            f"best {business_category.lower()}",
            f"{business_category.lower()} store",
            f"online {business_category.lower()}"
        ]
        
        return {"seed_keywords": seed_keywords}

class MockEnrichmentAgent(BaseAgent):
    """Mock enrichment agent for testing."""
    
    def __call__(self, state: GlobalState) -> Dict[str, Any]:
        """Mock keyword enrichment."""
        if not state.raw_keywords:
            return {"enriched_keywords": []}
        
        enriched_keywords = []
        intents = ["commercial", "transactional", "informational", "brand"]
        
        for raw_keyword in state.raw_keywords[:20]:  # Limit for testing
            enriched = EnrichedKeyword(
                keyword_id=raw_keyword.keyword,
                expansions=[
                    f"best {raw_keyword.keyword}",
                    f"buy {raw_keyword.keyword} online",
                    f"{raw_keyword.keyword} reviews",
                    f"cheap {raw_keyword.keyword}"
                ],
                intent=random.choice(intents),
                headlines=[
                    f"Top {raw_keyword.keyword.title()}",
                    f"Buy {raw_keyword.keyword.title()}",
                    f"Best {raw_keyword.keyword.title()}"
                ],
                descriptions=[
                    f"Find the best {raw_keyword.keyword} at great prices.",
                    f"Shop {raw_keyword.keyword} with free shipping and returns."
                ],
                landing_candidate=f"/{raw_keyword.keyword.replace(' ', '-')}",
                confidence=random.uniform(0.7, 0.95)
            )
            enriched_keywords.append(enriched)
        
        return {"enriched_keywords": enriched_keywords}

class MockClusteringAgent(BaseAgent):
    """Mock clustering agent for testing."""
    
    def __call__(self, state: GlobalState) -> Dict[str, Any]:
        """Mock keyword clustering."""
        if not state.enriched_keywords:
            return {"ad_groups": []}
        
        # Group keywords by intent
        intent_groups = {}
        for keyword in state.enriched_keywords:
            intent = keyword.intent
            if intent not in intent_groups:
                intent_groups[intent] = []
            intent_groups[intent].append(keyword.keyword_id)
        
        ad_groups = []
        for intent, keywords in intent_groups.items():
            ad_group = AdGroup(
                id=f"group_{intent}",
                name=f"{intent.title()} Keywords",
                keywords=keywords,
                centroid=[random.uniform(-1, 1) for _ in range(384)],  # Mock 384-dim vector
                score=random.uniform(0.7, 0.9)
            )
            ad_groups.append(ad_group)
        
        return {"ad_groups": ad_groups}