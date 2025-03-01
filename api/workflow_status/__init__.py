import json
import logging
import os

import azure.functions as func
import requests

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request to check GitHub workflow status.')
    
    # Get GitHub configuration from environment variables
    github_token = os.environ.get('GITHUB_TOKEN')
    github_owner = os.environ.get('GITHUB_OWNER')
    github_repo = os.environ.get('GITHUB_REPO')
    
    if not all([github_token, github_owner, github_repo]):
        return func.HttpResponse(
            json.dumps({
                "error": "Missing GitHub configuration in function app settings."
            }),
            status_code=500,
            mimetype="application/json"
        )
    
    # Check if a specific run ID was provided
    run_id = req.params.get('runId')
    
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
            return func.HttpResponse(
                response.text,
                status_code=200,
                mimetype="application/json"
            )
        else:
            logging.error(f"GitHub API returned: {response.status_code} - {response.text}")
            return func.HttpResponse(
                json.dumps({
                    "error": "Failed to retrieve GitHub workflow status",
                    "details": response.text
                }),
                status_code=response.status_code,
                mimetype="application/json"
            )
    except Exception as e:
        logging.exception("Exception occurred while retrieving GitHub workflow status")
        return func.HttpResponse(
            json.dumps({
                "error": str(e)
            }),
            status_code=500,
            mimetype="application/json"
        )
