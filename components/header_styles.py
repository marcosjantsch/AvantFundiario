from __future__ import annotations


def build_header_styles() -> str:
    return """
    <style>
    section.main > div.block-container {
        padding-top: 0.35rem;
    }

    .ag-header-wrap {
        position: sticky;
        top: 0.1rem;
        z-index: 20;
        margin: -4px 0 6px 0;
        padding: 0.2rem 0 0.25rem 0;
        backdrop-filter: blur(10px);
    }

    .ag-header-card {
        border: 1px solid rgba(79, 255, 196, 0.12);
        border-radius: 18px;
        padding: 0.5rem 0.8rem;
        background: linear-gradient(180deg, rgba(8, 18, 16, 0.96), rgba(6, 14, 13, 0.92));
        box-shadow: 0 12px 28px rgba(0, 0, 0, 0.22);
    }

    .ag-header-logo-fallback {
        width: 58px;
        height: 58px;
        border-radius: 16px;
        background: linear-gradient(135deg, #0f766e, #2563eb);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 18px;
        font-weight: 800;
        letter-spacing: 0.5px;
        box-shadow: 0 6px 18px rgba(37, 99, 235, 0.18);
    }

    .ag-header-title-row {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
        margin: 0;
        padding: 0;
    }

    .ag-header-title {
        font-size: 22px;
        font-weight: 800;
        line-height: 1.05;
        margin: 0;
        padding: 0;
        letter-spacing: -0.2px;
        color: #d9fff3;
    }

    .ag-header-version {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 3px 8px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 800;
        line-height: 1;
        color: #7ef9ff;
        border: 1px solid rgba(126, 249, 255, 0.18);
        background: rgba(126, 249, 255, 0.08);
    }

    .ag-header-subtitle {
        margin-top: 0.15rem;
        font-size: 12px;
        color: rgba(217, 255, 243, 0.7);
    }

    .ag-header-user-row {
        border: none;
        border-radius: 0;
        padding: 0;
        background: transparent;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 8px;
        min-height: 30px;
        white-space: nowrap;
        overflow: hidden;
    }

    .ag-header-user-inline {
        font-size: 11px;
        line-height: 1.2;
        color: rgba(217, 255, 243, 0.88);
        overflow: hidden;
        text-overflow: ellipsis;
    }

    @media (max-width: 900px) {
        .ag-header-title {
            font-size: 18px;
        }
        .ag-header-card {
            padding: 0.45rem 0.6rem;
        }
        .ag-header-user-row {
            white-space: normal;
            align-items: flex-start;
        }
    }
    </style>
    """
