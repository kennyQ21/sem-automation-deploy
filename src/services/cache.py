"""
Simple caching service to reduce Gemini API calls.
"""
import json
import hashlib
from typing import Optional, Dict, Any
from pathlib import Path

class CacheService:
    """Simple file-based cache for Gemini responses."""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_key(self, prompt: str) -> str:
        """Generate cache key from prompt."""
        return hashlib.md5(prompt.encode()).hexdigest()
    
    def get(self, prompt: str) -> Optional[str]:
        """Get cached response for prompt."""
        cache_key = self._get_cache_key(prompt)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    return data.get('response')
            except:
                pass
        return None
    
    def set(self, prompt: str, response: str) -> None:
        """Cache response for prompt."""
        cache_key = self._get_cache_key(prompt)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump({'prompt': prompt, 'response': response}, f)
        except:
            pass