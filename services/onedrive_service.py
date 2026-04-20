from __future__ import annotations

import base64
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


def _is_onedrive_share_url(value: str) -> bool:
    lowered = str(value or "").lower()
    return "1drv.ms/" in lowered or "onedrive.live.com/" in lowered


def _encode_onedrive_share_url(value: str) -> str:
    token = base64.b64encode(value.encode("utf-8")).decode("utf-8")
    token = token.replace("/", "_").replace("+", "-").rstrip("=")
    return f"u!{token}"


def _onedrive_api_url(share_url: str, suffix: str) -> str:
    token = _encode_onedrive_share_url(share_url)
    suffix = suffix if suffix.startswith("/") else f"/{suffix}"
    return f"https://api.onedrive.com/v1.0/shares/{token}{suffix}"


@st.cache_data(show_spinner=False, ttl=900)
def _list_onedrive_folder_children(folder_url: str) -> list[dict[str, object]]:
    response = requests.get(_onedrive_api_url(folder_url, "/root/children"), timeout=120)
    response.raise_for_status()
    payload = response.json() or {}
    return list(payload.get("value") or [])


def _download_onedrive_shared_file(source_url: str) -> bytes:
    response = requests.get(_onedrive_api_url(source_url, "/root/content"), timeout=120, allow_redirects=True)
    response.raise_for_status()
    return response.content


def _download_onedrive_folder_file(folder_url: str, file_name: str) -> bytes:
    wanted = str(file_name or "").strip().casefold()
    for item in _list_onedrive_folder_children(folder_url):
        item_name = str((item or {}).get("name") or "").strip()
        if item_name.casefold() != wanted:
            continue
        download_url = str((item or {}).get("@content.downloadUrl") or "").strip()
        if download_url:
            response = requests.get(download_url, timeout=120)
            response.raise_for_status()
            return response.content
    raise FileNotFoundError(f"Arquivo nao encontrado na pasta compartilhada: {file_name}")


def _normalize_token(value: object) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"\.pdf$", "", text)
    text = re.sub(r"[^a-z0-9]+", "", text)
    return text


def _load_bytes_from_source(source: str | Path) -> bytes:
    source_str = str(source)
    if _is_url(source_str):
        if _is_onedrive_share_url(source_str):
            return _download_onedrive_shared_file(source_str)
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
        if _is_onedrive_share_url(DOCS_BASE_URL):
            return _download_onedrive_folder_file(DOCS_BASE_URL, file_name)
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
