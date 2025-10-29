import streamlit as st
from chatbot_streamlit_lambda.app.components.chat_ui import show_message
from chatbot_streamlit_lambda.app.handlers.kb_handler import handle_kb
from chatbot_streamlit_lambda.app.handlers.robot_handler import handle_robot
from chatbot_streamlit_lambda.app.handlers.ticket_handler import handle_ticket


def handle_action(decision, user_input):
    """
    Gestiona las acciones según la decisión del modelo o backend.
    Permite manejar distintos modos de interacción: KB, tickets, robots, etc.
    """
    accion = decision.get("action", "")

    if accion == "query_kb":
        handle_kb(user_input, decision)

    elif accion in ("create_ticket", "query_tickets"):
        st.session_state["modo_ticket"] = True
        handle_ticket(user_input)

    elif accion == "invoke_robot":
        st.session_state["modo_robot"] = True
        handle_robot(decision)

    else:
        # Si no hay acción específica, muestra la respuesta general
        full_response = decision.get("userResponse", "")
        show_message("assistant", full_response)

    # Actualizar estado del flujo
    st.session_state["ultimo_estado"] = (
        f"Estado: {decision.get('status', '')}, "
        f"Paso siguiente: {decision.get('nextStep', '')}"
    )