import json
import logging
import os
from typing import Optional, Dict, Any, Union

import azure.functions as func
import requests
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI(title="PostgreSQL Backup and Restore API",
              description="API for triggering PostgreSQL backup and restore workflows")

class WorkflowRequest(BaseModel):
    pg_host_prod: str
    pg_host_dev: str
    pg_database: str
    pg_user: str
    resource_group: str

@app.get("/api/health")
async def health_check():
    """Health check endpoint to verify the API is running."""
    return {"status": "healthy", "version": "1.0.0"}

@app.post("/api/workflow/trigger", status_code=202)
async def trigger_workflow(workflow_data: WorkflowRequest):
    """
    Trigger a GitHub workflow to backup and restore a PostgreSQL database.
    """
    logging.info('Request received to trigger GitHub workflow.')
    
    # Get GitHub configuration from environment variables
    github_token = os.environ.get('GITHUB_TOKEN')
    github_owner = os.environ.get('GITHUB_OWNER')
    github_repo = os.environ.get('GITHUB_REPO')
    github_workflow_id = os.environ.get('GITHUB_WORKFLOW_ID', 'pg-backup-restore.yml')
    
    if not all([github_token, github_owner, github_repo]):
        raise HTTPException(
            status_code=500,
            detail="Missing GitHub configuration in function app settings."
        )
    
    # Extract parameters from request
    inputs = {
        'pg_host_prod': workflow_data.pg_host_prod,
        'pg_host_dev': workflow_data.pg_host_dev,
        'pg_database': workflow_data.pg_database,
        'pg_user': workflow_data.pg_user,
        'resource_group': workflow_data.resource_group
    }
    
    logging.info(f"Received parameters: {inputs}")
    
    # Construct GitHub API URL to trigger workflow
    url = f"https://api.github.com/repos/{github_owner}/{github_repo}/actions/workflows/{github_workflow_id}/dispatches"
    
    # Prepare payload for GitHub API
    payload = {
        "ref": "main",  # or your default branch
        "inputs": inputs
    }
    
    # Prepare headers for GitHub API
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_token}",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    try:
        # Call GitHub API to trigger workflow
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 204:  # GitHub returns 204 No Content on success
            return {
                "message": "GitHub workflow triggered successfully",
                "workflowUrl": f"https://github.com/{github_owner}/{github_repo}/actions/workflows/{github_workflow_id}"
            }
        else:
            logging.error(f"GitHub API returned: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to trigger GitHub workflow: {response.text}"
            )
    except Exception as e:
        logging.exception("Exception occurred while triggering GitHub workflow")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/api/workflow/status")
async def get_workflow_status(run_id: Optional[str] = Query(None, description="Specific workflow run ID")):
    """
    Get status of GitHub workflow runs, optionally filtered by a specific run ID.
    """
    logging.info('Request received to check GitHub workflow status.')
    
    # Get GitHub configuration from environment variables
    github_token = os.environ.get('GITHUB_TOKEN')
    github_owner = os.environ.get('GITHUB_OWNER')
    github_repo = os.environ.get('GITHUB_REPO')
    
    if not all([github_token, github_owner, github_repo]):
        raise HTTPException(
            status_code=500,
            detail="Missing GitHub configuration in function app settings."
        )
    
    # Prepare headers for GitHub API
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    try:
        # If run ID provided, get specific run info, else get latest runs
        if run_id:
            url = f"https://api.github.com/repos/{github_owner}/{github_repo}/actions/runs/{run_id}"
            response = requests.get(url, headers=headers)
        else:
            # Get the latest workflow runs
            url = f"https://api.github.com/repos/{github_owner}/{github_repo}/actions/runs"
            response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"GitHub API returned: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to retrieve GitHub workflow status: {response.text}"
            )
    except Exception as e:
        logging.exception("Exception occurred while retrieving GitHub workflow status")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# Hook up Azure Functions integration
def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    """
    Azure Functions entry point that integrates with the FastAPI application.
    """
    return func.AsgiMiddleware(app).handle(req, context)
