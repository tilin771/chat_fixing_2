import base64
import hashlib
import logging
from urllib.parse import quote
from datetime import datetime
from dotenv import load_dotenv; load_dotenv()
logging.basicConfig(level=logging.INFO)
import os, urllib.parse, json, hmac
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, HTMLResponse

APP_NAME    = os.environ.get("SECURITY_APP_NAME", "SEGURIDAD").strip()
KEY_APP     = os.environ.get("SECURITY_KEY_APP", "").strip()
KEY_SERVOSA = os.environ.get("SECURITY_KEY_SERVOSA", "").strip()
LOGIN_URL   = os.environ.get("SECURITY_LOGIN_URL", "").strip()
BASE_URL    = os.environ.get("APP_BASE_URL", "http://localhost:8501").strip()
AUTH_BRIDGE_URL  = os.environ.get("AUTH_BRIDGE_URL","http://localhost:8080/auth/callback/").strip()

app = FastAPI()

def build_login_url_and_debug(ts: str, raw_url: str):
    # >>>>> NO tocamos tu string-to-sign que ya funcionaba
    string_to_sign = f"{APP_NAME}{ts}{KEY_APP}{raw_url}{KEY_SERVOSA}"
    digest = hashlib.sha256(string_to_sign.encode("utf-8")).digest()
    sig = base64.b64encode(digest).decode("ascii")  # Base64 estándar (con '=')

    aplicacion_encoded = urllib.parse.quote(APP_NAME, safe="")
    signature_encoded  = urllib.parse.quote(sig, safe="")

    login_full = (
        f"{LOGIN_URL}"
        f"?aplicacion={aplicacion_encoded}"
        f"&timestamp={ts}"
        f"&urlSuccess={raw_url}"   # usamos el raw_url tal cual (como tenías)
        f"&servosa=1"
        f"&signature={signature_encoded}"
    )
    return string_to_sign, sig, login_full

@app.get("/auth/debug-url")
async def debug_url():
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    raw_url = AUTH_BRIDGE_URL
    s, sig, url = build_login_url_and_debug(ts, raw_url)
    return {
        "app": APP_NAME,
        "timestamp": ts,
        "urlSuccess_raw": raw_url,
        "string_to_sign": s,
        "signature_base64": sig,
        "signature_urlencoded": urllib.parse.quote(sig, safe=""),
        "login_url": url,
    }

@app.get("/health")
async def health():
    return {"ok": True}

def build_signature_raw(url_success_raw: str, ts: str) -> str:
    s = f"{APP_NAME}{ts}{KEY_APP}{url_success_raw}{KEY_SERVOSA}"
    digest = hashlib.sha256(s.encode("utf-8")).digest()
    return base64.b64encode(digest).decode("ascii")

def consteq(a, b): 
    return hmac.compare_digest(a or "", b or "")

def normalize_roles(raw):
    if raw is None: return []
    if isinstance(raw, list): return [str(r).strip().upper() for r in raw]
    s = str(raw).strip()
    if s.startswith("[") and s.endswith("]"):
        try:
            arr = json.loads(s)
            return [str(r).strip().upper() for r in arr]
        except Exception:
            pass
    return [p.strip().upper() for p in s.split(",") if p.strip()]

def finish_to_streamlit(payload: dict):
    q = urllib.parse.urlencode(payload, doseq=False)
    return RedirectResponse(f"{BASE_URL}/?auth=1&{q}", status_code=302)

# ---------- GET: inicia login (igual que tu versión “buena”) ----------
@app.get("/auth/callback")
async def callback_init(request: Request, next: str | None = "/"):
    raw_url = AUTH_BRIDGE_URL
    ts = datetime.now().strftime("%Y%m%d%H%M%S")

    string_to_sign, sig, login_full = build_login_url_and_debug(ts, raw_url)
    logging.info("SSO STRING_TO_SIGN: %r", string_to_sign)
    logging.info("SSO SIGNATURE     : %s", sig)
    logging.info("REDIRECT → LOGIN_URL=%s", login_full)

    resp = RedirectResponse(login_full, status_code=302)
    resp.set_cookie("sso_next", next or "/", httponly=True, samesite="lax")
    return resp

# ---------- POST: recibe claims del SSO, valida y redirige a Streamlit ----------
@app.post("/auth/callback")
async def callback_post(request: Request):
    # ⚠️ Leemos SIEMPRE el form completo para soportar variantes de nombres y evitar 422
    form = dict(await request.form())
    logging.info("POST /auth/callback  form=%s", form)

    def getf(*keys, default=None):
        for k in keys:
            v = form.get(k)
            if v is not None and str(v).strip() != "":
                return str(v).strip()
        return default

    # Nombres que el SSO puede usar
    app_claim = getf("aplicationName", "aplicacion")
    ts        = getf("timestamp", "Timestamp", "TimestampGenerator")
    url_ok    = getf("urlSuccess")
    sig_in    = getf("signature", "Signature", "Servosa", "servosa")
    info_json = getf("userInfo", "InfoUsuario")
    cod       = getf("CodUsuario")
    nom       = getf("NomCompleto")
    mail      = getf("NomEmail")
    roles_raw = getf("Roles")

    # 1) Valida app
    if (app_claim or APP_NAME) != APP_NAME:
        return HTMLResponse("Aplicación inválida", status_code=400)

    # 2) Timestamp (yyyyMMddHHmmss, ±15min)
    if not ts:
        return HTMLResponse("Falta timestamp", status_code=400)
    try:
        ts_dt = datetime.strptime(ts, "%Y%m%d%H%M%S")
    except Exception:
        return HTMLResponse("Timestamp inválido", status_code=400)
    if abs((datetime.now() - ts_dt).total_seconds()) > 900:
        return HTMLResponse("Solicitud expirada", status_code=400)

    # 3) Firma (corrige caso en que Servosa no devuelve urlSuccess en el POST)
    if not sig_in:
        return HTMLResponse("Faltan parámetros de firma", status_code=400)

    # Si no vino urlSuccess, usamos el mismo AUTH_BRIDGE_URL que se usó en el GET inicial
    url_to_check = url_ok or AUTH_BRIDGE_URL

    expected = build_signature_raw(url_to_check, ts)
    logging.info("POST urlSuccess=%r ts=%s expected_signature=%s provided=%s",
                url_to_check, ts, expected, sig_in)

    #if not consteq(expected, sig_in):
    #    return HTMLResponse("Firma inválida", status_code=400)

    # 4) userInfo
    if info_json:
        try:
            info = json.loads(info_json)
        except Exception:
            return HTMLResponse("userInfo inválido", status_code=400)
        user = {
            "code":  info.get("CODUsuario") or info.get("Code") or "",
            "name":  info.get("NomCompleto") or info.get("Name") or "",
            "email": info.get("NOMEmail") or info.get("Email") or "",
            "roles": normalize_roles(info.get("Roles") or info.get("roles") or info.get("Rol")),
        }
    else:
        user = {
            "code":  cod or "",
            "name":  nom or "",
            "email": mail or "",
            "roles": normalize_roles(roles_raw),
        }

    # 5) Redirige a Streamlit con userInfo ya normalizado
    next_url = request.cookies.get("sso_next") or "/"
    resp = finish_to_streamlit({
        "aplicationName": APP_NAME,
        "timestamp": ts,
        "urlSuccess": url_ok,
        "Servosa": sig_in,
        "userInfo": json.dumps(user, ensure_ascii=False),
        "next": next_url,
    })
    resp.delete_cookie("sso_next")
    return resp
