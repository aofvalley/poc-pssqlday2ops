import streamlit as st
import msal

def get_azure_token(secrets):
    """Obtener token de autenticación de Azure AD"""
    try:
        app = msal.ConfidentialClientApplication(
            client_id=secrets.get("client_id"),
            client_credential=secrets.get("client_secret"),
            authority=f"https://login.microsoftonline.com/{secrets.get('tenant_id')}"
        )
        
        result = app.acquire_token_for_client(scopes=[secrets.get("scope")])
        
        if "access_token" in result:
            return result["access_token"]
        else:
            st.error(f"Error getting token: {result.get('error_description', 'Unknown error')}")
            return None
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return None
