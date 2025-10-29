import streamlit as st
import json
from agents.orchestrator_agent import run_supervisor
from chatbot_streamlit_lambda.app.handlers.handle_actions import handle_action  
from app.handlers.robot_handler import handle_robot
from app.handlers.ticket_handler import handle_ticket
from app.components.chat_ui import show_message
from app.utils.validators import validate_message
from chatbot_streamlit_lambda.data.constants import ERRORES
from data.prompts import PROMPT_MODIFIER


def parse_decision_with_retry(user_input, session_id, max_retries=3):
    prompt = user_input
    for _ in range(max_retries):
        decision = run_supervisor(prompt, session_id)
        try:
            return json.loads(decision)
        except json.JSONDecodeError:
            prompt = user_input + PROMPT_MODIFIER["force_json"]
    return {"userResponse": ERRORES["bad_response_agent"]}



def send_message(user_input):
    """Procesa el input del usuario y llama al handler correspondiente"""
    session_id = st.session_state["session_id"]

    # Guardar mensaje del usuario
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Validar mensaje
    errores = validate_message(user_input)
    if errores:
        mensaje_errores = "Se encontraron los siguientes errores:\n\n" + "\n".join(f"- {e}" for e in errores)
        show_message("assistant", mensaje_errores)
        return

    if st.session_state.get("modo_ticket"):
        handle_ticket(user_input)
        return

    if st.session_state.get("modo_robot"):
        handle_robot(user_input)
        return

    decision = parse_decision_with_retry(user_input, session_id)

    handle_action(decision, user_input)
