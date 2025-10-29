import streamlit as st
from agents.robot_agent import run_robot
from app.components.chat_ui import stream_response, show_message
from data.constants import Constants

def handle_robot(user_input_or_decision):
    """Ejecuta el robot según el estado actual"""
    session_id = st.session_state["session_id"]

    if "robot_inicializado" not in st.session_state:
        st.session_state["robot_inicializado"] = True
        decision = user_input_or_decision
        user_code = decision.get("userCode", "")
        robot_task = decision.get("robotTask", {})
        task_type = robot_task.get("type", "")

        if not user_code or not task_type:
            show_message("assistant", "No se pudo identificar el código de usuario o tipo de tarea.")
            return

        st.session_state["robot_user_code"] = user_code
        st.session_state["robot_task_type"] = task_type
        prompt = f"Quiero ejecutar la acción '{task_type}', mi código de usuario es {user_code}"
    else:
        prompt = user_input_or_decision

    stream_response(run_robot, prompt, session_id, message_spinner=Constants.Spinners.ROBOT_EXECUTE)

    full_response = st.session_state["messages"][-1]["content"].lower()
    keywords_reinicio = ["lo siento", "por favor", "contacta con soporte"]
    if "el robot ha sido ejecutado" in full_response:
        st.session_state["modo_robot_finalizado"] = True
        st.rerun()
        return
    if any(k in full_response for k in keywords_reinicio):
        st.session_state["modo_robot"] = False
        for key in ["robot_inicializado", "robot_user_code", "robot_task_type"]:
            st.session_state.pop(key, None)
