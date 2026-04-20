from __future__ import annotations

import io
import re
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import requests
import streamlit as st

from core.settings import DOCS_BASE_URL, INDEX_URL, LOCAL_DOCS_DIR, LOCAL_INDEX_PATH


def _is_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def _normalize_token(value: object) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"\.pdf$", "", text)
    text = re.sub(r"[^a-z0-9]+", "", text)
    return text


def _load_bytes_from_source(source: str | Path) -> bytes:
    source_str = str(source)
    if _is_url(source_str):
        response = requests.get(source_str, timeout=120)
        response.raise_for_status()
        return response.content

    path = Path(source_str)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {path}")
    return path.read_bytes()


@st.cache_data(show_spinner="Lendo indice de arquivos...")
def load_index_dataframe() -> pd.DataFrame:
    source = INDEX_URL or str(LOCAL_INDEX_PATH)
    payload = _load_bytes_from_source(source)

    if str(source).lower().endswith(".txt"):
        lines = [line.strip() for line in payload.decode("utf-8", errors="ignore").splitlines() if line.strip()]
        df = pd.DataFrame({"arquivo": lines})
    else:
        df = pd.read_csv(io.BytesIO(payload), sep=None, engine="python")

    if "arquivo" not in df.columns:
        first_column = df.columns[0]
        df = df.rename(columns={first_column: "arquivo"})

    if "nome_sem_extensao" not in df.columns:
        df["nome_sem_extensao"] = df["arquivo"].astype(str).str.replace(r"\.pdf$", "", regex=True)

    df["arquivo"] = df["arquivo"].astype(str).str.strip()
    df["nome_sem_extensao"] = df["nome_sem_extensao"].astype(str).str.strip()
    df["match_key"] = df["nome_sem_extensao"].map(_normalize_token)
    df["file_name"] = df["arquivo"]
    if "file_url" in df.columns:
        df["file_url"] = df["file_url"].fillna("").astype(str).str.strip()
    if "file_id" in df.columns:
        df["file_id"] = df["file_id"].fillna("").astype(str).str.strip()
    return df


def list_available_files(index_df: pd.DataFrame) -> list[str]:
    return index_df["file_name"].dropna().astype(str).tolist()


def _exact_candidates(index_df: pd.DataFrame, value: object) -> pd.DataFrame:
    token = _normalize_token(value)
    if not token:
        return index_df.iloc[0:0].copy()

    exact = index_df[index_df["match_key"] == token].copy()
    return exact


def split_document_values(value: object) -> list[str]:
    raw = str(value or "").strip()
    if not raw:
        return []
    parts = [item.strip() for item in raw.split(";")]
    return [item for item in parts if item]


def _resolve_local_pdf_path(file_name: str) -> Path:
    return LOCAL_DOCS_DIR / file_name


def _download_pdf_content(file_name: str, file_url: str = "", file_id: str = "") -> bytes:
    if file_url:
        response = requests.get(file_url, timeout=120)
        response.raise_for_status()
        return response.content

    if file_id:
        response = requests.get(f"https://drive.google.com/uc?export=download&id={quote(file_id)}", timeout=120)
        response.raise_for_status()
        return response.content

    if DOCS_BASE_URL:
        base = DOCS_BASE_URL.rstrip("/")
        response = requests.get(f"{base}/{quote(file_name)}", timeout=120)
        response.raise_for_status()
        return response.content

    pdf_path = _resolve_local_pdf_path(file_name)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF nao encontrado: {pdf_path}")
    return pdf_path.read_bytes()


def resolve_document_for_value(index_df: pd.DataFrame, value: object, document_type: str) -> dict[str, object]:
    candidates = _exact_candidates(index_df=index_df, value=value)
    if candidates.empty:
        return {
            "found": False,
            "document_type": document_type,
            "query_value": value,
        }

    record = candidates.sort_values(by=["file_name"], ascending=[True]).iloc[0]
    file_name = str(record["file_name"])
    file_url = str(record["file_url"]) if "file_url" in record.index else ""
    file_id = str(record["file_id"]) if "file_id" in record.index else ""
    content = _download_pdf_content(file_name=file_name, file_url=file_url, file_id=file_id)
    return {
        "found": True,
        "document_type": document_type,
        "query_value": value,
        "file_name": file_name,
        "content": content,
    }


def resolve_documents_for_value(index_df: pd.DataFrame, value: object, document_type: str) -> dict[str, object]:
    items = split_document_values(value)
    if not items:
        return {"found": False, "document_type": document_type, "query_value": value, "files": []}

    files: list[dict[str, object]] = []
    missing: list[str] = []
    for item in items:
        result = resolve_document_for_value(index_df=index_df, value=item, document_type=document_type)
        if result.get("found"):
            files.append({"query_value": item, "file_name": result["file_name"], "content": result["content"]})
        else:
            missing.append(item)

    return {
        "found": bool(files),
        "document_type": document_type,
        "query_value": value,
        "files": files,
        "missing": missing,
    }
