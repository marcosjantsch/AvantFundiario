from __future__ import annotations

import tempfile
import unicodedata
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
import streamlit as st

from core.settings import BASE_DIR, LOCAL_SHAPEFILE_PATH, SHAPEFILE_QUERY


FIELD_ALIASES = {
    "empresa": ["empresa"],
    "bloco": ["bloco", "talhao", "quadra"],
    "fazenda": ["fazenda", "propriedade", "propriedad"],
    "uf": ["uf"],
    "matricula": ["matricula", "registro", "numeromatricula"],
    "area": ["area", "areaha", "areatotal"],
    "ccir": ["ccir"],
    "itr": ["itr", "nirf"],
    "car1": ["car1", "car", "k1"],
    "car_estadu": ["carestadu", "carestadual", "cefir", "sicaruf"],
    "geo": ["geo", "sigef", "georef", "georeferenciamento"],
    "outros": ["outros", "observacao", "observacoes", "documentos", "docs"],
    "municipio": ["municipio", "município"],
}


def normalize_field_name(name: str) -> str:
    text = unicodedata.normalize("NFKD", str(name or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.upper().strip()
    return "".join(ch for ch in text if ch.isalnum())


def detect_field(columns: list[str], aliases: dict[str, list[str]], key: str) -> str | None:
    normalized_columns = {normalize_field_name(column): column for column in columns}
    for alias in aliases.get(key, []):
        alias_norm = normalize_field_name(alias)
        if alias_norm in normalized_columns:
            return normalized_columns[alias_norm]
        for column_norm, original in normalized_columns.items():
            if column_norm.startswith(alias_norm):
                return original
    return None


def resolve_required_fields(columns: list[str]) -> dict[str, str]:
    resolved: dict[str, str] = {}
    for key in FIELD_ALIASES:
        field = detect_field(columns, FIELD_ALIASES, key)
        if field:
            resolved[key] = field

    for required in ["empresa", "bloco", "fazenda"]:
        if required not in resolved:
            raise KeyError(f"Campo obrigatorio nao encontrado no shapefile: {required}")
    return resolved


def _normalize_name(value: object) -> str:
    return normalize_field_name(str(value or ""))


def _extract_zip(zip_path: Path, target_dir: Path) -> Path:
    with zipfile.ZipFile(zip_path, "r") as archive:
        archive.extractall(target_dir)
    shp_files = list(target_dir.rglob("*.shp"))
    if not shp_files:
        raise FileNotFoundError("Nenhum arquivo .shp foi encontrado no ZIP baixado.")
    return shp_files[0]


def _find_shp_in_zip(zip_path: Path) -> str | None:
    try:
        with zipfile.ZipFile(zip_path, "r") as archive:
            for member in archive.namelist():
                if member.lower().endswith(".shp"):
                    return member
    except zipfile.BadZipFile:
        return None
    return None


def _build_candidate(path: Path, source: str, matched_name: str | None = None) -> dict[str, str]:
    return {
        "file_name": path.name,
        "full_path": str(path.resolve()),
        "identifier": str(path.resolve()),
        "extension": path.suffix.lower(),
        "source": source,
        "matched_name": matched_name or path.name,
    }


def _search_files_recursive(root: Path, query: str) -> list[dict[str, str]]:
    if not root.exists():
        return []

    query_token = _normalize_name(query)
    candidates: list[dict[str, str]] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix not in {".shp", ".zip"}:
            continue
        if suffix == ".shp":
            if not query_token or query_token in _normalize_name(path.name):
                candidates.append(_build_candidate(path, source="filesystem"))
            continue
        zip_member = _find_shp_in_zip(path)
        if not zip_member:
            continue
        matched_name = f"{path.name}!{Path(zip_member).name}"
        if not query_token or query_token in _normalize_name(path.name) or query_token in _normalize_name(zip_member):
            candidates.append(_build_candidate(path, source="zip", matched_name=matched_name))
    return candidates


def _rank_candidates(candidates: list[dict[str, str]], query: str) -> list[dict[str, str]]:
    query_token = _normalize_name(query)
    project_data_dir = str((BASE_DIR / "data").resolve()).lower()

    def score(item: dict[str, str]) -> tuple[int, int, int, int, str]:
        matched_token = _normalize_name(item["matched_name"])
        exact = int(bool(query_token) and matched_token == query_token)
        contains = int(bool(query_token) and query_token in matched_token)
        local = int(item["full_path"].lower().startswith(project_data_dir))
        shp_bonus = int(item["extension"] == ".shp")
        return (exact, contains, local, shp_bonus, item["full_path"].lower())

    return sorted(candidates, key=score, reverse=True)


@st.cache_data(show_spinner="Localizando shapefile...")
def find_shapefile_candidate() -> dict[str, str]:
    roots = [BASE_DIR / "data"]

    all_candidates: list[dict[str, str]] = []
    if LOCAL_SHAPEFILE_PATH.exists():
        all_candidates.append(_build_candidate(LOCAL_SHAPEFILE_PATH, source="local-explicit"))
    for root in roots:
        all_candidates.extend(_search_files_recursive(root=root, query=SHAPEFILE_QUERY))

    ranked = _rank_candidates(all_candidates, SHAPEFILE_QUERY)
    if not ranked:
        searched_roots = ", ".join(str(root) for root in roots)
        raise FileNotFoundError(
            "Nenhum shapefile .shp ou .zip contendo shapefile foi encontrado. "
            f"Locais pesquisados: {searched_roots}"
        )
    return ranked[0]


def _load_shapefile(shp_path: Path) -> gpd.GeoDataFrame:
    if not shp_path.exists():
        raise FileNotFoundError(f"Shapefile nao encontrado: {shp_path}")
    gdf = gpd.read_file(shp_path)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    elif str(gdf.crs).upper() != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")
    return gdf


def _load_shapefile_from_candidate(candidate: dict[str, str]) -> gpd.GeoDataFrame:
    source = candidate["source"]
    path = Path(candidate["full_path"])
    if source == "zip":
        with tempfile.TemporaryDirectory(prefix="avante_shape_zip_") as tmp_dir:
            shp_path = _extract_zip(path, Path(tmp_dir))
            return _load_shapefile(shp_path)
    return _load_shapefile(path)


@st.cache_data(show_spinner="Carregando base fundiaria...")
def load_fund_context() -> dict[str, object]:
    candidate = find_shapefile_candidate()
    gdf = _load_shapefile_from_candidate(candidate).copy()
    gdf["__row_id__"] = range(len(gdf))
    resolved_fields = resolve_required_fields(list(gdf.columns))
    return {
        "gdf": gdf,
        "resolved_fields": resolved_fields,
        "source": candidate,
        "columns": list(gdf.columns),
    }


def get_unique_sorted_values(df: pd.DataFrame, field: str) -> list[str]:
    if not field or field not in df.columns:
        return []
    values = [str(value).strip() for value in df[field].dropna().tolist() if str(value).strip()]
    return sorted(dict.fromkeys(values))


def filter_dataframe_by_empresa(df: pd.DataFrame, field_empresa: str, empresa: str) -> pd.DataFrame:
    return df[df[field_empresa].astype(str).str.strip() == str(empresa).strip()].copy()


def filter_dataframe_by_empresa_bloco(
    df: pd.DataFrame,
    field_empresa: str,
    field_bloco: str,
    empresa: str,
    bloco: str,
) -> pd.DataFrame:
    df_empresa = filter_dataframe_by_empresa(df, field_empresa, empresa)
    return df_empresa[df_empresa[field_bloco].astype(str).str.strip() == str(bloco).strip()].copy()


def filter_dataframe_by_empresa_bloco_fazenda(
    df: pd.DataFrame,
    field_empresa: str,
    field_bloco: str,
    field_fazenda: str,
    empresa: str,
    bloco: str,
    fazenda: str,
) -> pd.DataFrame:
    df_bloco = filter_dataframe_by_empresa_bloco(df, field_empresa, field_bloco, empresa, bloco)
    return df_bloco[df_bloco[field_fazenda].astype(str).str.strip() == str(fazenda).strip()].copy()


def get_blocos_by_empresa(df: pd.DataFrame, field_empresa: str, field_bloco: str, empresa: str) -> list[str]:
    df_empresa = filter_dataframe_by_empresa(df, field_empresa, empresa)
    return get_unique_sorted_values(df_empresa, field_bloco)


def get_fazendas_by_empresa_bloco(
    df: pd.DataFrame,
    field_empresa: str,
    field_bloco: str,
    field_fazenda: str,
    empresa: str,
    bloco: str,
) -> list[str]:
    df_bloco = filter_dataframe_by_empresa_bloco(df, field_empresa, field_bloco, empresa, bloco)
    return get_unique_sorted_values(df_bloco, field_fazenda)


def summarize_filter_options(gdf: pd.DataFrame, resolved_fields: dict[str, str]) -> dict[str, object]:
    empresa_col = resolved_fields["empresa"]
    return {"empresa": get_unique_sorted_values(gdf, empresa_col)}


def apply_filters(
    gdf: gpd.GeoDataFrame,
    filters: dict[str, object] | None,
    resolved_fields: dict[str, str],
) -> gpd.GeoDataFrame:
    if not filters:
        return gdf.iloc[0:0].copy()

    empresa = str(filters.get("empresa") or "").strip()
    bloco = str(filters.get("bloco") or "").strip()
    fazenda = str(filters.get("fazenda") or "").strip()
    if not empresa or not bloco:
        return gdf.iloc[0:0].copy()

    if fazenda:
        return (
            filter_dataframe_by_empresa_bloco_fazenda(
                gdf,
                resolved_fields["empresa"],
                resolved_fields["bloco"],
                resolved_fields["fazenda"],
                empresa,
                bloco,
                fazenda,
            )
            .reset_index(drop=True)
        )

    return (
        filter_dataframe_by_empresa_bloco(
            gdf,
            resolved_fields["empresa"],
            resolved_fields["bloco"],
            empresa,
            bloco,
        )
        .reset_index(drop=True)
    )
