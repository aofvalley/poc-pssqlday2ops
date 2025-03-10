import logging
import azure.functions as func
from azure.functions import AsgiMiddleware

# Importar config primero para cargar los secretos
import config
import main

# Configurar el logging
logging.info("Iniciando aplicación Azure Functions con FastAPI")

# Create the ASGI middleware
asgi_handler = AsgiMiddleware(main.app)

# Create a function app that properly exposes the function for Azure Functions
app = func.FunctionApp()

# Define a route for all HTTP requests
@app.route(route="{*route}", auth_level=func.AuthLevel.FUNCTION, methods=["GET", "POST"])
def handle_http(req: func.HttpRequest) -> func.HttpResponse:
    """Main entry point for the Azure Function."""
    return asgi_handler.handle(req)
