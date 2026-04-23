from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import streamlit as st
import yaml

try:
    import bcrypt
except ImportError:  # pragma: no cover
    bcrypt = None

from services.auth_log_service import registrar_login, registrar_logout


SESSION_DEFAULTS = {
    "authenticated": False,
    "username": "",
    "nome": "",
    "perfil": "",
    "user_display_name": "",
    "authenticator": None,
    "login_timestamp": "",
}


def _clean_text(value: object, default: str = "") -> str:
    text = str(value or "").strip()
    return text if text else default


def load_users_from_config(config_path: str) -> list[dict[str, str]]:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de autenticacao nao encontrado: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    usernames = (((data.get("credentials") or {}).get("usernames")) or {})
    users: list[dict[str, str]] = []
    for username, payload in usernames.items():
        payload = payload or {}
        password = _clean_text(payload.get("password"))
        if not username or not password:
            continue
        users.append(
            {
                "username": str(username).strip(),
                "nome": _clean_text(payload.get("name"), str(username).strip()),
                "password": password,
                "perfil": _clean_text(payload.get("role"), "Usuario"),
                "email": _clean_text(payload.get("email")),
            }
        )
    return users


def _verify_password(password: str, stored_value: str) -> bool:
    stored = _clean_text(stored_value)
    plain = str(password or "")
    if stored.startswith("$2a$") or stored.startswith("$2b$") or stored.startswith("$2y$"):
        if bcrypt is None:
            return False
        try:
            return bcrypt.checkpw(plain.encode("utf-8"), stored.encode("utf-8"))
        except Exception:
            return False
    return plain == stored


def authenticate_user(username: str, password: str, users: list[dict[str, str]]) -> dict[str, str] | None:
    wanted = _clean_text(username)
    for user in users:
        if user["username"] != wanted:
            continue
        if _verify_password(password, user["password"]):
            return user
    return None


def get_user_role(user: dict[str, str] | None) -> str:
    return _clean_text((user or {}).get("perfil"), "Usuario")


def get_user_display_name(user: dict[str, str] | None) -> str:
    return _clean_text((user or {}).get("nome"), _clean_text((user or {}).get("username"), "Usuario"))


def ensure_auth_session_defaults() -> None:
    for key, value in SESSION_DEFAULTS.items():
        st.session_state.setdefault(key, value)


@dataclass
class YAMLAuthenticator:
    def logout(self, label: str = "Logout", location: str = "main") -> bool:
        clicked = False
        if location == "main":
            clicked = st.button(label, key="header_logout_button", use_container_width=False)
        if not clicked:
            return False

        registrar_logout(
            st.session_state.get("username", ""),
            st.session_state.get("nome", ""),
            st.session_state.get("perfil", ""),
        )
        for key, default in SESSION_DEFAULTS.items():
            st.session_state[key] = default
        st.rerun()
        return True


def store_authenticated_user(user: dict[str, str]) -> None:
    display_name = get_user_display_name(user)
    st.session_state["authenticated"] = True
    st.session_state["username"] = user["username"]
    st.session_state["nome"] = display_name
    st.session_state["perfil"] = get_user_role(user)
    st.session_state["user_display_name"] = display_name
    st.session_state["authenticator"] = YAMLAuthenticator()
    st.session_state["login_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    registrar_login(user["username"], display_name, get_user_role(user))


def render_login_screen(config_path: str) -> bool:
    ensure_auth_session_defaults()
    if st.session_state.get("authenticated"):
        return True

    try:
        users = load_users_from_config(config_path)
    except Exception:
        st.error("Nao foi possivel carregar o arquivo de autenticacao.")
        st.stop()

    st.markdown("<div class='af-login-shell'>", unsafe_allow_html=True)
    margin_left, brand_col, form_col, margin_right = st.columns([0.12, 1.0, 0.9, 0.12], vertical_alignment="top")

    with brand_col:
        st.markdown(
            """
            <div class="af-login-brand">
                <div class="af-login-kicker">Avant Platform</div>
                <div class="af-login-title">Consulta Fundiaria</div>
                <div class="af-login-subtitle">
                    Ambiente corporativo para consulta territorial, filtro fundiario,
                    validacao documental e analise espacial em um fluxo unico.
                </div>
                <div class="af-login-points">
                    <div class="af-login-point"><strong>Base geografica</strong><br>Carregamento estruturado do shapefile principal com filtros por empresa, bloco e fazenda.</div>
                    <div class="af-login-point"><strong>Documentos</strong><br>Consulta de matricula, CCIR, ITR, CAR e anexos vinculados pelo indice oficial.</div>
                    <div class="af-login-point"><strong>Mapa executivo</strong><br>Visual tecnico com camadas de apoio e experiencia visual alinhada ao padrao Avant.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with form_col:
        st.markdown("<div class='af-login-panel'>", unsafe_allow_html=True)
        st.markdown("## Acesso")
        st.markdown(
            "<div class='af-soft-status'>Informe usuario e senha para entrar no sistema. O ambiente principal abre primeiro e os documentos complementares passam a ser carregados sob demanda.</div>",
            unsafe_allow_html=True,
        )
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Usuario")
            password = st.text_input("Senha", type="password")
            submit = st.form_submit_button("Entrar", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if submit:
        user = authenticate_user(username=username, password=password, users=users)
        if not user:
            st.error("Usuario ou senha invalidos.")
            st.stop()
        store_authenticated_user(user)
        st.rerun()

    return False
