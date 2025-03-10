import azure.functions as func
from main import app

# Create the Azure Functions app
app = func.AsgiFunctionApp(app=app, http_auth_level=func.AuthLevel.FUNCTION)
