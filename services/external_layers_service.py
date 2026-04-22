from __future__ import annotations

import json
import os
import subprocess
import unicodedata
import xml.etree.ElementTree as ET
from urllib.parse import urlencode

import folium
import geopandas as gpd
import pandas as pd
import requests
import streamlit as st
from shapely.geometry import box


INCRA_OGC_BASE = "https://acervofundiario.incra.gov.br/i3geo/ogc.php"
CAR_WFS_BASE_URL = "https://geoserver.car.gov.br/geoserver/sicar/wfs"
ICMBIO_OWS_BASE_URL = "https://geoservicos.inde.gov.br/geoserver/ICMBio/ows"
MMA_OWS_BASE_URL = "http://mapas.mma.gov.br/cgi-bin/mapserv?map=/opt/www/html/webservices/ucs.map"
FUNAI_OWS_CANDIDATES = [
    "http://proindio.funai.gov.br:8080/geoserver/ows",
    "https://geoserver.funai.gov.br/geoserver/Funai/ows",
]

INCRA_THEME_CANDIDATES = {
    "sigef": ["certificada_sigef_publico_{uf}"],
    "assentamentos": ["assentamentos_{uf}", "assentamento_{uf}"],
    "quilombolas": ["quilombolas_{uf}", "quilombola_{uf}"],
}

SERVICE_DEFINITIONS = {
    "sigef": {"label": "SIGEF/CIGEF", "kind": "incra", "keywords": ["sigef", "cert", "public"]},
    "assentamentos": {"label": "Assentamentos", "kind": "incra", "keywords": ["assentamento"]},
    "quilombolas": {"label": "Territorios Quilombolas", "kind": "incra", "keywords": ["quilombola"]},
    "uc": {
        "label": "Unidades de Conservacao",
        "kind": "icmbio",
        "keywords": ["limite", "ucs", "federais"],
        "exact_name": "ICMBio:limiteucsfederais_a",
    },
    "ti": {"label": "Terras Indigenas", "kind": "funai", "keywords": ["terra", "indigena"]},
    "car": {"label": "CAR", "kind": "car", "keywords": ["sicar", "imoveis"]},
}

LAYER_STYLES = {
    "sigef": {"color": "#59c3ff", "weight": 1.6, "fillColor": "#59c3ff", "fillOpacity": 0.05},
    "assentamentos": {"color": "#1d4ed8", "weight": 2.0, "fillColor": "#2563eb", "fillOpacity": 0.14},
    "quilombolas": {"color": "#8b5cf6", "weight": 1.8, "fillColor": "#8b5cf6", "fillOpacity": 0.08},
    "uc": {"color": "#22c55e", "weight": 1.6, "fillColor": "#22c55e", "fillOpacity": 0.07},
    "ti": {"color": "#f97316", "weight": 1.7, "fillColor": "#f97316", "fillOpacity": 0.07},
    "car": {"color": "#f4c542", "weight": 1.4, "fillColor": "#f4c542", "fillOpacity": 0.08},
}


def build_sigef_url(uf: str) -> str:
    suffix = str(uf or "").strip().lower()
    if not suffix:
        raise ValueError("UF invalida para montar a URL do SIGEF.")
    return f"{INCRA_OGC_BASE}?tema=certificada_sigef_publico_{suffix}"


def _normalize(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return "".join(ch for ch in text.strip().lower() if ch.isalnum() or ch == "_")


def get_map_bbox(map_state: dict | None) -> tuple[float, float, float, float] | None:
    if not map_state:
        return None
    bounds = map_state.get("bounds") if isinstance(map_state, dict) else None
    if not isinstance(bounds, dict):
        return None
    sw = bounds.get("_southWest") or {}
    ne = bounds.get("_northEast") or {}
    try:
        xmin = float(sw["lng"])
        ymin = float(sw["lat"])
        xmax = float(ne["lng"])
        ymax = float(ne["lat"])
    except Exception:
        return None
    return (xmin, ymin, xmax, ymax)


def _bbox_from_gdf(gdf: gpd.GeoDataFrame) -> tuple[float, float, float, float] | None:
    if gdf.empty:
        return None
    bounds = gdf.total_bounds
    if pd.isna(bounds).any():
        return None
    minx, miny, maxx, maxy = [float(value) for value in bounds]
    return (minx, miny, maxx, maxy)


def _buffer_geometry(gdf: gpd.GeoDataFrame, distance_meters: float = 5000) -> gpd.GeoDataFrame | None:
    if gdf.empty:
        return None
    try:
        metric = gdf.to_crs(3857)
        buffered = metric.geometry.buffer(distance_meters)
        buffered_gdf = gpd.GeoDataFrame(geometry=buffered, crs=3857).to_crs(4326)
        return buffered_gdf
    except Exception:
        return None


def _query_bbox_from_filtered_gdf(gdf: gpd.GeoDataFrame, distance_meters: float = 5000) -> tuple[float, float, float, float] | None:
    buffered = _buffer_geometry(gdf, distance_meters=distance_meters)
    if buffered is None or buffered.empty:
        return _bbox_from_gdf(gdf)
    return _bbox_from_gdf(buffered)


def _build_query_area(gdf: gpd.GeoDataFrame, distance_meters: float = 5000):
    buffered = _buffer_geometry(gdf, distance_meters=distance_meters)
    if buffered is None or buffered.empty:
        return None
    return buffered.unary_union


def _bbox_to_string(bbox: tuple[float, float, float, float], crs: str = "EPSG:4326") -> str:
    xmin, ymin, xmax, ymax = bbox
    return f"{xmin},{ymin},{xmax},{ymax},{crs}"


def _extract_entries(xml_text: str, tag: str) -> list[dict[str, str]]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    entries: list[dict[str, str]] = []
    for item in root.findall(f".//{{*}}{tag}"):
        name = item.findtext("{*}Name", default="").strip()
        title = item.findtext("{*}Title", default="").strip()
        if name:
            entries.append({"name": name, "title": title or name})
    return entries


def _friendly_label(field_name: str) -> str:
    pieces = str(field_name or "").replace(".", "_").split("_")
    words = [piece for piece in pieces if piece]
    if not words:
        return str(field_name or "")
    return " ".join(word.capitalize() for word in words)


def build_popup_from_properties(properties: dict) -> str:
    rows = []
    for key, value in properties.items():
        if value in (None, "", []):
            continue
        rows.append(
            f"<tr><th style='text-align:left;padding-right:8px'>{_friendly_label(key)}</th>"
            f"<td>{value}</td></tr>"
        )
    if not rows:
        return "<div>Sem atributos disponiveis.</div>"
    return f"<table>{''.join(rows)}</table>"


def _fetch_text(url: str, timeout: int = 40, verify: bool = True) -> str:
    response = requests.get(url, timeout=timeout, verify=verify)
    response.raise_for_status()
    return response.text


def _fetch_text_with_fallback(url: str, timeout: int = 40, verify: bool = True) -> str:
    try:
        return _fetch_text(url, timeout=timeout, verify=verify)
    except requests.exceptions.SSLError:
        if os.name != "nt":
            raise
        ps = (
            "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; "
            f"$r = Invoke-WebRequest -Uri '{url}' -UseBasicParsing -TimeoutSec {timeout}; "
            "$r.Content"
        )
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            text=True,
            timeout=timeout + 20,
            check=True,
        )
        return completed.stdout


def _fetch_json_with_fallback(url: str, params: dict[str, object], timeout: int = 60, verify: bool = True) -> dict:
    try:
        response = requests.get(url, params=params, timeout=timeout, verify=verify)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.SSLError:
        if os.name != "nt":
            raise
        full_url = f"{url}?{urlencode(params, doseq=True)}"
        ps = (
            "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; "
            f"$r = Invoke-WebRequest -Uri '{full_url}' -UseBasicParsing -TimeoutSec {timeout}; "
            "$r.Content"
        )
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            text=True,
            timeout=timeout + 20,
            check=True,
        )
        return json.loads(completed.stdout)


def _pick_layer(entries: list[dict[str, str]], keywords: list[str]) -> dict[str, str]:
    scored: list[tuple[int, dict[str, str]]] = []
    tokens = [_normalize(keyword) for keyword in keywords]
    for entry in entries:
        haystack = _normalize(f"{entry['name']} {entry['title']}")
        score = sum(1 for token in tokens if token and token in haystack)
        if score:
            scored.append((score, entry))
    if not scored:
        fallback = next((entry for entry in entries if ":" in entry["name"] or entry["name"]), None)
        if fallback:
            return fallback
        raise RuntimeError("Nenhuma camada compativel encontrada no GetCapabilities.")
    scored.sort(key=lambda item: (item[0], len(item[1]["name"])), reverse=True)
    return scored[0][1]


def _service_base_urls(service_key: str, uf: str | None = None) -> list[tuple[str, str]]:
    if service_key in {"sigef", "assentamentos", "quilombolas"}:
        if not uf:
            raise ValueError("UF e obrigatoria para os servicos do INCRA.")
        themes = INCRA_THEME_CANDIDATES[service_key]
        return [("incra", f"{INCRA_OGC_BASE}?tema={theme.format(uf=uf.lower())}") for theme in themes]
    if service_key == "uc":
        return [("icmbio", ICMBIO_OWS_BASE_URL), ("mma", MMA_OWS_BASE_URL)]
    if service_key == "ti":
        return [("funai", item) for item in FUNAI_OWS_CANDIDATES]
    if service_key == "car":
        return [("car", CAR_WFS_BASE_URL)]
    raise ValueError(f"Servico desconhecido: {service_key}")


@st.cache_data(show_spinner=False, ttl=86400)
def discover_service_layer(service_key: str, uf: str | None = None) -> dict[str, str]:
    definition = SERVICE_DEFINITIONS[service_key]
    keywords = definition["keywords"]
    last_error: Exception | None = None

    for provider, base_url in _service_base_urls(service_key, uf=uf):
        exact_name = str(definition.get("exact_name") or "")
        if service_key == "car" and uf:
            exact_name = f"sicar:sicar_imoveis_{uf.lower()}"
        try:
            wfs_cap = _fetch_text_with_fallback(
                f"{base_url}{'&' if '?' in base_url else '?'}SERVICE=WFS&REQUEST=GetCapabilities",
                verify=False if provider in {"mma", "funai", "icmbio"} else True,
            )
            entries = _extract_entries(wfs_cap, "FeatureType")
            if exact_name:
                feature = next((item for item in entries if _normalize(item["name"]) == _normalize(exact_name)), None)
                if feature is None:
                    feature = _pick_layer(entries, keywords + ([uf] if uf else []))
            else:
                feature = _pick_layer(entries, keywords + ([uf] if uf else []))
            return {
                "service_type": "WFS",
                "service_url": base_url,
                "layer_name": feature["name"],
                "layer_title": feature["title"],
                "provider": provider,
            }
        except Exception as exc:  # pragma: no cover
            last_error = exc
        try:
            wms_cap = _fetch_text_with_fallback(
                f"{base_url}{'&' if '?' in base_url else '?'}SERVICE=WMS&REQUEST=GetCapabilities",
                verify=False if provider in {"mma", "funai", "icmbio"} else True,
            )
            entries = _extract_entries(wms_cap, "Layer")
            if exact_name:
                layer = next((item for item in entries if _normalize(item["name"]) == _normalize(exact_name)), None)
                if layer is None:
                    layer = _pick_layer(entries, keywords + ([uf] if uf else []))
            else:
                layer = _pick_layer(entries, keywords + ([uf] if uf else []))
            return {
                "service_type": "WMS",
                "service_url": base_url,
                "layer_name": layer["name"],
                "layer_title": layer["title"],
                "provider": provider,
            }
        except Exception as exc:  # pragma: no cover
            last_error = exc
    raise RuntimeError(f"Nao foi possivel descobrir a camada {definition['label']}. {last_error}")


def load_wfs_features_by_bbox(
    service_url: str,
    typename: str,
    bbox: tuple[float, float, float, float],
    crs: str = "EPSG:4326",
    count: int = 1000,
) -> dict:
    all_features: list[dict] = []
    start_index = 0
    max_pages = 12

    for _ in range(max_pages):
        params = {
            "service": "WFS",
            "request": "GetFeature",
            "outputFormat": "application/json",
            "srsName": crs,
            "bbox": _bbox_to_string(bbox, crs=crs),
            "count": count,
            "startIndex": start_index,
        }
        if "geoserver.car.gov.br" in service_url or "geoservicos.inde.gov.br" in service_url:
            params["version"] = "2.0.0"
            params["typeNames"] = typename
        else:
            params["version"] = "1.0.0"
            params["typeName"] = typename
            params["maxFeatures"] = count

        payload = _fetch_json_with_fallback(
            service_url,
            params=params,
            timeout=60,
            verify=not service_url.startswith("http://"),
        )
        features = payload.get("features") or []
        all_features.extend(features)
        if len(features) < count:
            break
        start_index += count

    return {"type": "FeatureCollection", "features": all_features}


def load_layer_by_bbox(service_url: str, layer_name: str, bbox: tuple[float, float, float, float], crs: str = "EPSG:4326"):
    return load_wfs_features_by_bbox(service_url, layer_name, bbox, crs=crs)


def get_feature_info_wms(
    service_url: str,
    layer_name: str,
    click_x: int,
    click_y: int,
    bbox: tuple[float, float, float, float],
    width: int,
    height: int,
) -> str:
    params = {
        "service": "WMS",
        "request": "GetFeatureInfo",
        "layers": layer_name,
        "query_layers": layer_name,
        "bbox": ",".join(str(value) for value in bbox),
        "width": width,
        "height": height,
        "srs": "EPSG:4326",
        "x": click_x,
        "y": click_y,
        "info_format": "text/html",
        "version": "1.1.1",
    }
    response = requests.get(service_url, params=params, timeout=40)
    response.raise_for_status()
    return response.text


def _property_fields_from_geojson(geojson: dict) -> list[str]:
    features = geojson.get("features") or []
    if not features:
        return []
    properties = (features[0] or {}).get("properties") or {}
    preferred = []
    for key in properties.keys():
        normalized = _normalize(key)
        if any(token in normalized for token in ["nome", "id", "cod", "car", "status", "area", "uf", "situ"]):
            preferred.append(key)
    ordered = preferred + [key for key in properties.keys() if key not in preferred]
    return ordered[:8]


def _build_popup(geojson: dict) -> folium.GeoJsonPopup | None:
    fields = _property_fields_from_geojson(geojson)
    if not fields:
        return None
    aliases = [f"{_friendly_label(field)}: " for field in fields]
    return folium.GeoJsonPopup(fields=fields, aliases=aliases, labels=True, sticky=False)


def _add_vector_layer(
    map_obj: folium.Map,
    service_key: str,
    label: str,
    geojson: dict,
) -> None:
    style = LAYER_STYLES[service_key]
    popup = _build_popup(geojson)
    folium.GeoJson(
        geojson,
        name=label,
        style_function=lambda _: style,
        highlight_function=lambda _: {
            "color": style["color"],
            "weight": style["weight"] + 0.8,
            "fillColor": style["fillColor"],
            "fillOpacity": min(style["fillOpacity"] + 0.08, 0.22),
        },
        popup=popup,
    ).add_to(map_obj)


def _clip_geojson_to_query_area(geojson: dict, query_area) -> dict:
    if query_area is None:
        return geojson
    try:
        gdf = gpd.GeoDataFrame.from_features(geojson.get("features") or [], crs="EPSG:4326")
        if gdf.empty:
            return geojson
        clipped = gdf[gdf.intersects(query_area)].copy()
        if clipped.empty:
            return {"type": "FeatureCollection", "features": []}
        return json.loads(clipped.to_json())
    except Exception:
        return geojson


def _add_wms_layer(map_obj: folium.Map, label: str, discovery: dict[str, str], opacity: float = 0.55) -> None:
    folium.WmsTileLayer(
        url=discovery["service_url"],
        name=label,
        layers=discovery["layer_name"],
        fmt="image/png",
        transparent=True,
        version="1.1.1",
        overlay=True,
        control=True,
        show=True,
        opacity=opacity,
        attr=label,
    ).add_to(map_obj)


def resolve_single_uf(gdf: gpd.GeoDataFrame) -> str | None:
    for column in gdf.columns:
        if _normalize(column) != "uf":
            continue
        values = sorted({str(value).strip().lower() for value in gdf[column].dropna().tolist() if str(value).strip()})
        if len(values) == 1:
            return values[0]
    return None


def add_external_layers(
    map_obj: folium.Map,
    filtered_gdf: gpd.GeoDataFrame,
    toggles: dict[str, bool],
    visible_bbox: tuple[float, float, float, float] | None = None,
) -> list[str]:
    warnings: list[str] = []
    uf = resolve_single_uf(filtered_gdf)
    if visible_bbox:
        bbox = visible_bbox
        try:
            query_area = box(*visible_bbox)
        except Exception:
            query_area = _build_query_area(filtered_gdf, distance_meters=5000)
    else:
        query_area = _build_query_area(filtered_gdf, distance_meters=5000)
        bbox = _query_bbox_from_filtered_gdf(filtered_gdf, distance_meters=5000)
    if not bbox:
        return warnings

    toggle_to_service = {
        "show_sigef": "sigef",
        "show_car": "car",
        "show_assentamentos": "assentamentos",
        "show_quilombolas": "quilombolas",
        "show_uc": "uc",
        "show_ti": "ti",
    }

    for toggle_key, service_key in toggle_to_service.items():
        if not toggles.get(toggle_key):
            continue
        if service_key in {"sigef", "assentamentos", "quilombolas", "car"} and not uf:
            warnings.append(f"{SERVICE_DEFINITIONS[service_key]['label']} exige UF valida no subconjunto filtrado.")
            continue
        try:
            discovery = discover_service_layer(service_key, uf=uf)
            if discovery["service_type"] == "WFS":
                geojson = load_wfs_features_by_bbox(discovery["service_url"], discovery["layer_name"], bbox)
                geojson = _clip_geojson_to_query_area(geojson, query_area)
                _add_vector_layer(map_obj, service_key, SERVICE_DEFINITIONS[service_key]["label"], geojson)
            else:
                _add_wms_layer(map_obj, SERVICE_DEFINITIONS[service_key]["label"], discovery, opacity=0.58)
        except Exception as exc:
            warnings.append(f"{SERVICE_DEFINITIONS[service_key]['label']}: {exc}")

    if any(toggles.values()):
        folium.LayerControl(collapsed=False).add_to(map_obj)
    return warnings
