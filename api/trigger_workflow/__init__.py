import json
import logging
import os

import azure.functions as func
import requests

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request to trigger GitHub workflow.')
    
    # Get GitHub configuration from environment variables
    github_token = os.environ.get('GITHUB_TOKEN')
    github_owner = os.environ.get('GITHUB_OWNER')
    github_repo = os.environ.get('GITHUB_REPO')
    github_workflow_id = os.environ.get('GITHUB_WORKFLOW_ID', 'pg-backup-restore.yml')
    
    if not all([github_token, github_owner, github_repo]):
        return func.HttpResponse(
            json.dumps({
                "error": "Missing GitHub configuration in function app settings."
            }),
            status_code=500,
            mimetype="application/json"
        )
    
    # Get parameters from request
    try:
        req_body = req.get_json()
        
        # Extract parameters 
        params = {
            'pg_host_prod': req_body.get('pg_host_prod'),
            'pg_host_dev': req_body.get('pg_host_dev'),
            'pg_database': req_body.get('pg_database'),
            'pg_user': req_body.get('pg_user'),
            'resource_group': req_body.get('resource_group')
        }
        
        # Remove None values
        inputs = {k: v for k, v in params.items() if v is not None}
        
        logging.info(f"Received parameters: {inputs}")
        
    except ValueError:
        # If no body provided, use empty inputs
        inputs = {}
    
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
            return func.HttpResponse(
                json.dumps({
                    "message": "GitHub workflow triggered successfully",
                    "workflowUrl": f"https://github.com/{github_owner}/{github_repo}/actions/workflows/{github_workflow_id}"
                }),
                status_code=202,
                mimetype="application/json"
            )
        else:
            logging.error(f"GitHub API returned: {response.status_code} - {response.text}")
            return func.HttpResponse(
                json.dumps({
                    "error": "Failed to trigger GitHub workflow",
                    "details": response.text
                }),
                status_code=500,
                mimetype="application/json"
            )
    except Exception as e:
        logging.exception("Exception occurred while triggering GitHub workflow")
        return func.HttpResponse(
            json.dumps({
                "error": str(e)
            }),
            status_code=500,
            mimetype="application/json"
        )
