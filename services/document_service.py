from __future__ import annotations

import io
import re
import unicodedata
from pathlib import Path
from urllib.parse import quote, urlparse

import pandas as pd
import requests
import streamlit as st

from core.settings import (
    DOCS_BASE_URL,
    GCS_BUCKET_NAME,
    GCS_DOCS_PREFIX,
    GCS_INDEX_BLOB,
    INDEX_URL,
    LOCAL_DOCS_FALLBACK_DIR,
    LOCAL_DOCS_DIR,
    LOCAL_INDEX_PATH,
)

try:
    from google.cloud import storage
except ImportError:  # pragma: no cover
    storage = None

try:
    from google.auth.exceptions import DefaultCredentialsError
except ImportError:  # pragma: no cover
    DefaultCredentialsError = Exception


INDEX_SESSION_KEY = "_document_index_df"


def _is_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def _is_gs_url(value: str) -> bool:
    return str(value or "").startswith("gs://")


def _parse_gs_url(value: str) -> tuple[str, str]:
    parsed = urlparse(value)
    bucket = parsed.netloc.strip()
    blob = parsed.path.lstrip("/")
    if not bucket or not blob:
        raise ValueError(f"URL gs:// invalida: {value}")
    return bucket, blob


def _gcs_blob_path(file_name: str) -> str:
    if not GCS_DOCS_PREFIX:
        return file_name
    return f"{GCS_DOCS_PREFIX}/{file_name}"


def _download_gcs_bytes(bucket_name: str, blob_name: str) -> bytes:
    if storage is None:
        raise RuntimeError(
            "Dependencia google-cloud-storage nao instalada. "
            "Adicione-a ao ambiente para acessar arquivos privados no Google Cloud Storage."
        )

    auth_error: Exception | None = None
    clients = []
    try:
        clients.append(storage.Client())
    except DefaultCredentialsError as exc:
        auth_error = exc
    except Exception as exc:
        auth_error = exc

    try:
        clients.append(storage.Client.create_anonymous_client())
    except Exception:
        pass

    last_error: Exception | None = auth_error
    for client in clients:
        try:
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            if not blob.exists():
                raise FileNotFoundError(f"Objeto nao encontrado no GCS: gs://{bucket_name}/{blob_name}")
            return blob.download_as_bytes()
        except FileNotFoundError:
            raise
        except Exception as exc:
            last_error = exc

    if auth_error is not None:
        raise RuntimeError(
            "Nao foi possivel autenticar no Google Cloud Storage e o bucket/objeto nao esta acessivel anonimamente. "
            "Se o bucket for privado, configure ADC ou a service account do ambiente."
        ) from last_error
    raise RuntimeError(f"Falha ao acessar gs://{bucket_name}/{blob_name}") from last_error


def _download_default_gcs_index() -> bytes:
    if not GCS_BUCKET_NAME:
        raise FileNotFoundError("Bucket GCS nao configurado para leitura do indice.")
    return _download_gcs_bytes(GCS_BUCKET_NAME, GCS_INDEX_BLOB)


def _download_default_gcs_pdf(file_name: str) -> bytes:
    if not GCS_BUCKET_NAME:
        raise FileNotFoundError("Bucket GCS nao configurado para leitura dos PDFs.")
    return _download_gcs_bytes(GCS_BUCKET_NAME, _gcs_blob_path(file_name))


def _load_bytes_from_source(source: str | Path) -> bytes:
    source_str = str(source)
    if _is_gs_url(source_str):
        bucket_name, blob_name = _parse_gs_url(source_str)
        return _download_gcs_bytes(bucket_name, blob_name)
    if _is_url(source_str):
        response = requests.get(source_str, timeout=120)
        response.raise_for_status()
        return response.content

    path = Path(source_str)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {path}")
    return path.read_bytes()


def _detect_csv_separator(payload: bytes) -> str:
    sample = payload.decode("utf-8", errors="ignore").splitlines()
    first_line = next((line for line in sample if line.strip()), "")
    candidates = [";", ",", "\t", "|"]
    ranked = sorted(candidates, key=lambda sep: first_line.count(sep), reverse=True)
    return ranked[0] if first_line else ","


def _normalize_token(value: object) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"\.pdf$", "", text)
    text = re.sub(r"[^a-z0-9]+", "", text)
    return text


def normalize_shared_name(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.strip().casefold()


@st.cache_data(show_spinner="Lendo indice de arquivos...")
def load_index_dataframe() -> pd.DataFrame:
    source = INDEX_URL or str(LOCAL_INDEX_PATH)
    try:
        payload = _load_bytes_from_source(source)
    except FileNotFoundError:
        payload = _download_default_gcs_index()
        source = f"gs://{GCS_BUCKET_NAME}/{GCS_INDEX_BLOB}"

    if str(source).lower().endswith(".txt"):
        lines = [line.strip() for line in payload.decode("utf-8", errors="ignore").splitlines() if line.strip()]
        df = pd.DataFrame({"arquivo": lines})
    else:
        separator = _detect_csv_separator(payload)
        df = pd.read_csv(io.BytesIO(payload), sep=separator)

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


def get_cached_index_dataframe() -> pd.DataFrame:
    cached = st.session_state.get(INDEX_SESSION_KEY)
    if isinstance(cached, pd.DataFrame):
        return cached
    index_df = load_index_dataframe()
    st.session_state[INDEX_SESSION_KEY] = index_df
    return index_df


def _exact_candidates(index_df: pd.DataFrame, value: object) -> pd.DataFrame:
    token = _normalize_token(value)
    if not token:
        return index_df.iloc[0:0].copy()
    return index_df[index_df["match_key"] == token].copy()


def split_document_values(value: object) -> list[str]:
    raw = str(value or "").strip()
    if not raw:
        return []
    parts = [item.strip() for item in raw.split(";")]
    return [item for item in parts if item]


def _search_local_pdf_path(file_name: str) -> Path | None:
    wanted = normalize_shared_name(file_name)
    search_roots = [LOCAL_DOCS_DIR, LOCAL_DOCS_FALLBACK_DIR]
    for root in search_roots:
        if not root.exists():
            continue
        direct = root / file_name
        if direct.exists():
            return direct
        for path in root.rglob("*.pdf"):
            if normalize_shared_name(path.name) == wanted:
                return path
    return None


def _download_pdf_content(file_name: str, file_url: str = "", file_id: str = "") -> bytes:
    if file_url:
        if _is_gs_url(file_url):
            bucket_name, blob_name = _parse_gs_url(file_url)
            return _download_gcs_bytes(bucket_name, blob_name)
        response = requests.get(file_url, timeout=120)
        response.raise_for_status()
        return response.content

    if file_id:
        response = requests.get(f"https://drive.google.com/uc?export=download&id={quote(file_id)}", timeout=120)
        response.raise_for_status()
        return response.content

    if DOCS_BASE_URL:
        if _is_gs_url(DOCS_BASE_URL):
            bucket_name, base_blob = _parse_gs_url(DOCS_BASE_URL)
            blob_name = "/".join(part for part in [base_blob.rstrip("/"), file_name] if part)
            return _download_gcs_bytes(bucket_name, blob_name)
        base = DOCS_BASE_URL.rstrip("/")
        response = requests.get(f"{base}/{quote(file_name)}", timeout=120)
        response.raise_for_status()
        return response.content

    if GCS_BUCKET_NAME:
        try:
            return _download_default_gcs_pdf(file_name)
        except (FileNotFoundError, RuntimeError):
            pass

    pdf_path = _search_local_pdf_path(file_name)
    if pdf_path is None:
        raise FileNotFoundError(
            f"PDF nao encontrado: {file_name}. Locais pesquisados: gs://{GCS_BUCKET_NAME}/{_gcs_blob_path(file_name)}, "
            f"{LOCAL_DOCS_DIR} e {LOCAL_DOCS_FALLBACK_DIR}"
        )
    return pdf_path.read_bytes()


def resolve_document_for_value(index_df: pd.DataFrame, value: object, document_type: str) -> dict[str, object]:
    candidates = _exact_candidates(index_df=index_df, value=value)
    if candidates.empty:
        return {"found": False, "document_type": document_type, "query_value": value}

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
