from __future__ import annotations


def build_header_styles() -> str:
    return """
    <style>
    section.main > div.block-container {
        padding-top: 0.4rem;
    }

    .ag-header-wrap {
        position: sticky;
        top: 0.1rem;
        z-index: 20;
        margin: -2px 0 10px 0;
        padding: 0.15rem 0 0.3rem 0;
        backdrop-filter: blur(12px);
    }

    .ag-header-card {
        border: 1px solid #d2deec;
        border-radius: 20px;
        padding: 0.55rem 0.85rem;
        background:
            radial-gradient(circle at top right, rgba(16, 201, 187, 0.14), transparent 22%),
            linear-gradient(180deg, rgba(255,255,255,0.96), rgba(245,248,253,0.98));
        box-shadow: 0 20px 42px rgba(27, 46, 74, 0.14);
    }

    .ag-header-logo-fallback {
        width: 58px;
        height: 58px;
        border-radius: 16px;
        background: linear-gradient(135deg, #10c9bb, #1778e6);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 18px;
        font-weight: 800;
        letter-spacing: 0.5px;
        box-shadow: 0 10px 24px rgba(23, 120, 230, 0.22);
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
        letter-spacing: 0.07em;
        text-transform: uppercase;
        color: #1f3146;
    }

    .ag-header-version {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 4px 9px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 800;
        line-height: 1;
        color: #1778e6;
        border: 1px solid rgba(23, 120, 230, 0.18);
        background: rgba(23, 120, 230, 0.08);
    }

    .ag-header-subtitle {
        margin-top: 0.18rem;
        font-size: 12px;
        color: #556a82;
    }

    .ag-header-user-row {
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
        color: #556a82;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    @media (max-width: 900px) {
        .ag-header-title {
            font-size: 18px;
        }
        .ag-header-card {
            padding: 0.45rem 0.65rem;
        }
        .ag-header-user-row {
            white-space: normal;
            align-items: flex-start;
        }
    }
    </style>
    """
