import streamlit as st

def show_message(role, content):
    """Muestra un mensaje en la UI y lo guarda en el historial"""
    with st.chat_message(role):
        st.markdown(content)
    st.session_state["messages"].append({"role": role, "content": content})

def stream_response(generator_func, *args, message_spinner=None, **kwargs):
    """Muestra respuestas de forma streaming usando un generador"""
    with st.chat_message("assistant"):
        placeholder = st.empty()
        with st.spinner(message_spinner):
            full_response = ""
            for chunk in generator_func(*args, **kwargs):
                full_response += chunk
                placeholder.markdown(full_response)
    st.session_state["messages"].append({"role": "assistant", "content": full_response})
    return full_response