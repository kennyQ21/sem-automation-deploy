"""
Core workflow definition for the SEM automation system.
"""
from typing import Dict, Any
from datetime import datetime
from langgraph.graph import StateGraph, END
from openai import OpenAI
from src.schemas.state import GlobalState
from src.agents.website_analyzer import WebsiteAnalyzer
from src.agents.vector_ops import VectorManager, KeywordGenerator
from src.agents.clustering import ClusteringAgent
from src.agents.campaign import CampaignDesignerAgent
from src.agents.keyword_processor import KeywordProcessor
from src.agents.openai_enrichment import OpenAIEnrichmentAgent
from src.agents.mock_agents import MockWebsiteAnalyzer, MockKeywordGenerator, MockEnrichmentAgent, MockClusteringAgent
from src.services.google_ads import GoogleAdsClient
from src.services.database import DatabaseService

class WorkflowBuilder:
    def __init__(self, config: Dict[str, Any]):
        """Initializes all services and agents required for the workflow."""
        self.openai_client = OpenAI(api_key=config['openai_api_key'])
        
        # Initialize external services
        self.db_service = DatabaseService(config['database_url'])
        self.google_ads = GoogleAdsClient(config['google_ads_config_path'])
        
        # Initialize all agents with real APIs
        print(f"✅ Initializing real agents with OpenAI GPT-4o-mini")
        self.website_analyzer = WebsiteAnalyzer(self.openai_client)
        self.keyword_generator = KeywordGenerator(self.openai_client)
        self.enrichment_agent = OpenAIEnrichmentAgent(config['openai_api_key'])
        self.clusterer = ClusteringAgent(self.openai_client)
        self.use_mock_agents = False
        
        self.vector_ops = VectorManager(self.db_service)
        self.keyword_processor = KeywordProcessor()
        self.campaign_generator = CampaignDesignerAgent(self.openai_client)
    
    def _fetch_keywords(self, state: GlobalState) -> Dict[str, Any]:
        """Node for fetching keywords from Google Ads based on seed keywords."""
        start_time = datetime.now()
        print(f"🔍 [GoogleAds] Starting keyword fetch at {start_time.strftime('%H:%M:%S')}")
        
        try:
            seed_keywords = state.seed_keywords
            if not seed_keywords:
                print(f"⚠️ [GoogleAds] No seed keywords provided")
                return {"error_log": state.error_log + ["No seed keywords were generated to fetch."]}
            
            print(f"🔍 [GoogleAds] Fetching keywords for {len(seed_keywords)} seed keywords...")
            raw_keywords = self.google_ads.fetch_keyword_ideas(seed_keywords)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            print(f"✅ [GoogleAds] Fetched {len(raw_keywords)} keywords in {duration:.1f} seconds")
            
            return {"raw_keywords": raw_keywords}
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            print(f"❌ [GoogleAds] Failed after {duration:.1f} seconds: {str(e)}")
            return {"error_log": state.error_log + [f"Keyword fetch error: {str(e)}"]}
    
    def _should_recluster(self, state: GlobalState) -> str:
        """Decision node for evaluating the quality of keyword clusters."""
        ad_groups = state.ad_groups or []
        
        # If no embeddings or keywords, skip clustering and go to campaign generation
        if not getattr(state, 'embeddings', None) or not state.embeddings:
            print("⚠️ [ClusteringDecision] No embeddings available, proceeding to campaign generation")
            return "continue_processing"
            
        if not ad_groups:
            # Only try clustering once if no groups exist
            if state.clustering_attempts >= 3:  # Max 3 attempts
                print("⚠️ [ClusteringDecision] Max clustering attempts reached, proceeding anyway")
                return "continue_processing"
                
            return "recluster"
            
        # Check for low-quality clusters
        poor_clusters = [
            g for g in ad_groups
            if len(g.keywords) < 3 or g.score < 0.7
        ]
        
        # If more than 30% of clusters are poor, re-run the clustering step (max 2 times)
        if len(poor_clusters) > len(ad_groups) * 0.3:
            if state.clustering_attempts >= 2:  # Max 2 re-clustering attempts
                print("⚠️ [ClusteringDecision] Max re-clustering attempts reached")
                return "continue_processing"
                
            return "recluster"
            
        return "continue_processing"
    
    def create_workflow(self) -> StateGraph:
        """Builds and configures the definitive, logical workflow graph."""
        workflow = StateGraph(GlobalState)
        
        # Add all the nodes that will participate in the graph.
        workflow.add_node("analyze_websites", self.website_analyzer)
        workflow.add_node("generate_seed_keywords", self.keyword_generator)
        workflow.add_node("fetch_keywords", self._fetch_keywords)
        workflow.add_node("process_keywords", self.keyword_processor)
        workflow.add_node("enrich_keywords", self.enrichment_agent)
        workflow.add_node("manage_vectors", self.vector_ops)
        workflow.add_node("cluster_keywords", self.clusterer)
        workflow.add_node("generate_campaigns", self.campaign_generator)
        
        # --- CORRECTED: Define the graph with a logical data flow ---
        
        # 1. Start by analyzing the websites to get context.
        workflow.set_entry_point("analyze_websites")
        
        # 2. Use the analysis to generate initial seed keywords.
        workflow.add_edge("analyze_websites", "generate_seed_keywords")
        
        # 3. Use the seed keywords to fetch a larger list from the Google Ads API.
        workflow.add_edge("generate_seed_keywords", "fetch_keywords")
        
        # 4. Filter and score the raw keywords to find the most valuable ones.
        workflow.add_edge("fetch_keywords", "process_keywords")
        
        # 5. Enrich the valuable keywords with creative ideas and intent.
        workflow.add_edge("process_keywords", "enrich_keywords")
        
        # 6. Create vector embeddings for the enriched keywords and save them.
        workflow.add_edge("enrich_keywords", "manage_vectors")
        
        # 7. Group the keywords into semantically related ad groups.
        workflow.add_edge("manage_vectors", "cluster_keywords")
        
        # 8. Add a conditional edge for clustering quality.
        workflow.add_conditional_edges(
            "cluster_keywords",
            self._should_recluster,
            {
                "recluster": "cluster_keywords", # If quality is low, try again.
                "continue_processing": "generate_campaigns" # If quality is good, proceed.
            }
        )
        
        # 9. Finally, use the ad groups to design the final campaign structure.
        workflow.add_edge("generate_campaigns", END)
        
        # Set recursion limit to prevent infinite loops
        return workflow.compile(checkpointer=None, debug=False)
    
    async def execute_workflow(self, initial_request: Dict[str, Any]) -> Dict[str, Any]:
        """Executes the compiled workflow with proper state and error handling."""
        start_time = datetime.now()
        print(f"🚀 Starting workflow execution at {start_time.strftime('%H:%M:%S')}")
        
        workflow = self.create_workflow()
            
        # Prepare the initial state that will be passed through the graph.
        initial_state = GlobalState(
            initial_request=initial_request,
            job_id=f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            error_log=[],
            brand_analysis=None,
            competitor_analysis=None,
            seed_keywords=None,
            raw_keywords=None,
            enriched_keywords=None,
            embeddings={},
            ad_groups=None,
            campaigns=None,
            final_report=None
        )
            
        try:
            # Asynchronously invoke the workflow with recursion limit.
            print(f"⏱️ Invoking workflow graph...")
            final_state = await workflow.ainvoke(
                initial_state, 
                config={"recursion_limit": 50}
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            print(f"✅ Workflow completed in {duration:.1f} seconds")
            
            # Handle both dict and object responses
            if hasattr(final_state, 'error_log'):
                error_log = final_state.error_log or []
            elif isinstance(final_state, dict):
                error_log = final_state.get('error_log', [])
            else:
                error_log = []
                
            if error_log:
                print(f"⚠️ Workflow completed with errors: {error_log}")

            # Get results safely
            if hasattr(final_state, 'final_report'):
                results = final_state.final_report
            elif isinstance(final_state, dict):
                results = final_state.get('final_report')
            else:
                results = None

            return {
                "status": "success",
                "job_id": initial_state.job_id,
                "results": results,
                "errors": error_log
            }
            
        except Exception as e:
            # Handle critical, unrecoverable errors that halt the graph.
            job_id = initial_state.job_id
            print(f"A critical error occurred during workflow execution for job {job_id}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "job_id": job_id
            }