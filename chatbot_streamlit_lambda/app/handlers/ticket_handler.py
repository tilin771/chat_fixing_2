import streamlit as st
from agents.ticketing_agent import run_ticketing
from botocore.exceptions import EventStreamError
from app.components.chat_ui import stream_response
from data.constants import Constants

def handle_ticket(user_input):
    """Procesa mensajes en modo ticket"""
    session_id = st.session_state["session_id"]

    if not st.session_state.get("ticket_iniciado", False):
        st.session_state["ticket_iniciado"] = True
        spinner_message = Constants.Spinners["ticket_create"]
        prompt = "Resumen de la conversación:\n"
        for msg in st.session_state["messages"]:
            rol = "Usuario" if msg["role"] == "user" else "Asistente"
            prompt += f"{rol}: {msg['content']}\n"
    else:
        spinner_message = Constants.Spinners["ticket_update"]
        prompt = user_input
        
    try:
        response_text = stream_response(run_ticketing, prompt, session_id, message_spinner=spinner_message)
        if Constants.Labels["end_ticket"] in response_text:
            st.session_state["ticket_finalizado"] = True
            
    except EventStreamError as e:
        st.error("Ocurrió un error. Intenta de nuevo más tarde.")
    finally:
        st.rerun()
