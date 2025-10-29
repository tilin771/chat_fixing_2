import streamlit as st
from services.query_kb import consultar_kb_streaming
from data.constants import Constants

def generate_context_kb(max_ultimos=5):
    """Genera contexto de los últimos mensajes para KB"""
    context = ""
    ultimos_mensajes = st.session_state["messages"][-max_ultimos:]
    for msg in ultimos_mensajes:
        rol = "Usuario" if msg["role"] == "user" else "Asistente"
        context += f"{rol}: {msg['content']}\n"
    return context

def handle_kb(user_input, decision=None):
    """Consulta la KB con contexto y muestra confirmationMessage si existe"""
    context = generate_context_kb()
    query = f"{context}\nPregunta del usuario: {user_input}"
    full_response = ""

    st.session_state["messages"].append({"role": "assistant", "content": ""})
    current_idx = len(st.session_state["messages"]) - 1

    with st.chat_message("assistant"):
        placeholder = st.empty()
        with st.spinner(Constants.Spinners.KB_QUERY):
            for chunk in consultar_kb_streaming(user_input, query, prioridad=7):
                full_response += chunk
                st.session_state["messages"][current_idx]["content"] = full_response
                placeholder.markdown(full_response)

        if decision and "confirmationMessage" in decision:
            full_response += f"\n\n**{decision.get('confirmationMessage', '')}**"
            st.session_state["messages"][current_idx]["content"] = full_response
            placeholder.markdown(full_response)
