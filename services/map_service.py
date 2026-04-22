from __future__ import annotations

import folium
import geopandas as gpd
import pandas as pd

from services.external_layers_service import add_external_layers


BRAZIL_CENTER = [-15.793889, -47.882778]
ESRI_SATELLITE_URL = (
    "https://server.arcgisonline.com/ArcGIS/rest/services/"
    "World_Imagery/MapServer/tile/{z}/{y}/{x}"
)
ESRI_ATTR = "Esri World Imagery"


POPUP_FIELDS = [
    ("BLOCO", "bloco"),
    ("Fazenda", "fazenda"),
    ("MATRICULA", "matricula"),
    ("Area", "area"),
    ("CCIR", "ccir"),
    ("ITR", "itr"),
    ("CAR1", "car1"),
    ("CAR_ESTADU", "car_estadu"),
    ("GEO", "geo"),
]


def build_base_map(center: list[float] | tuple[float, float] | None = None, zoom_start: int = 4) -> folium.Map:
    map_obj = folium.Map(
        location=center or BRAZIL_CENTER,
        zoom_start=zoom_start,
        control_scale=True,
        tiles=None,
        prefer_canvas=True,
    )
    folium.TileLayer(
        tiles=ESRI_SATELLITE_URL,
        attr=ESRI_ATTR,
        name="ESRI Satellite",
        overlay=False,
        control=False,
    ).add_to(map_obj)
    return map_obj


def _fit_bounds(map_obj: folium.Map, gdf: gpd.GeoDataFrame) -> None:
    bounds = gdf.total_bounds
    minx, miny, maxx, maxy = bounds
    if pd.isna(bounds).any():
        return
    if minx == maxx and miny == maxy:
        map_obj.location = [miny, minx]
        map_obj.zoom_start = 14
        return
    map_obj.fit_bounds([[miny, minx], [maxy, maxx]])


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


def _build_map_gdf(gdf: gpd.GeoDataFrame, resolved_fields: dict[str, str]) -> gpd.GeoDataFrame:
    map_gdf = _json_safe_gdf(gdf)
    for label, field_key in POPUP_FIELDS:
        source = resolved_fields.get(field_key)
        if source and source in map_gdf.columns:
            map_gdf[label] = map_gdf[source]
        elif label not in map_gdf.columns:
            map_gdf[label] = ""
    return map_gdf


def render_fund_map(
    gdf: gpd.GeoDataFrame,
    resolved_fields: dict[str, str],
    show_primary: bool = True,
    external_toggles: dict[str, bool] | None = None,
    visible_bbox: tuple[float, float, float, float] | None = None,
) -> tuple[folium.Map, list[str]]:
    external_toggles = external_toggles or {}
    warnings: list[str] = []
    if gdf.empty:
        map_obj = build_base_map()
        warnings.extend(add_external_layers(map_obj, gdf, external_toggles, visible_bbox=visible_bbox))
        return map_obj, warnings

    map_gdf = _build_map_gdf(gdf, resolved_fields)
    map_obj = build_base_map()
    popup = folium.GeoJsonPopup(
        fields=[item[0] for item in POPUP_FIELDS],
        aliases=[f"{item[0]}: " for item in POPUP_FIELDS],
        labels=True,
        sticky=False,
    )

    if show_primary:
        folium.GeoJson(
            map_gdf,
            name="Matrícula",
            style_function=lambda _: {
                "color": "#ff0000",
                "weight": 2,
                "fillColor": "#ff0000",
                "fillOpacity": 0.12,
            },
            highlight_function=lambda _: {
                "color": "#ff4d4d",
                "weight": 3,
                "fillOpacity": 0.18,
            },
            popup=popup,
        ).add_to(map_obj)

    _fit_bounds(map_obj, map_gdf)
    warnings.extend(add_external_layers(map_obj, map_gdf, external_toggles, visible_bbox=visible_bbox))
    return map_obj, warnings
