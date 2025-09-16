"""
LangGraph nodes for website analysis with robust error handling.
"""
import json
import logging
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
import requests
from pydantic import ValidationError
from src.schemas.state import GlobalState, WebsiteAnalysis, CompetitorAnalysis

class WebsiteAnalyzer:
    """Node for analyzing brand and competitor websites."""
    
    def __init__(self, openai_client):
        self.client = openai_client
        
    def _scrape_website(self, url: str) -> Optional[str]:
        """Scrape website content, handling potential HTTP and network errors."""
        if not url or not url.startswith('http'):
            logging.warning(f"Invalid URL provided for scraping: {url}")
            return None
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                element.decompose()
            
            text = soup.get_text(separator='\n', strip=True)
            return text
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error scraping {url}: {e}")
            return None

    def _analyze_content(self, content: str, prompt: str, url: str) -> Optional[Dict[str, Any]]:
        """Call OpenAI API to analyze content, handling API and JSON parsing errors."""
        if not content:
            logging.warning(f"No content to analyze for URL: {url}")
            return None
        try:
            full_prompt = f"{prompt}\n\nWebsite content:\n{content[:20000]}"
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": full_prompt}],
                temperature=0.7,
                max_tokens=800
            )
            response_text = response.choices[0].message.content.strip()
            cleaned_text = response_text.lstrip("```json").rstrip("```")
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode JSON from OpenAI for {url}. Response: {response_text}", exc_info=True)
            return None
        except Exception as e:
            logging.error(f"OpenAI API call failed for {url}", exc_info=True)
            return None

    def __call__(self, state: GlobalState) -> Dict[str, Any]:
        """Analyze brand and competitor websites and update the state."""
        from datetime import datetime
        start_time = datetime.now()
        print(f"🌐 [WebsiteAnalyzer] Starting website analysis at {start_time.strftime('%H:%M:%S')}")
        
        brand_url = state.initial_request.get('brand_url')
        competitor_urls = state.initial_request.get('competitor_urls', [])
        print(f"🌐 [WebsiteAnalyzer] Analyzing brand: {brand_url}, competitors: {len(competitor_urls)}")
        
        brand_content = self._scrape_website(brand_url)
        brand_analysis_json = self._analyze_content(
            brand_content,
            prompt="""You are a world-class marketing analyst. Based on website content, extract information and return ONLY valid JSON with these exact keys:
{
  "products_services": ["product1", "product2", "product3"],
  "target_audience": "description of target audience",
  "value_props": ["prop1", "prop2"],
  "brand_tone": "description of brand tone"
}""",
            url=brand_url
        )
        
        brand_state = None
        if brand_analysis_json:
            try:
                brand_state = WebsiteAnalysis(
                    url=brand_url,
                    products_services=brand_analysis_json.get('products_services', []),
                    target_audience=brand_analysis_json.get('target_audience', {}),
                    brand_positioning={
                        'value_props': brand_analysis_json.get('value_props', []),
                        'brand_tone': brand_analysis_json.get('brand_tone', '')
                    },
                    commercial_signals=[]
                )
            except ValidationError as e:
                logging.error(f"Pydantic validation failed for brand {brand_url}: {e}")

        competitor_states: List[CompetitorAnalysis] = []
        for url in competitor_urls:
            content = self._scrape_website(url)
            comp_analysis_json = self._analyze_content(
                content,
                prompt="""Analyze this competitor website and return ONLY valid JSON with these exact keys:
{
  "products": ["product1", "product2"],
  "target_market": "description of target market",
  "differentiators": ["diff1", "diff2"],
  "price_position": "pricing strategy description"
}""",
                url=url
            )
            if comp_analysis_json:
                try:
                    # --- THIS IS THE CORRECTED LINE ---
                    competitor_states.append(CompetitorAnalysis(
                        url=url, products_services=comp_analysis_json.get('products', []),
                        target_audience=comp_analysis_json.get('target_market', {}),
                        brand_positioning={
                            'differentiators': comp_analysis_json.get('differentiators', []),
                            'price_position': comp_analysis_json.get('price_position', '')
                        },
                        commercial_signals=[], market_position=comp_analysis_json,
                        overlap_score=0.0, competitive_gaps=[]
                    ))
                except ValidationError as e:
                    logging.error(f"Pydantic validation failed for competitor {url}: {e}")
            
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"✅ [WebsiteAnalyzer] Completed in {duration:.1f} seconds")
        
        return {
            "brand_analysis": brand_state,
            "competitor_analysis": competitor_states
        }