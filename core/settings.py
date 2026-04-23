from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

APP_TITLE = "Avant Fundiario"
APP_VERSION = "v1"
APP_ICON = "map"
LOGO_PATH = str(BASE_DIR / "assets" / "Logo.png")
AUTH_CONFIG_PATH = str(BASE_DIR / "config.yaml")

LOCAL_SHAPEFILE_PATH = DATA_DIR / "Geo.shp"
SHAPEFILE_QUERY = LOCAL_SHAPEFILE_PATH.stem
LOCAL_INDEX_PATH = DATA_DIR / "index_arquivos.csv"
LOCAL_DOCS_FALLBACK_DIR = Path("C:/01")

GCS_BUCKET_NAME = os.getenv("AVANTE_GCS_BUCKET", "storefundiario").strip()
GCS_DOCS_PREFIX = os.getenv("AVANTE_GCS_DOCS_PREFIX", "").strip().strip("/")

DOCUMENT_COLUMNS = ("MATRICULA", "CCIR", "ITR", "CAR1", "GEO", "CAR_ESTADUAL", "Outros")

DOCUMENT_COLUMN_ALIASES = {
    "MATRICULA": ["MATRICULA", "MATRIC", "MATR", "REGISTRO", "NUMERO_MATRICULA"],
    "CCIR": ["CCIR"],
    "ITR": ["ITR", "NIRF"],
    "CAR1": ["CAR1", "CAR", "K1"],
    "GEO": ["GEO", "SIGEF", "GEOREF", "GEOREFERENCIAMENTO"],
    "CAR_ESTADUAL": ["CAR_ESTADU", "CAR_ESTADUAL", "CEFIR", "SICAR_UF"],
    "Outros": ["OUTROS", "OBSERVACAO", "OBSERVACOES", "DOCUMENTOS", "DOCS"],
}

DISPLAY_COLUMN_ALIASES = {
    "Empresa": ["EMPRESA", "EMPRESA_NOME"],
    "BLOCO": ["BLOCO", "TALHAO", "QUADRA"],
    "Fazenda": ["FAZENDA", "PROPRIEDAD", "PROPRIEDADE"],
    "MATRICULA": ["MATRICULA", "MATRIC", "MATR", "REGISTRO", "NUMERO_MATRICULA"],
    "Area": ["AREA", "AREA_HA", "AREA_TOTAL"],
    "CCIR": ["CCIR"],
    "ITR": ["ITR", "NIRF"],
    "CAR1": ["CAR1", "CAR", "K1"],
    "CAR_ESTADUAL": ["CAR_ESTADU", "CAR_ESTADUAL", "CEFIR", "SICAR_UF"],
    "GEO": ["GEO", "SIGEF", "GEOREF", "GEOREFERENCIAMENTO"],
    "Outros": ["OUTROS", "OBSERVACAO", "OBSERVACOES", "DOCUMENTOS", "DOCS"],
}

TABLE_COLUMN_ORDER = [
    "Empresa",
    "BLOCO",
    "Fazenda",
    "MATRICULA",
    "Area",
    "CCIR",
    "ITR",
    "CAR1",
    "CAR_ESTADUAL",
    "GEO",
    "Outros",
    "Municipio",
    "UF",
]
