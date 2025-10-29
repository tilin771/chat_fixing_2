import uuid
import streamlit as st

def initialize_session():
    """Inicializa todas las variables de sesión necesarias"""
    defaults = {
        "messages": [],
        "session_id": str(uuid.uuid4()),
        "ultimo_estado": "",
        "modo_ticket": False,
        "ticket_iniciado": False,
        "modo_robot": False,
        "modo_robot_finalizado": False,
        "ticket_finalizado": False,
        "ia_inicializada": None  
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
