from pathlib import Path

import streamlit as st


def add_logo_sidebar(logo_path: str) -> None:
    logo_file = Path(logo_path)
    if not logo_file.exists():
        return

    try:
        st.sidebar.markdown('<div style="margin-bottom:-10px;">', unsafe_allow_html=True)
        st.sidebar.image(str(logo_file), width=140)
        st.sidebar.markdown("</div>", unsafe_allow_html=True)
    except Exception:
        return
