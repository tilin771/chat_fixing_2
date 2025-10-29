
import hashlib, hmac, os, time, json, urllib.parse
from typing import Dict, Any, List, Optional

APP_NAME    = os.environ.get("SECURITY_APP_NAME", "SEGURIDAD")
KEY_APP     = os.environ.get("SECURITY_KEY_APP", "")
KEY_SERVOSA = os.environ.get("SECURITY_KEY_SERVOSA", "")
LOGIN_URL   = os.environ.get("SECURITY_LOGIN_URL", "")
BASE_URL    = os.environ.get("APP_BASE_URL", "")

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def build_signature(url_success: str) -> str:
    return sha256_hex(f"{APP_NAME}{KEY_APP}{url_success}{KEY_SERVOSA}")

def consteq(a: str, b: str) -> bool:
    return hmac.compare_digest(a or "", b or "")

def build_login_redirect(next_url: str) -> str:
    callback = f"{BASE_URL}/"
    url_success = f"{callback}?auth=1&next={urllib.parse.quote(next_url, safe='')}"
    ts = str(int(time.time()))
    sig = build_signature(url_success)
    qs = {
        "aplicationName": APP_NAME,
        "timestamp": ts,
        "urlSuccess": url_success,
        "Servosa": sig,
    }
    return f"{LOGIN_URL}?{urllib.parse.urlencode(qs)}"

def normalize_roles(roles: Optional[str | List[str]]) -> List[str]:
    if roles is None:
        return []
    if isinstance(roles, list):
        return [str(r).strip().upper() for r in roles]
    txt = str(roles).strip()
    if txt.startswith("[") and txt.endswith("]"):
        try:
            arr = json.loads(txt)
            return [str(r).strip().upper() for r in arr]
        except Exception:
            pass
    return [p.strip().upper() for p in txt.split(",") if p.strip()]

def validate_and_parse_callback(params: Dict[str, List[str]]) -> Dict[str, Any]:
    appl = (params.get("aplicationName") or [""])[0]
    ts   = (params.get("timestamp") or [""])[0]
    urlS = (params.get("urlSuccess") or [""])[0]
    sign = (params.get("Servosa") or [""])[0]
    if appl != APP_NAME:
        raise ValueError("Aplicación inválida")
    try:
        its = int(ts)
    except Exception:
        raise ValueError("Timestamp inválido")
    if abs(int(time.time()) - its) > 300:
        raise ValueError("Solicitud expirada")
    if not consteq(build_signature(urlS), sign):
        raise ValueError("Firma inválida")

    info = None
    if "userInfo" in params:
        try:
            info = json.loads((params["userInfo"][0]))
        except Exception:
            raise ValueError("userInfo inválido")

    if info:
        roles = normalize_roles(info.get("Roles") or info.get("roles") or info.get("Rol"))
        return {
            "code":  info.get("CodUsuario") or info.get("Code") or "",
            "name":  info.get("NomCompleto") or info.get("Name") or "",
            "email": info.get("NomEmail") or info.get("Email") or "",
            "roles": roles,
            "raw":   info,
        }
    else:
        cod  = (params.get("CodUsuario") or [""])[0]
        nom  = (params.get("NomCompleto") or [""])[0]
        mail = (params.get("NomEmail") or [""])[0]
        roles = normalize_roles((params.get("Roles") or [""])[0])
        return {
            "code": cod, "name": nom, "email": mail,
            "roles": roles,
            "raw": {
                "CodUsuario": cod, "NomCompleto": nom, "NomEmail": mail, "Roles": roles
            }
        }
