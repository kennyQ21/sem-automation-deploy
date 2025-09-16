"""
Workflow manager for orchestrating the SEM automation pipeline.
"""
import logging
from typing import Dict, Any
from src.workflow import WorkflowBuilder
from src.config import load_config

class WorkflowManager:
    def __init__(self):
        self.config = load_config()
        self.workflow_builder = WorkflowBuilder(self.config)
            
    async def execute_workflow(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Call the workflow builder's execute method directly
            result_dict = await self.workflow_builder.execute_workflow(request_data)
            
            if result_dict.get("status") == "error":
                return {"status": "failed", "error": result_dict.get("error")}
            
            final_report = result_dict.get("results")
            if not final_report:
                # Check for errors in different formats
                errors = result_dict.get("errors", [])
                if hasattr(result_dict, 'error_log'):
                    errors.extend(result_dict.error_log)
                elif isinstance(result_dict, dict) and 'error_log' in result_dict:
                    errors.extend(result_dict['error_log'])
                
                error_msg = "Workflow finished but produced no report."
                if errors:
                    error_msg += f" Errors: {'; '.join(errors)}"
                return {"status": "failed", "error": error_msg}
                
            # Format results into the exact structure the frontend expects
            formatted_results = {
                "search_campaign": final_report.get("search_campaign", {"ad_groups": []}),
                "shopping_campaign": final_report.get("shopping_campaign", {"product_bids": []}),
                "pmax_campaign": final_report.get("pmax_campaign", {"themes": []})
            }

            return {"status": "success", "results": formatted_results}
            
        except Exception as e:
            logging.exception("Critical error in WorkflowManager")
            return {"status": "failed", "error": str(e)}