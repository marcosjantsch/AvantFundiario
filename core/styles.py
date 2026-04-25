from __future__ import annotations

import streamlit as st


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --af-font: "Segoe UI", "IBM Plex Sans", sans-serif;
            --af-page-bg: #e7edf6;
            --af-page-bg-soft: #f5f8fd;
            --af-surface: #ffffff;
            --af-surface-muted: #f6f9fd;
            --af-surface-alt: #edf3fb;
            --af-surface-strong: #e0e8f4;
            --af-text: #1f3146;
            --af-text-soft: #556a82;
            --af-text-muted: #7f91a6;
            --af-accent: #10c9bb;
            --af-accent-strong: #17d2bf;
            --af-accent-blue: #1778e6;
            --af-accent-danger: #f04d63;
            --af-accent-ink: #16273c;
            --af-sidebar: #11243a;
            --af-sidebar-strong: #0c1b2d;
            --af-sidebar-text: #edf5fb;
            --af-sidebar-muted: #8ea8c2;
            --af-sidebar-title: #19d0bc;
            --af-border: #d2deec;
            --af-border-strong: #b9c8db;
            --af-shadow-soft: 0 16px 38px rgba(27, 46, 74, 0.12);
            --af-shadow-card: 0 20px 42px rgba(27, 46, 74, 0.14);
            --af-radius-input: 12px;
            --af-radius-card: 16px;
            --af-radius-panel: 18px;
        }

        html, body, [class*="css"] {
            font-family: var(--af-font);
        }

        .stApp {
            background:
                radial-gradient(circle at top right, rgba(16, 201, 187, 0.14), transparent 24%),
                radial-gradient(circle at top left, rgba(23, 120, 230, 0.10), transparent 22%),
                linear-gradient(180deg, var(--af-page-bg-soft) 0%, var(--af-page-bg) 100%);
            color: var(--af-text);
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, var(--af-sidebar) 0%, var(--af-sidebar-strong) 100%);
            border-right: 1px solid rgba(210, 222, 236, 0.18);
        }

        [data-testid="stSidebar"] > div:first-child {
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.02), rgba(255, 255, 255, 0.00));
        }

        .block-container {
            padding-top: 1rem;
            padding-bottom: 1.4rem;
        }

        h1, h2, h3 {
            color: var(--af-text);
            letter-spacing: 0.07em;
            text-transform: uppercase;
            font-weight: 800;
        }

        p, label, span, div, li, small {
            color: inherit;
        }

        [data-testid="stMarkdownContainer"] p,
        [data-testid="stCaptionContainer"],
        .stCaption {
            color: var(--af-text-soft);
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] div {
            color: var(--af-sidebar-text) !important;
        }

        [data-testid="stSidebar"] .stSelectbox,
        [data-testid="stSidebar"] .stCheckbox,
        [data-testid="stSidebar"] .stButton {
            padding: 0.5rem 0.65rem;
            border: 1px solid rgba(142, 168, 194, 0.18);
            border-radius: var(--af-radius-panel);
            background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.03));
            margin-bottom: 0.65rem;
        }

        [data-testid="stSidebar"] div[data-baseweb="select"] > div {
            background: linear-gradient(180deg, #ffffff, #f6f9fd) !important;
            border: 1px solid #d2deec !important;
            color: #1f3146 !important;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.65);
        }

        [data-testid="stSidebar"] div[data-baseweb="select"] span,
        [data-testid="stSidebar"] div[data-baseweb="select"] input,
        [data-testid="stSidebar"] div[data-baseweb="select"] div {
            color: #1f3146 !important;
        }

        [data-testid="stSidebar"] div[data-baseweb="select"] input::placeholder {
            color: #7f91a6 !important;
            -webkit-text-fill-color: #7f91a6 !important;
        }

        [data-testid="stSidebar"] div[data-baseweb="select"] svg {
            fill: #1f3146 !important;
        }

        div[data-baseweb="select"] > div,
        .stTextInput input,
        .stTextArea textarea,
        .stNumberInput input {
            border-radius: var(--af-radius-input) !important;
            border: 1px solid var(--af-border) !important;
            background: linear-gradient(180deg, #ffffff, #f6f9fd) !important;
            color: var(--af-text) !important;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.65);
        }

        .stTextInput input:focus,
        .stTextArea textarea:focus,
        .stNumberInput input:focus {
            border-color: #93b9d7 !important;
            box-shadow: 0 0 0 3px rgba(16, 201, 187, 0.12) !important;
        }

        .stButton > button,
        .stForm button[kind="secondaryFormSubmit"],
        .stDownloadButton > button {
            border-radius: 12px;
            border: 1px solid rgba(23, 120, 230, 0.22);
            background: linear-gradient(180deg, #ffffff 0%, #eaf2fb 100%);
            color: var(--af-accent-ink);
            font-weight: 700;
            box-shadow: var(--af-shadow-soft);
        }

        .stButton > button:disabled,
        .stForm button[kind="secondaryFormSubmit"]:disabled,
        .stDownloadButton > button:disabled {
            background: linear-gradient(180deg, #e8eef6 0%, #dde7f3 100%) !important;
            border: 1px solid #c7d4e5 !important;
            color: #7f91a6 !important;
            opacity: 1 !important;
            box-shadow: none !important;
        }

        [data-testid="stSidebar"] .stButton > button,
        [data-testid="stSidebar"] .stButton > button p,
        [data-testid="stSidebar"] button[kind="secondary"] p,
        [data-testid="stSidebar"] button[kind="primary"] p {
            color: #16273c !important;
        }

        [data-testid="stSidebar"] .stButton > button:disabled,
        [data-testid="stSidebar"] .stButton > button:disabled p,
        [data-testid="stSidebar"] button[disabled],
        [data-testid="stSidebar"] button[disabled] p {
            background: linear-gradient(180deg, #e8eef6 0%, #dde7f3 100%) !important;
            border: 1px solid #c7d4e5 !important;
            color: #7f91a6 !important;
            -webkit-text-fill-color: #7f91a6 !important;
            opacity: 1 !important;
            box-shadow: none !important;
        }

        .stButton > button:hover,
        .stForm button[kind="secondaryFormSubmit"]:hover,
        .stDownloadButton > button:hover {
            border-color: rgba(16, 201, 187, 0.42);
            background: linear-gradient(180deg, #faffff 0%, #e1fbf7 100%);
            color: #0f3d56;
        }

        .stForm button[kind="secondaryFormSubmit"],
        .af-primary-action button {
            background: linear-gradient(180deg, var(--af-accent-strong) 0%, var(--af-accent) 100%);
            border: 1px solid rgba(16, 201, 187, 0.4);
            color: #0e2436;
            box-shadow: 0 16px 34px rgba(16, 201, 187, 0.24);
        }

        div[data-testid="stForm"] {
            border: 1px solid var(--af-border);
            border-radius: var(--af-radius-panel);
            background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(246,249,253,0.98));
            padding: 0.9rem 1rem 0.35rem 1rem;
            box-shadow: var(--af-shadow-card);
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid var(--af-border);
            border-radius: var(--af-radius-panel);
            overflow: hidden;
            background: var(--af-surface);
            box-shadow: var(--af-shadow-card);
        }

        div[data-testid="stDataFrame"] [role="grid"] {
            cursor: pointer;
        }

        div[data-testid="stDataFrame"] [role="columnheader"] {
            background: #e8f0fa !important;
            color: var(--af-text) !important;
            font-weight: 700;
        }

        div[data-testid="stDataFrame"] [role="gridcell"] {
            color: #1f3146 !important;
            background-color: #ffffff !important;
        }

        .af-table-hint {
            margin: 0 0 0.6rem 0;
            padding: 0.7rem 0.9rem;
            border: 1px solid var(--af-border);
            border-radius: 14px;
            background: linear-gradient(180deg, #ffffff, #f3f8fe);
            color: var(--af-text-soft);
            box-shadow: var(--af-shadow-soft);
            font-size: 0.92rem;
        }

        .af-login-shell {
            padding: 0.2rem 0 0.35rem 0;
        }

        .af-login-brand,
        .af-login-panel {
            border: 1px solid var(--af-border);
            border-radius: 22px;
            box-shadow: var(--af-shadow-card);
            overflow: hidden;
        }

        .af-login-brand {
            padding: 1.5rem;
            background:
                radial-gradient(circle at top right, rgba(16, 201, 187, 0.22), transparent 30%),
                radial-gradient(circle at bottom left, rgba(23, 120, 230, 0.16), transparent 32%),
            linear-gradient(180deg, #17314f 0%, #10253b 100%);
            color: #edf5fb;
        }

        .af-login-topbar {
            display: flex;
            align-items: center;
            gap: 14px;
            margin-bottom: 1.1rem;
        }

        .af-login-logo-card {
            width: 68px;
            height: 68px;
            border-radius: 18px;
            border: 1px solid rgba(255, 255, 255, 0.12);
            background: linear-gradient(180deg, rgba(255,255,255,0.10), rgba(255,255,255,0.04));
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.08);
        }

        .af-login-logo-image {
            width: 46px;
            height: 46px;
            object-fit: contain;
            display: block;
        }

        .af-login-logo-fallback {
            color: #ffffff;
            font-size: 1rem;
            font-weight: 800;
            letter-spacing: 0.08em;
        }

        .af-login-kicker {
            display: inline-flex;
            padding: 0.35rem 0.7rem;
            border-radius: 999px;
            background: rgba(16, 201, 187, 0.14);
            border: 1px solid rgba(25, 208, 188, 0.18);
            color: #8ef2e7;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .af-login-title {
            margin-top: 1rem;
            font-size: 2rem;
            line-height: 1.05;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            font-weight: 800;
            color: #ffffff;
        }

        .af-login-subtitle {
            margin-top: 0.75rem;
            color: #c8d7e7;
            font-size: 0.98rem;
            line-height: 1.55;
            max-width: 36rem;
        }

        .af-login-points {
            margin-top: 1.2rem;
            display: grid;
            gap: 0.65rem;
        }

        .af-login-point {
            padding: 0.7rem 0.8rem;
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(210, 222, 236, 0.14);
            color: #edf5fb;
        }

        .af-login-panel {
            padding: 1.5rem;
            background: linear-gradient(180deg, rgba(255,255,255,0.94), rgba(245,248,253,0.98));
        }

        .af-login-panel h2 {
            margin: 0 0 0.2rem 0;
            font-size: 1.05rem;
        }

        .af-soft-status {
            margin-bottom: 0.85rem;
            padding: 0.72rem 0.88rem;
            border-radius: 14px;
            border: 1px solid var(--af-border);
            background: linear-gradient(180deg, #ffffff, #f3f8fe);
            color: var(--af-text-soft);
            box-shadow: var(--af-shadow-soft);
        }

        @media (max-width: 900px) {
            .af-login-shell {
                padding-top: 0.1rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
