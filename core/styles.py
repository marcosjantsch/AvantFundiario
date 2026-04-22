from __future__ import annotations

import streamlit as st


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --af-bg: #06110f;
            --af-card: #0f1f1b;
            --af-line: rgba(79, 255, 196, 0.18);
            --af-ink: #d9fff3;
            --af-muted: #88b7ac;
            --af-accent: #4fffc4;
            --af-accent-2: #7ef9ff;
        }
        .stApp {
            background:
                radial-gradient(circle at top right, rgba(126, 249, 255, 0.14), transparent 26%),
                radial-gradient(circle at top left, rgba(79, 255, 196, 0.12), transparent 22%),
                linear-gradient(180deg, #05100e 0%, var(--af-bg) 100%);
            color: var(--af-ink);
        }
        [data-testid="stHeader"] {
            background: rgba(0, 0, 0, 0);
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #091512 0%, #07110f 100%);
            border-right: 1px solid var(--af-line);
        }
        .block-container {
            padding-top: 1.1rem;
            padding-bottom: 1.4rem;
        }
        .stApp [data-testid="stSidebar"] .stButton > button {
            width: 100%;
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--af-line);
            border-radius: 18px;
            overflow: hidden;
            background: var(--af-card);
            box-shadow: 0 16px 34px rgba(0, 0, 0, 0.18);
        }
        div[data-testid="stDataFrame"] [role="grid"] {
            cursor: pointer;
        }
        div[data-testid="stDataFrame"] [role="grid"] * {
            transition: background-color 120ms ease, color 120ms ease;
        }
        h1, h2, h3, label, [data-testid="stSidebar"] * {
            color: var(--af-ink) !important;
        }
        [data-testid="stMarkdownContainer"], p, span, div {
            color: inherit;
        }
        .af-title {
            display: flex;
            align-items: baseline;
            gap: 12px;
            margin: 0 0 16px 0;
        }
        .af-title-main {
            font-size: 2.1rem;
            font-weight: 800;
            letter-spacing: 0.03em;
            color: var(--af-accent);
            text-shadow: 0 0 22px rgba(79, 255, 196, 0.22);
        }
        .af-title-version {
            font-size: 0.95rem;
            font-weight: 800;
            letter-spacing: 0.28em;
            text-transform: uppercase;
            color: var(--af-accent-2);
            text-shadow: 0 0 18px rgba(126, 249, 255, 0.22);
        }
        div[data-testid="stForm"] {
            border: 1px solid var(--af-line);
            border-radius: 18px;
            background: rgba(15, 31, 27, 0.92);
            padding: 0.75rem 0.8rem 0.2rem 0.8rem;
        }
        .af-table-hint {
            margin: 0 0 0.55rem 0;
            padding: 0.55rem 0.8rem;
            border: 1px solid rgba(126, 249, 255, 0.16);
            border-radius: 14px;
            background: rgba(126, 249, 255, 0.06);
            color: rgba(217, 255, 243, 0.86);
            font-size: 0.9rem;
        }
        .stButton > button, .stForm button[kind="secondaryFormSubmit"] {
            border-radius: 12px;
            border: 1px solid rgba(126, 249, 255, 0.22);
            background: linear-gradient(180deg, rgba(79,255,196,0.16), rgba(126,249,255,0.10));
            color: #d9fff3;
        }
        .stDownloadButton > button {
            border-radius: 12px;
            border: 1px solid rgba(79, 255, 196, 0.2);
            background: linear-gradient(180deg, rgba(79,255,196,0.18), rgba(126,249,255,0.12));
            color: #d9fff3;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
