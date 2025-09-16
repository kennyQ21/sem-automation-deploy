"""
FastAPI application for SEM automation.
"""
import os
import json
from datetime import datetime
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.workflow_manager import WorkflowManager

app = FastAPI(
    title="SEM Automation API",
    description="Intelligent SEM campaign planning with LangGraph and OpenAI GPT-4",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GeneratePlanRequest(BaseModel):
    """Request model for plan generation."""
    brand_url: str
    competitor_urls: List[str]
    target_location: str
    monthly_budget: float
    business_category: str
    target_roas: float = 3.0

class JobStatus(BaseModel):
    """Response model for job status."""
    job_id: str
    status: str
    progress: float = 0.0
    results: Dict[str, Any] = None
    errors: List[str] = []

# Store job statuses in memory (use Redis in production)
job_statuses: Dict[str, JobStatus] = {}
    
@app.post("/api/v1/generate-plan", response_model=JobStatus)
async def generate_plan(
    request: GeneratePlanRequest,
    background_tasks: BackgroundTasks
) -> JobStatus:
    """Generate an SEM plan asynchronously."""
    try:
        # Initialize workflow manager
        workflow_manager = WorkflowManager()
        
        # Create initial job status
        job_status = JobStatus(
            job_id=f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            status="pending",
            progress=0.0
        )
        job_statuses[job_status.job_id] = job_status
        
        # Start workflow execution in background
        background_tasks.add_task(
            execute_workflow_task,
            workflow_manager,
            request.dict(),
            job_status.job_id
        )
        
        return job_status
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error starting plan generation: {str(e)}"
        )

@app.get("/api/v1/job/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str) -> JobStatus:
    """Get the status of a plan generation job."""
    if job_id not in job_statuses:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found"
        )
    return job_statuses[job_id]

async def execute_workflow_task(
    workflow_manager: WorkflowManager,
    request_data: Dict[str, Any],
    job_id: str
) -> None:
    """Execute workflow in background and update job status."""
    try:
        # Update status to running
        job_statuses[job_id].status = "running"
        job_statuses[job_id].progress = 0.1
        
        # Execute workflow
        result = await workflow_manager.execute_workflow(request_data)
        
        if result["status"] == "success":
            # Save deliverables to files
            save_deliverables(result["results"], job_id)
            
            # Update job status
            job_statuses[job_id].status = "completed"
            job_statuses[job_id].progress = 1.0
            job_statuses[job_id].results = result["results"]
            
        else:
            job_statuses[job_id].status = "failed"
            job_statuses[job_id].errors.append(result["error"])
            
    except Exception as e:
        job_statuses[job_id].status = "failed"
        job_statuses[job_id].errors.append(str(e))

def save_deliverables(results: Dict[str, Any], job_id: str) -> None:
    """Save campaign deliverables to files."""
    try:
        # Create output directory for job
        output_dir = f"data/jobs/{job_id}"
        os.makedirs(output_dir, exist_ok=True)
        
        # Save keyword groups
        if "ad_groups" in results:
            with open(f"{output_dir}/keyword_groups.csv", "w") as f:
                f.write("ad_group,keyword,intent,search_volume,suggested_bid\n")
                for group in results["ad_groups"]:
                    for kw in group["keywords"]:
                        f.write(f"{group['name']},{kw['keyword']}," +
                               f"{kw['intent']},{kw['search_volume']}," +
                               f"{kw['suggested_bid']}\n")
        
        # Save PMax assets
        if "pmax_campaigns" in results:
            with open(f"{output_dir}/pmax_assets.json", "w") as f:
                json.dump(results["pmax_campaigns"], f, indent=2)
                
        # Save shopping campaign settings
        if "shopping_strategies" in results:
            with open(f"{output_dir}/shopping_settings.json", "w") as f:
                json.dump(results["shopping_strategies"], f, indent=2)
            
            # Save detailed CPC calculations
            with open(f"{output_dir}/shopping_cpcs.csv", "w") as f:
                f.write("ad_group,keyword,search_volume,competition,target_cpa,computed_cpc\n")
                for strategy in results["shopping_strategies"]:
                    for bid in strategy["bidding"]["keyword_bids"]:
                        f.write(f"{strategy['ad_group']},{bid['keyword']}," +
                               f"{bid['search_volume']},{bid['competition']}," +
                               f"{bid['target_cpa']},{bid['computed_cpc']}\n")
                
    except Exception as e:
        print(f"Error saving deliverables: {str(e)}")
                   
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)