"""
Fallback naming utility for ad groups when AI fails.
"""
from typing import List

class FallbackNaming:
    """Simple fallback naming for ad groups."""
    
    @staticmethod
    def generate_group_name(keywords: List[str]) -> str:
        """Generate a simple fallback name based on keywords."""
        if not keywords:
            return "Unnamed Group"
        
        # Use the first keyword as base
        base_keyword = keywords[0].lower()
        
        # Common patterns
        if any(word in base_keyword for word in ['buy', 'purchase', 'order']):
            return "Purchase Intent"
        elif any(word in base_keyword for word in ['best', 'top', 'review']):
            return "Research Intent"
        elif any(word in base_keyword for word in ['cheap', 'discount', 'deal']):
            return "Price Focused"
        elif any(word in base_keyword for word in ['near me', 'local', 'location']):
            return "Local Search"
        else:
            # Extract main noun
            words = base_keyword.split()
            if len(words) > 1:
                return f"{words[-1].title()} Keywords"
            else:
                return f"{base_keyword.title()} Group"