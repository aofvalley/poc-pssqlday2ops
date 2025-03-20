import json
import logging
import os
import time
import datetime
from typing import Optional, Dict, Any, Union, List

import azure.functions as func
import requests
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

# Importar la configuración
from config import get_github_config

# Set the path for the docs - ensure it works when deployed
app = FastAPI(
    title="PostgreSQL Backup and Restore API",
    description="API for triggering PostgreSQL backup and restore workflows",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

class WorkflowRequest(BaseModel):
    pg_host_prod: str
    pg_host_dev: str
    pg_database: str
    pg_user: str
    pg_password: str  # New field for database password
    resource_group: str
    storage_account: str  # New field for storage account
    storage_container: str  # New field for storage container

class HealthStatus(BaseModel):
    status: str
    version: str
    timestamp: str
    uptime: float
    github_api_status: str
    github_config_status: str
    details: Dict[str, Any]

# Variable para almacenar el tiempo de inicio de la aplicación
start_time = time.time()

@app.get("/api/health", response_model=HealthStatus)
async def health_check():
    """
    Health check endpoint que verifica varios componentes del sistema:
    - Estado general de la API
    - Conectividad con la API de GitHub
    - Configuración de GitHub cargada correctamente
    """
    logging.info("Ejecutando verificación de salud completa del sistema")
    
    # Obtener la configuración de GitHub
    github_config = get_github_config()
    config_status = "ok" if all([
        github_config["token"], 
        github_config["owner"], 
        github_config["repo"]
    ]) else "error"
    
    # Verificar conectividad con la API de GitHub
    github_api_status = "unknown"
    github_api_details = {}
    try:
        response = requests.get("https://api.github.com/rate_limit", 
                           headers={"Authorization": f"Bearer {github_config['token']}"} if github_config['token'] else {})
        if response.status_code == 200:
            github_api_status = "ok"
            rate_limit_data = response.json()
            github_api_details = {
                "rate_limit": {
                    "limit": rate_limit_data["rate"]["limit"],
                    "remaining": rate_limit_data["rate"]["remaining"],
                    "reset_at": datetime.datetime.fromtimestamp(rate_limit_data["rate"]["reset"]).isoformat()
                }
            }
        else:
            github_api_status = "error"
            github_api_details = {"error": f"Status code: {response.status_code}", "message": response.text}
    except Exception as e:
        github_api_status = "error"
        github_api_details = {"error": str(e)}
    
    # Calcular tiempo de actividad
    uptime_seconds = time.time() - start_time
    
    # Determinar estado general
    overall_status = "healthy" if github_api_status == "ok" and config_status == "ok" else "degraded"
    
    return HealthStatus(
        status=overall_status,
        version="1.1.0",
        timestamp=datetime.datetime.now().isoformat(),
        uptime=round(uptime_seconds, 2),
        github_api_status=github_api_status,
        github_config_status=config_status,
        details={
            "github_api": github_api_details,
            "environment": {
                "python_version": os.environ.get("PYTHON_VERSION", "unknown"),
                "function_name": os.environ.get("FUNCTIONS_WORKER_RUNTIME", "unknown")
            }
        }
    )

@app.get("/api/config")
async def get_config():
    """
    Endpoint para verificar la configuración cargada (sin mostrar secretos completos).
    """
    config = get_github_config()
    # Ocultar el token para seguridad
    if config["token"]:
        config["token"] = config["token"][:5] + "..." + config["token"][-5:]
    
    return {
        "github_owner": config["owner"],
        "github_repo": config["repo"],
        "github_workflow_id": config["workflow_id"],
        "token_loaded": bool(config["token"])
    }

@app.post("/api/workflow/dump-restore", status_code=202)
async def dump_restore_workflow(workflow_data: WorkflowRequest):
    """
    Ejecuta un workflow de GitHub para hacer backup y restauración de una base de datos PostgreSQL.
    """
    logging.info('Request received to execute PostgreSQL dump-restore workflow.')
    
    # Obtener la configuración de GitHub
    github_config = get_github_config()
    github_token = github_config["token"]
    github_owner = github_config["owner"]
    github_repo = github_config["repo"]
    github_workflow_id = github_config["workflow_id"]
    
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
        'pg_password': workflow_data.pg_password,  # Add password
        'resource_group': workflow_data.resource_group,
        'storage_account': workflow_data.storage_account,  # Add storage account
        'storage_container': workflow_data.storage_container  # Add storage container
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
                "message": "PostgreSQL dump-restore workflow initiated successfully",
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
    Get status of GitHub workflow runs, with detailed job and step information.
    If no run_id is provided, returns the latest run with details.
    """
    logging.info('Request received to check GitHub workflow status.')
    
    # Obtener la configuración de GitHub
    github_config = get_github_config()
    github_token = github_config["token"]
    github_owner = github_config["owner"]
    github_repo = github_config["repo"]
    
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
        if run_id is None:
            # Get latest workflow run
            runs_url = f"https://api.github.com/repos/{github_owner}/{github_repo}/actions/runs"
            response = requests.get(runs_url, headers=headers)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to retrieve workflow runs: {response.text}"
                )
                
            runs_data = response.json()
            if not runs_data["workflow_runs"]:
                return {
                    "message": "No workflow runs found",
                    "runs_count": 0
                }
                
            # Get the most recent run
            run_id = runs_data["workflow_runs"][0]["id"]
        
        # Get detailed information about the run
        run_url = f"https://api.github.com/repos/{github_owner}/{github_repo}/actions/runs/{run_id}"
        run_response = requests.get(run_url, headers=headers)
        
        if run_response.status_code != 200:
            raise HTTPException(
                status_code=run_response.status_code,
                detail=f"Failed to retrieve run details: {run_response.text}"
            )
            
        run_data = run_response.json()
        
        # Get jobs for this run
        jobs_url = f"https://api.github.com/repos/{github_owner}/{github_repo}/actions/runs/{run_id}/jobs"
        jobs_response = requests.get(jobs_url, headers=headers)
        
        if jobs_response.status_code != 200:
            raise HTTPException(
                status_code=jobs_response.status_code,
                detail=f"Failed to retrieve job details: {jobs_response.text}"
            )
            
        jobs_data = jobs_response.json()
        
        # Calculate duration and format timestamps
        if run_data.get("created_at"):
            created_at = datetime.datetime.strptime(run_data["created_at"], "%Y-%m-%dT%H:%M:%SZ")
            
            if run_data.get("updated_at"):
                updated_at = datetime.datetime.strptime(run_data["updated_at"], "%Y-%m-%dT%H:%M:%SZ")
                duration_seconds = (updated_at - created_at).total_seconds()
            else:
                duration_seconds = (datetime.datetime.utcnow() - created_at).total_seconds()
                
            run_data["duration"] = {
                "seconds": round(duration_seconds),
                "formatted": format_duration(duration_seconds)
            }
        
        # Format job steps
        formatted_jobs = []
        for job in jobs_data.get("jobs", []):
            job_steps = []
            for step in job.get("steps", []):
                # Calculate step duration
                step_duration = None
                if step.get("started_at") and step.get("completed_at"):
                    started = datetime.datetime.strptime(step["started_at"], "%Y-%m-%dT%H:%M:%SZ")
                    completed = datetime.datetime.strptime(step["completed_at"], "%Y-%m-%dT%H:%M:%SZ")
                    step_duration = (completed - started).total_seconds()
                
                job_steps.append({
                    "name": step.get("name", "Unknown step"),
                    "status": step.get("status", "unknown"),
                    "conclusion": step.get("conclusion", None),
                    "started_at": step.get("started_at"),
                    "completed_at": step.get("completed_at"),
                    "duration": format_duration(step_duration) if step_duration else None
                })
            
            # Calculate job duration
            job_duration = None
            if job.get("started_at") and job.get("completed_at"):
                job_started = datetime.datetime.strptime(job["started_at"], "%Y-%m-%dT%H:%M:%SZ")
                job_completed = datetime.datetime.strptime(job["completed_at"], "%Y-%m-%dT%H:%M:%SZ")
                job_duration = (job_completed - job_started).total_seconds()
            
            formatted_jobs.append({
                "id": job.get("id"),
                "name": job.get("name", "Unknown job"),
                "status": job.get("status", "unknown"),
                "conclusion": job.get("conclusion", None),
                "started_at": job.get("started_at"),
                "completed_at": job.get("completed_at"),
                "duration": format_duration(job_duration) if job_duration else None,
                "steps": job_steps
            })
        
        # Build enhanced response
        enhanced_response = {
            "id": run_data.get("id"),
            "name": run_data.get("name", "Unknown workflow"),
            "status": run_data.get("status", "unknown"),
            "conclusion": run_data.get("conclusion", None),
            "html_url": run_data.get("html_url"),
            "created_at": run_data.get("created_at"),
            "updated_at": run_data.get("updated_at"),
            "duration": run_data.get("duration"),
            "jobs": formatted_jobs,
            "raw_data_urls": {
                "run_url": run_url,
                "jobs_url": jobs_url
            }
        }
        
        return enhanced_response
    
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("Exception occurred while retrieving GitHub workflow status")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

def format_duration(seconds: float) -> str:
    """
    Formatea una duración en segundos a un formato legible.
    Por ejemplo: "2h 5m 30s" o "45s"
    """
    if seconds is None:
        return None
        
    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or hours > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    
    return " ".join(parts)

# Note: The Azure Functions integration now happens in function_app.py 
# so we don't need the original main() function here
