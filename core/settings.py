from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

APP_TITLE = "Avant Fundiario"
APP_VERSION = "v1"
APP_ICON = "map"
LOGO_PATH = str(BASE_DIR / "assets" / "Logo.png")
AUTH_CONFIG_PATH = str(BASE_DIR / "config.yaml")

LOCAL_SHAPEFILE_PATH = Path(os.getenv("AVANTE_LOCAL_SHAPEFILE", BASE_DIR / "data" / "Geo.shp"))
SHAPEFILE_QUERY = os.getenv("AVANTE_SHAPEFILE_QUERY", LOCAL_SHAPEFILE_PATH.stem).strip()
LOCAL_INDEX_PATH = Path(
    os.getenv("AVANTE_LOCAL_INDEX", r"\\172.28.10.1\VALOR_FLORESTAL$\CARTOGRAFIA\FUNDIARIO\RRDOCS\index_arquivos.csv")
)
LOCAL_DOCS_DIR = Path(os.getenv("AVANTE_LOCAL_DOCS_DIR", r"\\172.28.10.1\VALOR_FLORESTAL$\CARTOGRAFIA\FUNDIARIO\RRDOCS"))
LOCAL_DOCS_FALLBACK_DIR = Path(os.getenv("AVANTE_FALLBACK_DOCS_DIR", "C:/01"))

SHAPEFILE_URL = os.getenv("AVANTE_SHAPEFILE_URL", "").strip()
INDEX_URL = os.getenv(
    "AVANTE_INDEX_URL",
    "",
).strip()
DOCS_BASE_URL = os.getenv(
    "AVANTE_DOCS_BASE_URL",
    "",
).strip()
GCS_BUCKET_NAME = os.getenv("AVANTE_GCS_BUCKET", "storefundiario").strip()
GCS_INDEX_BLOB = os.getenv("AVANTE_GCS_INDEX_BLOB", "data/index_arquivos.csv").strip()
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
