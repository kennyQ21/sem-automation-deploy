"""
OpenAI GPT-4 enrichment agent as alternative to Gemini.
"""
import json
import logging
import os
from typing import Dict, Any
from openai import OpenAI
from pydantic import ValidationError
from .base import BaseAgent
from src.schemas.state import GlobalState, EnrichedKeyword
from src.services.cache import CacheService

class OpenAIEnrichmentAgent(BaseAgent):
    """Agent for enriching keywords using OpenAI GPT-4."""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.cache = CacheService()
    
    def __call__(self, state: GlobalState) -> Dict[str, Any]:
        """Enrich keywords with OpenAI GPT-4."""
        from datetime import datetime
        start_time = datetime.now()
        print(f"🔮 [OpenAIEnrichment] Starting keyword enrichment at {start_time.strftime('%H:%M:%S')}")
        
        if not state.raw_keywords:
            print(f"⚠️ [OpenAIEnrichment] No raw keywords to process")
            return {"enriched_keywords": []}

        # Batch keywords for processing - limit to top 20 for better coverage but still fast
        top_keywords = sorted(state.raw_keywords, key=lambda x: x.opportunity_score or 0, reverse=True)[:20]
        keyword_batches = [top_keywords]  # Single batch for speed
        
        print(f"🔮 [OpenAIEnrichment] Processing top {len(top_keywords)} keywords by opportunity score")
        
        enriched_keywords_list = []
        for batch in keyword_batches:
            # Prepare context
            keywords_context = "\n".join([
                f"Keyword: {k.keyword}\n"
                f"Monthly Searches: {k.avg_monthly_searches}\n"
                f"Competition: {k.competition:.2f}\n" 
                for k in batch
            ])
            
            # Create prompt
            prompt = f"""Analyze these keywords and return a JSON array with enrichment data:

{keywords_context}

For each keyword, provide:
- keyword: the original keyword
- expansions: 4 related keyword variations
- intent: one of "brand", "commercial", "transactional", "informational"
- headlines: 3 ad headlines (max 30 chars each)
- descriptions: 2 ad descriptions (max 90 chars each)  
- landing_candidate: suggested landing page URL path
- confidence: score 0.0-1.0

Return only valid JSON array."""
            
            try:
                # Check cache first
                cached_response = self.cache.get(prompt)
                if cached_response:
                    response_text = cached_response
                else:
                    # Call OpenAI API
                    response = self.client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.5,
                        max_tokens=800
                    )
                    response_text = response.choices[0].message.content.strip()
                    # Cache the response
                    self.cache.set(prompt, response_text)
                
                # Clean and parse JSON with better error handling
                cleaned_text = response_text.strip()
                if "```json" in cleaned_text:
                    cleaned_text = cleaned_text.split("```json")[1].split("```")[0]
                elif "```" in cleaned_text:
                    cleaned_text = cleaned_text.split("```")[1]
                
                # Remove any trailing commas or fix common JSON issues
                cleaned_text = cleaned_text.strip().rstrip(',').replace(',}', '}').replace(',]', ']')
                enrichments = json.loads(cleaned_text)
                
                # Process each enrichment
                for enrichment_data in enrichments:
                    try:
                        parsed_keyword = EnrichedKeyword(
                            keyword_id=enrichment_data["keyword"],
                            expansions=enrichment_data.get("expansions", []),
                            intent=enrichment_data.get("intent", "commercial"),
                            headlines=enrichment_data.get("headlines", []),
                            descriptions=enrichment_data.get("descriptions", []),
                            landing_candidate=enrichment_data.get("landing_candidate", ""),
                            confidence=enrichment_data.get("confidence", 0.75)
                        )
                        
                        if self.validate_output(parsed_keyword):
                            enriched_keywords_list.append(parsed_keyword)
                            
                    except (ValidationError, KeyError) as e:
                        logging.error(f"Validation failed for enrichment data: {enrichment_data}. Error: {e}")
                        # Create fallback
                        try:
                            fallback_keyword = EnrichedKeyword(
                                keyword_id=enrichment_data.get("keyword", "unknown"),
                                expansions=[],
                                intent="commercial",
                                headlines=["Shop Now"],
                                descriptions=["Find great deals online"],
                                landing_candidate="/",
                                confidence=0.5
                            )
                            enriched_keywords_list.append(fallback_keyword)
                        except:
                            continue

            except json.JSONDecodeError as e:
                logging.error(f"Error decoding JSON from OpenAI response: {e}")
                # Create fallback enriched keywords for this batch
                for kw in batch:
                    try:
                        fallback_keyword = EnrichedKeyword(
                            keyword_id=kw.keyword,
                            expansions=[f"buy {kw.keyword}", f"best {kw.keyword}", f"{kw.keyword} online"],
                            intent="commercial",
                            headlines=["Shop Now", "Best Deals", "Buy Online"],
                            descriptions=["Find great deals online", "Quality products at low prices"],
                            landing_candidate="/",
                            confidence=0.7
                        )
                        enriched_keywords_list.append(fallback_keyword)
                    except:
                        continue
                continue
            except Exception as e:
                logging.error(f"Error enriching batch with OpenAI: {str(e)}")
                # Create fallback enriched keywords for this batch
                for kw in batch:
                    try:
                        fallback_keyword = EnrichedKeyword(
                            keyword_id=kw.keyword,
                            expansions=[f"buy {kw.keyword}", f"best {kw.keyword}"],
                            intent="commercial",
                            headlines=["Shop Now", "Best Deals"],
                            descriptions=["Find great deals online"],
                            landing_candidate="/",
                            confidence=0.6
                        )
                        enriched_keywords_list.append(fallback_keyword)
                    except:
                        continue
                continue
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"✅ [OpenAIEnrichment] Enriched {len(enriched_keywords_list)} keywords in {duration:.1f} seconds")
        return {"enriched_keywords": enriched_keywords_list}
        
    def validate_output(self, enrichment: EnrichedKeyword) -> bool:
        """Validate the content of the enriched keyword data."""
        if not enrichment:
            return False
            
        # Validate headline and description lengths
        if any(len(h) > 30 for h in enrichment.headlines):
            logging.warning(f"Invalid headline length for keyword: {enrichment.keyword_id}")
            return False
        if any(len(d) > 90 for d in enrichment.descriptions):
            logging.warning(f"Invalid description length for keyword: {enrichment.keyword_id}")
            return False
        if not 0 <= enrichment.confidence <= 1:
            logging.warning(f"Invalid confidence score for keyword: {enrichment.keyword_id}")
            return False
            
        return True