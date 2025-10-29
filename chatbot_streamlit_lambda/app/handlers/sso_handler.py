import json
import os as _os
import streamlit as st

def _as_list_dict(d):
    return {k: (v if isinstance(v, list) else [v]) for k, v in d.items()}

def _parse_user_from_query(params: dict) -> dict:
    """Recibe st.query_params (dict simple), extrae userInfo/InfoUsuario y devuelve el user dict."""
    p = _as_list_dict(params)
    raw = p.get("userInfo", [None])[0] or p.get("InfoUsuario", [None])[0]
    if not raw:
        raise ValueError("No se encontró userInfo/InfoUsuario en el retorno")
    info = json.loads(raw)
    roles = info.get("roles") or info.get("Roles") or info.get("Rol") or []
    if isinstance(roles, str):
        try:
            roles = json.loads(roles)
        except Exception:
            roles = [r.strip() for r in roles.split(",") if r.strip()]
    return {
        "code":  info.get("code") or info.get("CODUsuario") or "",
        "name":  info.get("name") or info.get("NomCompleto") or "",
        "email": info.get("email") or info.get("NOMEmail") or "",
        "roles": roles,
    }

def ensure_sso_session():
    """Valida la sesión SSO, redirige si no hay autenticación válida."""
    _params_raw = dict(st.query_params)

    _has_auth_flag   = "auth" in _params_raw
    _has_userinfo    = "userInfo" in _params_raw or "InfoUsuario" in _params_raw
    _has_raw_markers = all(k in _params_raw for k in ("aplicationName", "timestamp", "urlSuccess", "Servosa"))

    # 1) Caso válido (retorno con userInfo/InfoUsuario)
    if _has_auth_flag or _has_userinfo:
        try:
            user = _parse_user_from_query(_params_raw)
            st.session_state["user"] = user
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Error de autenticación: {e}")
            st.stop()

    # 2) Caso intermedio (GET sin userInfo todavía)
    elif _has_raw_markers and not _has_userinfo:
        bridge = _os.environ.get("AUTH_BRIDGE_URL")
        st.markdown(f'<meta http-equiv="refresh" content="0; url={bridge}?next=%2F">', unsafe_allow_html=True)
        st.stop()

    # 3) No hay sesión aún
    if "user" not in st.session_state:
        bridge = _os.environ.get("AUTH_BRIDGE_URL")
        st.markdown(f'<meta http-equiv="refresh" content="0; url={bridge}?next=%2F">', unsafe_allow_html=True)
        st.stop()
