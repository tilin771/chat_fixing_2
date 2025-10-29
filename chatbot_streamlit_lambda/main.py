import json
import streamlit as st
from app.utils.session_manager import initialize_session
from app.components.chat_handlers import send_message
from app.components.chat_ui import show_message
from agents.orchestrator_agent import run_supervisor
from chatbot_streamlit_lambda.data.constants import Constants
from app.handlers import ensure_sso_session

#ensure_sso_session()
# Inicializar sesión
initialize_session()
st.title("Chatbot soporte Autoline con IA")

# Saludo inicial
if not st.session_state["ia_inicializada"]:
    st.session_state["ia_inicializada"] = True
    saludo = run_supervisor("hola", st.session_state["session_id"])
    try:
        saludo_json = json.loads(saludo)
        saludo_texto = saludo_json.get("userResponse", "")
    except:
        saludo_texto = Constants.Prompts["greeting"]
    
    # Solo guardamos, no mostramos directamente
    st.session_state["messages"].append({"role": "assistant", "content": saludo_texto})


# Mostrar mensajes previos
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input del usuario
if st.session_state.get("modo_robot_finalizado", False):
    st.chat_input(Constants.Labels["chat_disabled"], disabled=True)
    
elif st.session_state.get("ticket_finalizado", False):
    st.chat_input(Constants.Labels["chat_disabled"], disabled=True)
else:
    user_input = st.chat_input(Constants.Labels["input_placeholder"])
    if user_input:
        send_message(user_input)
