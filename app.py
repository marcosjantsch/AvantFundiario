from __future__ import annotations

import pandas as pd
import streamlit as st

from components.header import render_header
from components.sidebar import render_sidebar
from core.settings import APP_ICON, APP_TITLE, APP_VERSION, AUTH_CONFIG_PATH, DOCUMENT_COLUMNS, LOGO_PATH
from core.styles import apply_styles
from services.auth_service import ensure_auth_session_defaults, render_login_screen
from services.document_service import get_cached_index_dataframe, resolve_documents_for_value
from services.shapefile_service import apply_filters, load_fund_context
from services.table_service import (
    build_display_table,
    build_table_styler,
    describe_active_selection,
    export_table_to_excel_bytes,
    resolve_document_click,
)
from tabs.tab_mapa import render_tab_mapa


st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_styles()


def _reset_applied_filters() -> None:
    st.session_state["applied_filters"] = None


def _on_empresa_change() -> None:
    st.session_state["bloco_selecionado"] = ""
    st.session_state["fazenda_selecionada"] = ""
    _reset_applied_filters()


def _on_bloco_change() -> None:
    st.session_state["fazenda_selecionada"] = ""
    _reset_applied_filters()


def _ensure_filter_state() -> None:
    st.session_state.setdefault("empresa_selecionada", "")
    st.session_state.setdefault("bloco_selecionado", "")
    st.session_state.setdefault("fazenda_selecionada", "")
    st.session_state.setdefault("applied_filters", None)


def _render_document_panel(table_df: pd.DataFrame) -> None:
    st.markdown("## Tabela de dados")
    export_bytes = export_table_to_excel_bytes(table_df)
    st.download_button(
        "Exportar Excel",
        data=export_bytes,
        file_name="consulta_fundiaria.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="export_excel_button",
    )
    st.markdown(
        "<div class='af-table-hint'>Passe o mouse pela tabela e clique em uma celula destacada para baixar o documento correspondente quando ele existir no indice.</div>",
        unsafe_allow_html=True,
    )

    display_df = table_df.drop(columns="__row_id__", errors="ignore")
    styled_df = build_table_styler(table_df)
    event = st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-cell",
        column_config={
            col: st.column_config.TextColumn(width="small") for col in DOCUMENT_COLUMNS if col in display_df.columns
        },
        key="fund_docs_table",
    )

    selection = describe_active_selection(event, display_df=display_df)
    if selection is None:
        return

    clicked = resolve_document_click(selection=selection, table_df=table_df, display_df=display_df)
    if clicked is None:
        return

    st.markdown(f"### Documento: `{clicked['column']}`")
    st.write(f"Valor selecionado: `{clicked['value'] or '-'}`")
    st.caption(
        "Clique para baixar quando cada valor da celula corresponder ao nome cadastrado no indice. "
        "Valores separados por ';' geram multiplos downloads."
    )
    try:
        if "_document_index_df" in st.session_state:
            index_df = get_cached_index_dataframe()
        else:
            with st.spinner("Carregando indice de documentos..."):
                index_df = get_cached_index_dataframe()
        result = resolve_documents_for_value(index_df=index_df, value=clicked["value"], document_type=clicked["column"])
    except Exception as exc:
        st.error(f"Erro ao baixar documento: {exc}")
        return

    if not result["found"]:
        st.error("Arquivo nao encontrado")
        return

    st.success(f"{len(result['files'])} arquivo(s) localizado(s).")
    for index, file_item in enumerate(result["files"], start=1):
        st.download_button(
            label=f"Baixar PDF {index}: {file_item['file_name']}",
            data=file_item["content"],
            file_name=file_item["file_name"],
            mime="application/pdf",
            key=f"download_{clicked['row_id']}_{clicked['column']}_{index}",
        )
    if result.get("missing"):
        st.warning("Arquivos nao encontrados: " + "; ".join(result["missing"]))


def _render_authenticated_app() -> None:
    _ensure_filter_state()
    render_header(
        logo_path=LOGO_PATH,
        app_name=APP_TITLE,
        version=APP_VERSION,
        user=st.session_state.get("nome"),
        role=st.session_state.get("perfil"),
        current_mode="Consulta Fundiaria",
        username=st.session_state.get("username"),
        authenticator=st.session_state.get("authenticator"),
        subtitle="Mapa, filtros, documentos e camadas de apoio territorial.",
    )

    try:
        fund_context = load_fund_context()
    except FileNotFoundError as exc:
        st.error("Base fundiaria principal nao encontrada no ambiente atual.")
        st.info(
            "Inclua o shapefile principal `Geo.shp` e seus arquivos auxiliares dentro de `data/`."
        )
        st.caption(str(exc))
        st.stop()
    except Exception as exc:
        st.error("Nao foi possivel carregar a base fundiaria principal.")
        st.caption(str(exc))
        st.stop()

    gdf = fund_context["gdf"]
    resolved_fields = fund_context["resolved_fields"]
    filters = render_sidebar(
        gdf,
        resolved_fields=resolved_fields,
        source=fund_context["source"],
        on_empresa_change=_on_empresa_change,
        on_bloco_change=_on_bloco_change,
    )

    if filters.get("apply_clicked") and filters.get("apply_ready"):
        st.session_state["applied_filters"] = {
            "empresa": filters["empresa"],
            "bloco": filters["bloco"],
            "fazenda": filters["fazenda"],
        }

    applied_filters = st.session_state.get("applied_filters")
    gdf_base_sidebar = filters.get("df_base_sidebar", gdf.iloc[0:0].copy())
    filtered_gdf = apply_filters(gdf_base_sidebar, applied_filters, resolved_fields=resolved_fields)
    effective_fields = dict(resolved_fields)
    table_df = build_display_table(filtered_gdf, effective_fields) if applied_filters else pd.DataFrame()

    if not filters.get("empresa"):
        st.info("Selecione uma empresa para habilitar o filtro de bloco.")
        return
    if not filters.get("bloco"):
        st.info("Selecione um bloco da empresa escolhida para habilitar o botao Aplicar.")
        return
    if not applied_filters:
        st.info("Clique em Aplicar para carregar o subconjunto filtrado no mapa, tabela e exportacao.")
        return
    if filtered_gdf.empty:
        if filters.get("fazenda"):
            st.warning("Nenhum registro encontrado para a combinacao Empresa + BLOCO + Fazenda.")
        else:
            st.warning("Nenhum registro encontrado para a combinacao Empresa + BLOCO.")
        return

    st.markdown(
        "<div class='af-soft-status'>O sistema abre a consulta primeiro. O indice de documentos e carregado apenas quando voce clica em uma celula documental.</div>",
        unsafe_allow_html=True,
    )
    _render_document_panel(table_df=table_df)

    st.markdown("## Mapa")
    _, layer_warnings, _ = render_tab_mapa(
        filtered_gdf=filtered_gdf,
        effective_fields=effective_fields,
        show_primary=bool(filters.get("show_primary", True)),
        show_car=bool(filters.get("show_car", False)),
    )

    for warning in layer_warnings:
        st.warning(warning)


def main() -> None:
    ensure_auth_session_defaults()
    if not render_login_screen(AUTH_CONFIG_PATH):
        return
    _render_authenticated_app()


if __name__ == "__main__":
    main()
