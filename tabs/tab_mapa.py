from __future__ import annotations

import folium
import geopandas as gpd
import pandas as pd
from shapely.geometry import box
from streamlit_folium import st_folium

from services.map_service import build_base_map, render_fund_map


def _serialize_scalar(value):
    if pd.isna(value):
        return None
    if isinstance(value, (pd.Timestamp, pd.Timedelta)):
        return value.isoformat()
    return value


def _json_safe_gdf(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    safe_gdf = gdf.copy()
    for column in safe_gdf.columns:
        if column == "geometry":
            continue
        series = safe_gdf[column]
        if pd.api.types.is_datetime64_any_dtype(series) or pd.api.types.is_timedelta64_dtype(series):
            safe_gdf[column] = series.map(_serialize_scalar)
            continue
        if pd.api.types.is_object_dtype(series):
            safe_gdf[column] = series.map(_serialize_scalar)
    return safe_gdf


def _clip_auxiliary_layer_to_bbox(
    gdf: gpd.GeoDataFrame | None,
    visible_bbox: tuple[float, float, float, float] | None,
) -> gpd.GeoDataFrame | None:
    if gdf is None or gdf.empty:
        return gdf
    if not visible_bbox:
        return gdf.head(1500).copy()

    try:
        xmin, ymin, xmax, ymax = visible_bbox
        bbox_gdf = gpd.GeoDataFrame(geometry=[box(xmin, ymin, xmax, ymax)], crs="EPSG:4326").to_crs(3857)
        query_union = bbox_gdf.geometry.iloc[0]
        clipped = gdf.to_crs(3857)
        clipped = clipped[clipped.intersects(query_union)].copy()
        if clipped.empty:
            return clipped.to_crs(4326)
        clipped["geometry"] = clipped.geometry.intersection(query_union)
        clipped = clipped[clipped.geometry.notna() & ~clipped.geometry.is_empty].copy()
        return clipped.to_crs(4326)
    except Exception:
        return gdf.head(1500).copy()


def _add_auxiliary_layer(
    mapa: folium.Map,
    gdf: gpd.GeoDataFrame | None,
    visible_bbox: tuple[float, float, float, float] | None,
    name: str,
    style: dict[str, object],
) -> None:
    if gdf is None or gdf.empty:
        return
    clipped_gdf = _clip_auxiliary_layer_to_bbox(gdf, visible_bbox)
    if clipped_gdf is None or clipped_gdf.empty:
        return
    safe_gdf = _json_safe_gdf(clipped_gdf)
    popup_fields = [column for column in safe_gdf.columns if column != "geometry"][:10]
    popup = None
    if popup_fields:
        popup = folium.GeoJsonPopup(
            fields=popup_fields,
            aliases=[f"{field}: " for field in popup_fields],
            labels=True,
            sticky=False,
        )
    folium.GeoJson(
        safe_gdf,
        name=name,
        style_function=lambda _: style,
        popup=popup,
    ).add_to(mapa)


def _ensure_layer_control(mapa: folium.Map) -> None:
    if any(isinstance(child, folium.map.LayerControl) for child in mapa._children.values()):
        return
    folium.LayerControl(collapsed=False).add_to(mapa)


def render_tab_mapa(
    filtered_gdf,
    effective_fields: dict[str, str],
    show_primary: bool,
    layer_request: dict[str, object] | None,
    camadas_auxiliares: dict[str, gpd.GeoDataFrame | None],
):
    visible_bbox = None if not layer_request else layer_request.get("bbox")
    external_toggles = {
        "show_sigef": False,
        "show_car": bool(layer_request and layer_request.get("show_car")),
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
            visible_bbox=visible_bbox,
        )
    else:
        mapa = build_base_map()
        layer_warnings = []

    if layer_request:
        _add_auxiliary_layer(
            mapa,
            camadas_auxiliares.get("quilombolas"),
            visible_bbox,
            "Areas de Quilombolas",
            {"color": "#7c3aed", "weight": 1.8, "fillColor": "#7c3aed", "fillOpacity": 0.06},
        )
        _add_auxiliary_layer(
            mapa,
            camadas_auxiliares.get("assentamento_brasil"),
            visible_bbox,
            "Assentamento Brasil",
            {"color": "#1d4ed8", "weight": 1.8, "fillColor": "#1d4ed8", "fillOpacity": 0.06},
        )
        _add_auxiliary_layer(
            mapa,
            camadas_auxiliares.get("assentamento_reconhecimento"),
            visible_bbox,
            "Assentamento Reconhecimento",
            {"color": "#2563eb", "weight": 1.8, "fillColor": "#2563eb", "fillOpacity": 0.06},
        )
        _add_auxiliary_layer(
            mapa,
            camadas_auxiliares.get("snci"),
            visible_bbox,
            "Imovel certificado SNCI Brasil",
            {"color": "#0f766e", "weight": 1.8, "fillColor": "#0f766e", "fillOpacity": 0.06},
        )
        _add_auxiliary_layer(
            mapa,
            camadas_auxiliares.get("sigefl"),
            visible_bbox,
            "Sigefl",
            {"color": "#0891b2", "weight": 1.8, "fillColor": "#0891b2", "fillOpacity": 0.06},
        )

    if layer_request and any(layer is not None and not layer.empty for layer in camadas_auxiliares.values()):
        _ensure_layer_control(mapa)

    map_state = st_folium(
        mapa,
        width=None,
        height=520,
        key="fund_map",
        returned_objects=["bounds", "last_object_clicked_popup", "last_object_clicked_tooltip"],
    )

    return mapa, layer_warnings, map_state
