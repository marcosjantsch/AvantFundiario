from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path


LOG_PATH = Path("auth_login_log.csv")
LOG_HEADER = ["username", "nome", "perfil", "login_data_hora", "logout_data_hora", "status"]


def _ensure_log_file() -> None:
    if LOG_PATH.exists():
        return
    try:
        with LOG_PATH.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file, delimiter=";")
            writer.writerow(LOG_HEADER)
    except Exception:
        return


def _write_row(row: list[str]) -> None:
    _ensure_log_file()
    try:
        with LOG_PATH.open("a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file, delimiter=";")
            writer.writerow(row)
    except Exception:
        return


def registrar_login(username: str, nome: str = "", perfil: str = "") -> None:
    _write_row(
        [
            str(username or "").strip(),
            str(nome or "").strip(),
            str(perfil or "").strip(),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "",
            "LOGIN",
        ]
    )


def registrar_logout(username: str, nome: str = "", perfil: str = "") -> None:
    _write_row(
        [
            str(username or "").strip(),
            str(nome or "").strip(),
            str(perfil or "").strip(),
            "",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "LOGOUT",
        ]
    )
