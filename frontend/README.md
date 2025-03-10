# PostgreSQL Backup & Restore Frontend

Este es un frontend de Streamlit para la API de PostgreSQL Backup and Restore que permite ejecutar y monitorear los workflows de backup y restauración.

## Requisitos

- Python 3.8+
- Streamlit y otras dependencias listadas en `requirements.txt`
- La API de PostgreSQL Backup and Restore debe estar corriendo

## Instalación

1. Instala las dependencias:
```bash
pip install -r requirements.txt
```

2. Ejecuta la aplicación Streamlit:
```bash
streamlit run streamlit_app.py
```

3. Accede a la aplicación en tu navegador:
```
http://localhost:8501
```

## Funcionalidades

- **Dashboard**: Muestra una visión general del estado del sistema
- **Ejecutar Workflows**: Formulario para iniciar workflows de backup/restore
- **Monitoreo**: Visualización detallada del estado de ejecución de los workflows
- **Configuración**: Información sobre la configuración actual de la API

## Configuración

Al iniciar la aplicación, puedes configurar la URL base de la API en la barra lateral. Por defecto, se utiliza `http://localhost:7071`.
