from __future__ import annotations

from io import BytesIO
from typing import Any

import geopandas as gpd
import pandas as pd

from core.settings import DOCUMENT_COLUMNS, TABLE_COLUMN_ORDER


DISPLAY_TO_FIELD_KEY = {
    "Empresa": "empresa",
    "BLOCO": "bloco",
    "Fazenda": "fazenda",
    "MATRICULA": "matricula",
    "Area": "area",
    "CCIR": "ccir",
    "ITR": "itr",
    "CAR1": "car1",
    "CAR_ESTADUAL": "car_estadu",
    "GEO": "geo",
    "Outros": "outros",
    "Municipio": "municipio",
    "UF": "uf",
}

HIGHLIGHT_COLUMNS = {"MATRICULA", "CCIR", "ITR", "CAR1", "CAR_ESTADUAL", "Outros"}


def build_display_table(gdf: gpd.GeoDataFrame, resolved_fields: dict[str, str]) -> pd.DataFrame:
    if gdf.empty:
        return pd.DataFrame(columns=["__row_id__", *TABLE_COLUMN_ORDER])

    source_df = pd.DataFrame(gdf.drop(columns="geometry", errors="ignore")).copy()
    display_df = pd.DataFrame()
    display_df["__row_id__"] = source_df.get("__row_id__", pd.Series(range(len(source_df))))

    for display_col in TABLE_COLUMN_ORDER:
        field_key = DISPLAY_TO_FIELD_KEY.get(display_col)
        source_col = resolved_fields.get(field_key, "")
        if source_col and source_col in source_df.columns:
            display_df[display_col] = source_df[source_col]
        else:
            display_df[display_col] = ""

    display_df = display_df.fillna("")
    if "Area" in display_df.columns:
        display_df["Area"] = display_df["Area"].map(_format_area)
    return display_df


def _format_area(value: object) -> object:
    if value in ("", None):
        return ""
    try:
        number = float(str(value).replace(",", "."))
    except Exception:
        return value
    return f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def export_table_to_excel_bytes(display_df: pd.DataFrame) -> bytes:
    export_df = display_df.drop(columns="__row_id__", errors="ignore").copy()
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="consulta")
    buffer.seek(0)
    return buffer.read()


def build_table_styler(display_df: pd.DataFrame):
    visible_df = display_df.drop(columns="__row_id__", errors="ignore").copy()
    styler = visible_df.style

    def highlight_column(series: pd.Series) -> list[str]:
        if series.name in HIGHLIGHT_COLUMNS:
            return [
                "background-color: #fff7d6; color: #1f3146; font-weight: 600; border-color: #e8d48a;"
                for _ in series
            ]
        return ["color: #1f3146;" for _ in series]

    return styler.apply(highlight_column, axis=0)


def _is_int_like(value: object) -> bool:
    try:
        int(str(value))
        return True
    except Exception:
        return False


def describe_active_selection(event: Any, display_df: pd.DataFrame | None = None) -> dict[str, int | str] | None:
    if not event:
        return None
    selection = event.get("selection") if isinstance(event, dict) else None
    if not selection:
        return None

    cells = selection.get("cells") or []
    if cells:
        cell = cells[0]
        if isinstance(cell, dict):
            return {"row": int(cell["row"]), "column": int(cell["column"])}
        if isinstance(cell, (list, tuple)) and len(cell) >= 2:
            left, right = cell[0], cell[1]
            if _is_int_like(left) and not _is_int_like(right):
                return {"row": int(str(left)), "column": str(right)}
            if _is_int_like(right) and not _is_int_like(left):
                return {"row": int(str(right)), "column": str(left)}
            if isinstance(left, str) and not isinstance(right, str):
                return {"row": int(right), "column": left}
            if isinstance(right, str) and not isinstance(left, str):
                return {"row": int(left), "column": right}
            return {"row": int(left), "column": int(right)}

    rows = selection.get("rows") or []
    columns = selection.get("columns") or []
    if rows and columns:
        column_value = columns[0]
        if isinstance(column_value, str):
            return {"row": int(rows[0]), "column": column_value}
        return {"row": int(rows[0]), "column": int(column_value)}
    return None


def resolve_document_click(
    selection: dict[str, int | str],
    table_df: pd.DataFrame,
    display_df: pd.DataFrame | None = None,
) -> dict[str, object] | None:
    row_idx = int(selection["row"])
    display_source = display_df if display_df is not None else table_df.drop(columns="__row_id__", errors="ignore")
    column_value = selection["column"]
    if row_idx >= len(table_df):
        return None

    if isinstance(column_value, str):
        column_name = column_value
    else:
        col_idx = int(column_value)
        if col_idx >= len(display_source.columns):
            return None
        column_name = display_source.columns[col_idx]

    if column_name not in DOCUMENT_COLUMNS:
        return None

    row = table_df.iloc[row_idx]
    return {
        "row_id": row.get("__row_id__", row_idx),
        "column": column_name,
        "value": row.get(column_name, ""),
    }
