"""
Google Ads API integration for keyword research.
"""
import random
from typing import Dict, List, Any
from src.schemas.state import RawKeyword

class GoogleAdsClient:
    """Client for interacting with Google Ads API."""
    
    def __init__(self, credentials_path: str):
        """Initialize client with credentials.
        
        Args:
            credentials_path: Path to google-ads.yaml config file
        """
        self.use_mock_data = False
        self.client = None
        try:
            # Load real credentials
            from google.ads.googleads.client import GoogleAdsClient as GAdsClient
            self.client = GAdsClient.load_from_storage(credentials_path)
            print(f"✅ Google Ads API client initialized successfully")
        except Exception as e:
            print(f"❌ Google Ads API initialization failed: {str(e)}")
            print(f"📝 Falling back to mock data for development")
            self.use_mock_data = True
    
    def fetch_keyword_ideas(
        self, 
        seed_keywords: List[str], 
        language: str = "en",
        location_id: str = "2840"  # US by default
    ) -> List[RawKeyword]:
        """Fetch keyword ideas from Google Ads Keyword Planner.
        
        Args:
            seed_keywords: List of seed keywords to get ideas for
            language: Language code (default: "en")
            location_id: Google Ads location ID (default: US)
            
        Returns:
            List of RawKeyword objects with metrics
        """
        if self.use_mock_data:
            return self._generate_mock_keywords(seed_keywords)
        
        try:
            from google.ads.googleads.errors import GoogleAdsException
            
            # Get service
            service = self.client.get_service("KeywordPlanIdeaService")
            
            # Get customer ID from config
            customer_id = "5686133715"
            
            # Create request with login customer ID for manager access
            request = self.client.get_type("GenerateKeywordIdeasRequest")
            request.customer_id = customer_id
            request.language = f"languageConstants/1000"  # English
            request.geo_target_constants.append(f"geoTargetConstants/{location_id}")
            

            
            # Set keyword seed
            keyword_seed = self.client.get_type("KeywordSeed")
            keyword_seed.keywords.extend(seed_keywords)
            request.keyword_seed = keyword_seed
            
            # Get results with error handling
            response = service.generate_keyword_ideas(request=request)
            
            # Process results
            keywords = []
            for result in response:
                metrics = result.keyword_idea_metrics
                keywords.append(RawKeyword(
                    keyword=result.text,
                    avg_monthly_searches=metrics.avg_monthly_searches or 0,
                    competition=float(metrics.competition.value) if metrics.competition else 0.5,
                    suggested_bid=(metrics.low_top_of_page_bid_micros or 1000000) / 1_000_000
                ))
            
            print(f"✅ Retrieved {len(keywords)} keywords from Google Ads API")
                
            return keywords
            
        except Exception as e:
            print(f"❌ Google Ads API error: {str(e)}")
            print(f"📝 Using mock data as fallback")
            return self._generate_mock_keywords(seed_keywords)
    
    def _generate_mock_keywords(self, seed_keywords: List[str]) -> List[RawKeyword]:
        """Generate mock keyword data for testing."""
        mock_keywords = []
        
        # Base keyword variations
        variations = [
            "buy {}", "best {}", "cheap {}", "{} online", "{} store", 
            "{} reviews", "{} price", "top {}", "{} deals", "{} sale",
            "affordable {}", "{} near me", "{} service", "{} company"
        ]
        
        for seed in seed_keywords:
            # Add the seed keyword itself
            mock_keywords.append(RawKeyword(
                keyword=seed,
                avg_monthly_searches=random.randint(1000, 50000),
                competition=random.uniform(0.1, 0.9),
                suggested_bid=random.uniform(0.50, 5.00)
            ))
            
            # Add variations
            for variation in variations[:8]:  # Limit to 8 variations per seed
                keyword = variation.format(seed)
                mock_keywords.append(RawKeyword(
                    keyword=keyword,
                    avg_monthly_searches=random.randint(500, 20000),
                    competition=random.uniform(0.1, 0.9),
                    suggested_bid=random.uniform(0.30, 3.00)
                ))
        
        return mock_keywords