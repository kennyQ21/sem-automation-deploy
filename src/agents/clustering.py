"""
Clustering agent for creating ad groups using embeddings.
"""
import logging
from typing import List, Dict, Any
import numpy as np
import hdbscan
from .base import BaseAgent
from src.schemas.state import GlobalState, AdGroup
from src.services.cache import CacheService
from .fallback_naming import FallbackNaming

class ClusteringAgent(BaseAgent):
    """Agent for clustering keywords into ad groups with robust error handling."""

    def __init__(self, openai_client):
        """
        Initializes the agent with the OpenAI client needed for naming clusters.
        """
        self.client = openai_client
        self.cache = CacheService()

    def __call__(self, state: GlobalState) -> Dict[str, Any]:
        """Cluster keywords into ad groups using HDBSCAN."""
        from datetime import datetime
        start_time = datetime.now()
        print(f"🔍 [ClusteringAgent] Starting keyword clustering at {start_time.strftime('%H:%M:%S')}")
        
        # Input validation: Ensure there's enough data to cluster.
        if not state.embeddings:
            print(f"⚠️ [ClusteringAgent] No embeddings to cluster")
            return {
                "ad_groups": [],
                "clustering_attempts": state.clustering_attempts + 1
            }
        
        # If too few keywords, create simple groups
        if len(state.embeddings) < 3:
            print(f"⚠️ [ClusteringAgent] Too few embeddings ({len(state.embeddings)}), creating simple groups")
            keywords = list(state.embeddings.keys())
            ad_groups = []
            for i, keyword in enumerate(keywords):
                ad_groups.append(AdGroup(
                    id=f"group_{i}",
                    name=f"Keywords Group {i+1}",
                    keywords=[keyword],
                    centroid=state.embeddings[keyword],
                    score=0.8
                ))
            return {
                "ad_groups": ad_groups,
                "clustering_attempts": state.clustering_attempts + 1
            }

        keyword_ids = list(state.embeddings.keys())
        embeddings_array = np.array(list(state.embeddings.values()))
        
        if embeddings_array.ndim != 2:
            logging.error(f"ClusteringAgent: Embeddings array has incorrect shape {embeddings_array.shape}. Skipping.")
            return {
                "ad_groups": [],
                "clustering_attempts": state.clustering_attempts + 1
            }

        # Perform clustering with error handling.
        try:
            # Fast clustering with minimal parameters
            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=2,
                min_samples=1,
                metric='euclidean'
            )
            cluster_labels = clusterer.fit_predict(embeddings_array)
        except Exception as e:
            logging.error(f"HDBSCAN clustering failed: {e}")
            # Fallback: create simple groups
            ad_groups = []
            for i, keyword in enumerate(keyword_ids):
                ad_groups.append(AdGroup(
                    id=f"fallback_group_{i}",
                    name=f"Keyword Group {i+1}",
                    keywords=[keyword],
                    centroid=embeddings_array[i].tolist(),
                    score=0.7
                ))
            return {"ad_groups": ad_groups}
        
        ad_groups = []
        unique_clusters = set(cluster_labels)
        
        # Handle noise points (-1) by creating individual groups
        noise_indices = np.where(cluster_labels == -1)[0]
        if len(noise_indices) > 0:
            for i, idx in enumerate(noise_indices):
                keyword = keyword_ids[idx]
                ad_groups.append(AdGroup(
                    id=f"noise_group_{i}",
                    name=f"Individual Keywords {i+1}",
                    keywords=[keyword],
                    centroid=embeddings_array[idx].tolist(),
                    score=0.6
                ))
        
        # Process actual clusters
        for cluster_id in unique_clusters:
            if cluster_id == -1:  # Skip noise, already handled
                continue
                
            cluster_indices = np.where(cluster_labels == cluster_id)[0]
            if len(cluster_indices) == 0: 
                continue

            cluster_keywords = [keyword_ids[i] for i in cluster_indices]
            centroid = embeddings_array[cluster_indices].mean(axis=0)
            
            # Safe score calculation
            try:
                score = float(clusterer.probabilities_[cluster_indices].mean()) if hasattr(clusterer, 'probabilities_') else 0.8
            except:
                score = 0.8
            
            # Generate a name for the ad group.
            name = self._generate_group_name(cluster_keywords)
            
            ad_groups.append(AdGroup(
                id=f"group_{cluster_id}", 
                name=name, 
                keywords=cluster_keywords,
                centroid=centroid.tolist(), 
                score=score
            ))
        
        # Ensure we have at least one ad group
        if not ad_groups and keyword_ids:
            ad_groups.append(AdGroup(
                id="default_group",
                name="All Keywords",
                keywords=keyword_ids,
                centroid=embeddings_array.mean(axis=0).tolist(),
                score=0.7
            ))
            
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"✅ [ClusteringAgent] Created {len(ad_groups)} ad groups in {duration:.1f} seconds")
        
        # Increment clustering attempts counter
        return {
            "ad_groups": ad_groups,
            "clustering_attempts": state.clustering_attempts + 1
        }
        
    def _generate_group_name(self, keywords: List[str]) -> str:
        """Generate a name for the ad group using OpenAI with a fallback."""
        if not keywords: return "Unnamed Group"
        try:
            keyword_str = ", ".join(keywords[:5]) # Use first 5 for brevity.
            prompt = f"Generate a short, concise (2-3 words max) ad group name that summarizes this keyword theme: {keyword_str}"
            
            # Check cache first
            cached_response = self.cache.get(prompt)
            if cached_response:
                return cached_response.strip().replace('"', '')
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=30
            )
            result = response.choices[0].message.content.strip().replace('"', '')
            # Cache the response
            self.cache.set(prompt, result)
            return result
        except Exception as e:
            logging.error(f"Failed to generate group name with OpenAI: {e}")
            # Use intelligent fallback naming
            from .fallback_naming import FallbackNaming
            return FallbackNaming.generate_group_name(keywords)