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
ONEDRIVE_ROOT_DIR = Path(os.getenv("AVANTE_ONEDRIVE_ROOT", "C:/Users/marco/OneDrive"))
SHAPEFILE_QUERY = os.getenv("AVANTE_SHAPEFILE_QUERY", LOCAL_SHAPEFILE_PATH.stem).strip()
LOCAL_INDEX_PATH = Path(
    os.getenv("AVANTE_LOCAL_INDEX", "C:/Users/marco/OneDrive/00_MAP_DOC/RRDOCS/index_arquivos.csv")
)
LOCAL_DOCS_DIR = Path(os.getenv("AVANTE_LOCAL_DOCS_DIR", BASE_DIR / "data" / "RRDocs"))

SHAPEFILE_URL = os.getenv("AVANTE_SHAPEFILE_URL", "").strip()
INDEX_URL = os.getenv(
    "AVANTE_INDEX_URL",
    "https://1drv.ms/x/c/8b88b81c064543d3/IQD7BgHZu2HoSJgnrFbCqxWiAenPGpFmOK8wFImKqmZqbnE?e=w9Udqt",
).strip()
DOCS_BASE_URL = os.getenv(
    "AVANTE_DOCS_BASE_URL",
    "https://1drv.ms/f/c/8b88b81c064543d3/IgDTQ0UGHLiIIICLUV0IAAAAAeYZ-IYCKnnjmVsmhN1PnOA?e=aUtg9t",
).strip()
REMOTE_DATA_FOLDER_URL = os.getenv(
    "AVANTE_REMOTE_DATA_URL",
    "https://1drv.ms/f/c/8b88b81c064543d3/IgBGEAmSs4rFSKtxZck7F0iDAbjN8qgzzI2KnfHX6MyE3aU?e=ho0Y2s",
).strip()

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
