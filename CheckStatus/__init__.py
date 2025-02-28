import json
import os
import logging
import requests
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request to check workflow status.')

    # Get GitHub API configuration from settings
    github_owner = os.environ.get('GITHUB_OWNER')
    github_repo = os.environ.get('GITHUB_REPO')
    github_token = os.environ.get('GITHUB_TOKEN')
    
    # Allow override via query parameters
    owner = req.params.get('owner') or github_owner
    repo = req.params.get('repo') or github_repo
    run_id = req.params.get('runId')
    
    # Validate required parameters
    if not all([owner, repo, github_token]):
        return func.HttpResponse(
            "GitHub configuration environment variables are missing.",
            status_code=500
        )
    
    try:
        # If run_id is provided, check specific run
        if run_id:
            url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}"
            headers = {
                'Authorization': f'Bearer {github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return func.HttpResponse(
                    response.text,
                    status_code=200,
                    mimetype="application/json"
                )
            else:
                return func.HttpResponse(
                    json.dumps({
                        'message': 'Failed to get workflow run status',
                        'status_code': response.status_code,
                        'response': response.text
                    }),
                    status_code=400,
                    mimetype="application/json"
                )
        # Otherwise, list recent runs
        else:
            url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"
            headers = {
                'Authorization': f'Bearer {github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                # Return only the most recent workflows (first 5)
                data = response.json()
                recent_runs = data.get('workflow_runs', [])[:5]
                
                return func.HttpResponse(
                    json.dumps({
                        'message': 'Recent workflow runs',
                        'workflow_runs': recent_runs
                    }),
                    status_code=200,
                    mimetype="application/json"
                )
            else:
                return func.HttpResponse(
                    json.dumps({
                        'message': 'Failed to list workflow runs',
                        'status_code': response.status_code,
                        'response': response.text
                    }),
                    status_code=400,
                    mimetype="application/json"
                )
            
    except Exception as e:
        logging.error(f"Error checking workflow status: {str(e)}")
        return func.HttpResponse(
            f"An error occurred: {str(e)}",
            status_code=500
        )