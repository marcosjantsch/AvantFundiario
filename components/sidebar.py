from __future__ import annotations

import pandas as pd
import streamlit as st


def _safe_select_index(options: list[str], selected: str) -> int:
    if selected in options:
        return options.index(selected)
    return 0


def _normalize_key(value: object) -> str:
    return str(value or "").strip().casefold()


def _resolve_column_name(df: pd.DataFrame, target: str) -> str | None:
    target_norm = _normalize_key(target)
    for column in df.columns:
        if _normalize_key(column) == target_norm:
            return column
    return None


def _filter_gfp_base(df: pd.DataFrame) -> pd.DataFrame:
    corporacao_col = _resolve_column_name(df, "Corporacao")
    if corporacao_col is None:
        return df.iloc[0:0].copy()
    return df[df[corporacao_col].astype(str).str.strip().str.casefold() == "gfp"].copy()


def _get_unique_sorted_values(df: pd.DataFrame, field: str) -> list[str]:
    if not field or field not in df.columns:
        return []
    values = [str(value).strip() for value in df[field].dropna().tolist() if str(value).strip()]
    return sorted(dict.fromkeys(values))


def _filter_by_value(df: pd.DataFrame, field: str, value: str) -> pd.DataFrame:
    if not value or field not in df.columns:
        return df.copy()
    return df[df[field].astype(str).str.strip() == str(value).strip()].copy()


def render_sidebar(
    df: pd.DataFrame,
    resolved_fields: dict[str, str],
    source: dict[str, object],
    on_empresa_change,
    on_bloco_change,
) -> dict[str, object]:
    empresa_col = resolved_fields["empresa"]
    bloco_col = resolved_fields["bloco"]
    fazenda_col = resolved_fields["fazenda"]

    df_base_sidebar = _filter_gfp_base(df)

    empresa_selecionada = st.session_state.get("empresa_selecionada", "")
    bloco_selecionado = st.session_state.get("bloco_selecionado", "")
    fazenda_selecionada = st.session_state.get("fazenda_selecionada", "")

    empresa_options = [""] + _get_unique_sorted_values(df_base_sidebar, empresa_col)

    df_blocos = _filter_by_value(df_base_sidebar, empresa_col, empresa_selecionada)
    bloco_options = [""] + _get_unique_sorted_values(df_blocos, bloco_col)
    if bloco_selecionado not in bloco_options:
        st.session_state["bloco_selecionado"] = ""
        st.session_state["fazenda_selecionada"] = ""

    df_fazendas = _filter_by_value(df_blocos, bloco_col, bloco_selecionado)
    fazenda_options = [""] + _get_unique_sorted_values(df_fazendas, fazenda_col)
    if fazenda_selecionada not in fazenda_options:
        st.session_state["fazenda_selecionada"] = ""

    with st.sidebar:
        st.markdown("## Filtros")
        st.caption(
            f"Fonte: {source.get('file_name')} | campos: {resolved_fields['empresa']}, "
            f"{resolved_fields['bloco']}, {resolved_fields['fazenda']}"
        )

        st.selectbox(
            "Empresa",
            empresa_options,
            index=_safe_select_index(empresa_options, st.session_state["empresa_selecionada"]),
            key="empresa_selecionada",
            format_func=lambda value: value if value else "Selecione a empresa",
            on_change=on_empresa_change,
        )

        st.selectbox(
            "Bloco",
            bloco_options,
            index=_safe_select_index(bloco_options, st.session_state["bloco_selecionado"]),
            key="bloco_selecionado",
            format_func=lambda value: value if value else "Selecione o bloco",
            disabled=not bool(st.session_state["empresa_selecionada"]),
            on_change=on_bloco_change,
        )

        st.selectbox(
            "Fazenda",
            fazenda_options,
            index=_safe_select_index(fazenda_options, st.session_state["fazenda_selecionada"]),
            key="fazenda_selecionada",
            format_func=lambda value: value if value else "Todas as fazendas do bloco",
            disabled=not bool(st.session_state["bloco_selecionado"]),
        )

        apply_ready = all(
            [
                st.session_state.get("empresa_selecionada"),
                st.session_state.get("bloco_selecionado"),
            ]
        )
        apply_clicked = st.button("Aplicar", use_container_width=True, disabled=not apply_ready)

        st.markdown("## Camadas")
        show_primary = st.checkbox("Matricula", value=True)
        show_car = st.checkbox("Exibir CAR", value=False)

    return {
        "empresa": st.session_state.get("empresa_selecionada", ""),
        "bloco": st.session_state.get("bloco_selecionado", ""),
        "fazenda": st.session_state.get("fazenda_selecionada", ""),
        "apply_clicked": apply_clicked,
        "apply_ready": apply_ready,
        "show_primary": show_primary,
        "show_car": show_car,
        "df_base_sidebar": df_base_sidebar,
    }
