"""
LangGraph nodes for keyword generation and vector operations using PostgreSQL.
"""
import json
from typing import Dict, Any, List
from sentence_transformers import SentenceTransformer
from src.schemas.state import GlobalState
from .base import BaseAgent
from src.services.database import DatabaseService

class KeywordGenerator(BaseAgent):
    """Node for generating seed keywords using OpenAI."""
    def __init__(self, openai_client):
        self.client = openai_client
        
    def __call__(self, state: GlobalState) -> Dict[str, Any]:
        from datetime import datetime
        start_time = datetime.now()
        print(f"🌱 [KeywordGenerator] Starting seed keyword generation at {start_time.strftime('%H:%M:%S')}")
        
        brand_analysis = state.brand_analysis
        prompt = f"""As a strategic SEM keyword planner, generate 15 high-intent seed keywords
        based on this brand analysis: {brand_analysis.dict() if brand_analysis else {}}.
        Return only a JSON array of keyword strings like: ["keyword1", "keyword2", "keyword3"]"""
        
        print(f"🤖 [KeywordGenerator] Calling OpenAI GPT-4o-mini...")
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=200
        )
        response_text = response.choices[0].message.content.strip()
        cleaned_text = response_text.lstrip("```json").rstrip("```")
        seed_keywords = json.loads(cleaned_text)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"✅ [KeywordGenerator] Generated {len(seed_keywords)} keywords in {duration:.1f} seconds")
        
        return {"seed_keywords": seed_keywords}

class VectorManager:
    """Node for managing keyword vectors in PostgreSQL."""
    def __init__(self, database_service: DatabaseService):
        self.db_service = database_service
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
    def _generate_vector(self, keyword: str) -> List[float]:
        return self.model.encode(keyword).tolist()
        
    def __call__(self, state: GlobalState) -> Dict[str, Any]:
        from datetime import datetime
        start_time = datetime.now()
        print(f"🔢 [VectorManager] Starting vector generation at {start_time.strftime('%H:%M:%S')}")
        
        if not state.raw_keywords:
            print(f"⚠️ [VectorManager] No keywords to vectorize")
            return {"error_log": state.error_log + ["No keywords to vectorize"]}
            
        job_id = state.job_id
        vectors_to_upsert = []
        embeddings_for_state = {}
        
        print(f"🔢 [VectorManager] Processing {len(state.raw_keywords)} keywords...")
        for kw in state.raw_keywords:
            vector = self._generate_vector(kw.keyword)
            embeddings_for_state[kw.keyword] = vector
            vectors_to_upsert.append({
                'id': kw.keyword,
                'vector': vector,
                'metadata': {'search_volume': kw.avg_monthly_searches, 'competition': kw.competition}
            })
        
        self.db_service.upsert_keywords(job_id, vectors_to_upsert)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"✅ [VectorManager] Generated {len(embeddings_for_state)} vectors in {duration:.1f} seconds")
        
        return {"embeddings": embeddings_for_state}