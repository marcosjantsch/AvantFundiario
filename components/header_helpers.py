from __future__ import annotations

from html import escape
from pathlib import Path

import streamlit as st


def sanitize_header_inputs(app_name, version, user, role, current_mode, subtitle, username):
    return {
        "app_name": escape(app_name or "Avant Fundiario"),
        "version": escape(version or ""),
        "user": escape(user or "-"),
        "role": escape(role or "-"),
        "current_mode": escape(current_mode or ""),
        "subtitle": escape(subtitle or ""),
        "username": escape(username or "-"),
    }


def render_logo_or_fallback(logo_path: str):
    logo_ok = False
    if logo_path:
        path = Path(logo_path).resolve()
        if path.exists():
            try:
                st.image(str(path), width=58)
                logo_ok = True
            except Exception:
                logo_ok = False

    if not logo_ok:
        st.markdown(
            """
            <div class="ag-header-logo-fallback">
                AF
            </div>
            """,
            unsafe_allow_html=True,
        )
