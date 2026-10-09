"""Carga los archivos crudos del SIES y los guarda en parquet con nombres de columna normalizados."""
import re
import unicodedata
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
RAW = RAIZ / "datos" / "raw"
INTERIM = RAIZ / "datos" / "interim"


def normalizar(col: str) -> str:
    col = unicodedata.normalize("NFKD", col.strip()).encode("ascii", "ignore").decode()
    col = re.sub(r"[^0-9a-zA-Z]+", "_", col).strip("_").lower()
    return col


def cargar_matricula() -> pd.DataFrame:
    df = pd.read_csv(
        RAW / "matriculados" / "Matricula_2007_2026_WEB_10_07_2026.csv",
        sep=";", encoding="latin-1", low_memory=False,
    )
    df.columns = [normalizar(c) for c in df.columns]
    df["anio"] = df["ano"].str.extract(r"(\d{4})").astype(int)
    return df.drop(columns="ano")


def cargar_titulados() -> pd.DataFrame:
    df = pd.read_excel(RAW / "titulados" / "TITULADO_2007-2025_web_27_05_2026_E-1.xlsx")
    df.columns = [normalizar(c) for c in df.columns]
    df["anio"] = df["ano"].astype(str).str.extract(r"(\d{4})").astype(int)
    return df.drop(columns="ano")


if __name__ == "__main__":
    INTERIM.mkdir(parents=True, exist_ok=True)
    for nombre, f in [("matricula", cargar_matricula), ("titulados", cargar_titulados)]:
        df = f()
        df.to_parquet(INTERIM / f"{nombre}.parquet", index=False)
        print(nombre, df.shape)
        print(df.dtypes.to_string())
