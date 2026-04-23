from __future__ import annotations

from streamlit_folium import st_folium

from services.map_service import build_base_map, render_fund_map


def render_tab_mapa(
    filtered_gdf,
    effective_fields: dict[str, str],
    show_primary: bool,
    show_car: bool,
):
    external_toggles = {
        "show_sigef": False,
        "show_car": show_car,
        "show_assentamentos": False,
        "show_quilombolas": False,
        "show_uc": False,
        "show_ti": False,
    }

    if filtered_gdf is not None and not filtered_gdf.empty:
        mapa, layer_warnings = render_fund_map(
            filtered_gdf,
            resolved_fields=effective_fields,
            show_primary=show_primary,
            external_toggles=external_toggles,
            visible_bbox=None,
        )
    else:
        mapa = build_base_map()
        layer_warnings = []

    map_state = st_folium(
        mapa,
        width=None,
        height=520,
        key="fund_map",
        returned_objects=["bounds", "last_object_clicked_popup", "last_object_clicked_tooltip"],
    )

    return mapa, layer_warnings, map_state
