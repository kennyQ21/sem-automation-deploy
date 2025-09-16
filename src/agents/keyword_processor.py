"""
Keyword processing and scoring node.
"""
from typing import Dict, List, Any
from src.schemas.state import GlobalState, RawKeyword
from .base import BaseAgent

class KeywordProcessor(BaseAgent):
    """Node for processing and scoring keywords."""
    
    def handle_error(self, error: Exception, state: GlobalState) -> Dict[str, Any]:
        """Handle errors by logging them in state."""
        return {
            "error_log": state.error_log + [str(error)]
        }
    
    def _calculate_opportunity_score(self, keyword: RawKeyword) -> float:
        """Calculate opportunity score for a keyword."""
        # Use a more reasonable search volume normalization
        # Most keywords have 50-5000 searches, so normalize differently
        if keyword.avg_monthly_searches <= 100:
            search_volume_norm = 0.2  # Low but acceptable
        elif keyword.avg_monthly_searches <= 1000:
            search_volume_norm = 0.5  # Good volume
        elif keyword.avg_monthly_searches <= 5000:
            search_volume_norm = 0.8  # High volume
        else:
            search_volume_norm = 1.0  # Very high volume
        
        # Normalize competition (assuming it's 0-5 scale based on logs)
        competition_norm = min(keyword.competition / 5.0, 1.0)
        competition_score = 1.0 - competition_norm  # Invert competition
        
        # Consider bid value as an indicator of commercial value
        bid_norm = min(keyword.suggested_bid / 100.0, 1.0)  # Normalize bids up to $100
        
        # Basic opportunity score with more balanced weighting
        base_score = (search_volume_norm * 0.4) + (competition_score * 0.3) + (bid_norm * 0.3)
        
        # Boost score for commercial intent
        commercial_modifiers = ['buy', 'price', 'deal', 'shop', 'purchase', 'store', 'online']
        if any(mod in keyword.keyword.lower() for mod in commercial_modifiers):
            base_score *= 1.2
            
        return min(base_score, 1.0)
    
    def _filter_keywords(self, keywords: List[RawKeyword]) -> List[RawKeyword]:
        """Filter keywords based on assignment criteria."""
        print(f"🔍 [KeywordProcessor] Analyzing {len(keywords)} raw keywords...")
        
        # Debug first 10 keywords in detail
        for i, kw in enumerate(keywords[:10]):
            print(f"  {i+1}. '{kw.keyword}' - searches: {kw.avg_monthly_searches}, bid: {kw.suggested_bid}, competition: {kw.competition}")
        
        # Filter with detailed logging
        filtered = []
        failed_counts = {
            'search_volume': 0,
            'bid_data': 0,
            'too_long': 0,
            'too_short': 0
        }
        
        for kw in keywords:
            if kw.avg_monthly_searches < 50:
                failed_counts['search_volume'] += 1
                continue
            if kw.suggested_bid <= 0:
                failed_counts['bid_data'] += 1
                continue
            if len(kw.keyword.split()) > 6:
                failed_counts['too_long'] += 1
                continue
            if len(kw.keyword.strip()) <= 1:
                failed_counts['too_short'] += 1
                continue
            
            filtered.append(kw)
        
        print(f"🔍 [KeywordProcessor] Filter results:")
        print(f"  - Failed search volume (< 50): {failed_counts['search_volume']}")
        print(f"  - Failed bid data (<= 0): {failed_counts['bid_data']}")
        print(f"  - Failed too long (> 6 words): {failed_counts['too_long']}")
        print(f"  - Failed too short (<= 1 char): {failed_counts['too_short']}")
        print(f"  - Passed all filters: {len(filtered)}")
        
        return filtered
    
    def __call__(self, state: GlobalState) -> Dict[str, Any]:
        """Process and score keywords."""
        from datetime import datetime
        start_time = datetime.now()
        print(f"⚙️ [KeywordProcessor] Starting keyword processing at {start_time.strftime('%H:%M:%S')}")
        
        try:
            raw_keywords = state.raw_keywords
            if not raw_keywords:
                print(f"⚠️ [KeywordProcessor] No keywords to process")
                return self.handle_error(ValueError("No keywords to process"), state)
                
            # Filter keywords
            filtered = self._filter_keywords(raw_keywords)
            
            if not filtered:
                print(f"⚠️ [KeywordProcessor] No keywords passed filtering criteria")
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                print(f"✅ [KeywordProcessor] Processed 0 keywords in {duration:.1f} seconds")
                return {"raw_keywords": []}
            
            # Score keywords
            scored_keywords = []
            opportunity_failures = 0
            
            print(f"🔍 [KeywordProcessor] Scoring top 5 keywords:")
            
            for i, kw in enumerate(filtered):
                opportunity_score = self._calculate_opportunity_score(kw)
                
                # Debug first 5 scores
                if i < 5:
                    print(f"  {i+1}. '{kw.keyword}' - score: {opportunity_score:.3f} (searches: {kw.avg_monthly_searches}, bid: {kw.suggested_bid:.2f}, comp: {kw.competition})")
                
                # Add to scored list if meets threshold  
                if opportunity_score >= 0.15:  # Slightly higher threshold for better quality
                    # Update the RawKeyword with the opportunity score
                    kw.opportunity_score = opportunity_score
                    scored_keywords.append(kw)
                else:
                    opportunity_failures += 1
                    
            print(f"🔍 [KeywordProcessor] Opportunity scoring results:")
            print(f"  - Failed opportunity threshold (< 0.1): {opportunity_failures}")
            print(f"  - Passed opportunity scoring: {len(scored_keywords)}")
                    
            # Sort by opportunity score and limit to top keywords for performance
            sorted_keywords = sorted(
                scored_keywords,
                key=lambda x: x.opportunity_score or 0.0,
                reverse=True
            )
            
            # Limit to top 150 keywords for optimal performance vs. quality balance
            max_keywords = 150
            if len(sorted_keywords) > max_keywords:
                sorted_keywords = sorted_keywords[:max_keywords]
                print(f"🔄 [KeywordProcessor] Limited to top {max_keywords} keywords for performance")
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            print(f"✅ [KeywordProcessor] Processed {len(sorted_keywords)} keywords in {duration:.1f} seconds")
            
            return {
                "raw_keywords": sorted_keywords
            }
            
        except Exception as e:
            return self.handle_error(e, state)