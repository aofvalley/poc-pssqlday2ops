import json
import os
import logging
from pathlib import Path

def load_secrets():
    """
    Carga los secretos desde el archivo secrets.json y los establece como variables de entorno
    si no están definidos ya.
    """
    try:
        # Ruta al archivo secrets.json (relativa a la raíz del proyecto)
        secrets_path = Path(__file__).parent.parent / 'secrets.json'
        
        if secrets_path.exists():
            logging.info(f"Cargando configuración desde {secrets_path}")
            with open(secrets_path, 'r') as file:
                secrets = json.load(file)
            
            # Establecer las variables solo si no están ya definidas en el entorno
            for key, value in secrets.items():
                if not os.environ.get(key):
                    os.environ[key] = value
                    logging.info(f"Variable de entorno {key} cargada desde secrets.json")
        else:
            logging.warning(f"El archivo {secrets_path} no existe. Usando solo variables de entorno.")
    except Exception as e:
        logging.error(f"Error al cargar secrets.json: {str(e)}")

# Cargar secretos al importar este módulo
load_secrets()

def get_github_config():
    """
    Obtiene la configuración de GitHub desde las variables de entorno.
    Estas variables pueden haberse cargado desde secrets.json.
    """
    return {
        "token": os.environ.get("GITHUB_TOKEN"),
        "owner": os.environ.get("GITHUB_OWNER"),
        "repo": os.environ.get("GITHUB_REPO"),
        "workflow_id": os.environ.get("GITHUB_WORKFLOW_ID", "pg-backup-restore.yml")
    }
