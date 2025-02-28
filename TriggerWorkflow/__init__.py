import json
import os
import logging
import requests
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request to trigger workflow.')

    # Get GitHub API configuration from settings
    github_owner = os.environ.get('GITHUB_OWNER')
    github_repo = os.environ.get('GITHUB_REPO')
    workflow_id = os.environ.get('GITHUB_WORKFLOW_ID')
    github_token = os.environ.get('GITHUB_TOKEN')
    
    # Validate required environment variables
    if not all([github_owner, github_repo, workflow_id, github_token]):
        return func.HttpResponse(
            "GitHub configuration environment variables are missing.",
            status_code=500
        )

    try:
        # Parse request body
        req_body = req.get_json()
        
        # Validate required parameters
        required_params = [
            'pg_host_prod', 'pg_host_dev', 'pg_database', 
            'pg_user', 'pg_password', 'azure_storage_account', 
            'azure_storage_container'
        ]
        
        for param in required_params:
            if param not in req_body:
                return func.HttpResponse(
                    f"Missing required parameter: {param}",
                    status_code=400
                )
        
        # Prepare the GitHub API request
        url = f"https://api.github.com/repos/{github_owner}/{github_repo}/actions/workflows/{workflow_id}/dispatches"
        headers = {
            'Authorization': f'Bearer {github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
        
        # Prepare the workflow inputs
        payload = {
            'ref': 'main',  # or your default branch
            'inputs': {
                'pg_host_prod': req_body.get('pg_host_prod'),
                'pg_host_dev': req_body.get('pg_host_dev'),
                'pg_database': req_body.get('pg_database'),
                'pg_user': req_body.get('pg_user'),
                'pg_password': req_body.get('pg_password'),
                'azure_storage_account': req_body.get('azure_storage_account'),
                'azure_storage_container': req_body.get('azure_storage_container')
            }
        }
        
        # Trigger the GitHub workflow
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        # Handle the response
        if response.status_code == 204:  # GitHub returns 204 No Content on success
            return func.HttpResponse(
                json.dumps({
                    'message': 'Workflow triggered successfully',
                    'checkStatusUrl': f'/api/workflow/status?owner={github_owner}&repo={github_repo}'
                }),
                status_code=200,
                mimetype="application/json"
            )
        else:
            return func.HttpResponse(
                json.dumps({
                    'message': 'Failed to trigger workflow',
                    'status_code': response.status_code,
                    'response': response.text
                }),
                status_code=400,
                mimetype="application/json"
            )
            
    except ValueError:
        return func.HttpResponse(
            "Invalid request body. JSON expected.",
            status_code=400
        )
    except Exception as e:
        logging.error(f"Error triggering workflow: {str(e)}")
        return func.HttpResponse(
            f"An error occurred: {str(e)}",
            status_code=500
        )