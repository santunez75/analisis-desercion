"""Tasa de abandono aparente por programa e institución.

Cada titulado del año y se compara con el ingreso a primer año de la cohorte y - L,
donde L = duración formal de la carrera en años (semestres / 2, redondeado hacia arriba).
Sumando sobre varios años se obtiene una tasa de titulación aparente:

    titulación = Σ titulados(y) / Σ ingreso(y - L)      abandono = 1 - titulación

Es una aproximación con datos agregados: quien se cambia de carrera o institución
cuenta como abandono, y quien se titula muy tarde puede quedar fuera de la ventana.
"""
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
INTERIM = RAIZ / "datos" / "interim"
RESULTADOS = RAIZ / "resultados"

TIPOS_CARRERA = ["Técnico de Nivel Superior", "Profesional Con Licenciatura", "Profesional Sin Licenciatura"]
ANIO_TIT_MIN = 2010  # antes de 2010 menos del 90 % de los titulados cruza con matrícula
ANIO_TIT_MAX = 2025
INGRESO_MIN = 100  # ingreso acumulado mínimo para reportar una tasa


def filtrar_pregrado(df: pd.DataFrame) -> pd.DataFrame:
    return df[
        (df["nivel_global"] == "Pregrado")
        & (df["tipo_de_plan_de_la_carrera"] == "Plan Regular")
        & (df["carrera_clasificacion_nivel_1"].isin(TIPOS_CARRERA))
    ]


def cohortes() -> pd.DataFrame:
    m = filtrar_pregrado(pd.read_parquet(INTERIM / "matricula.parquet"))
    t = filtrar_pregrado(pd.read_parquet(INTERIM / "titulados.parquet"))

    ing = m[["anio", "codigo_carrera", "total_matricula_primer_ano", "duracion_estudio_carrera"]].copy()
    ing["ingreso"] = ing["total_matricula_primer_ano"].fillna(0)
    ing["lag"] = np.ceil(ing["duracion_estudio_carrera"] / 2)
    ing = ing.dropna(subset=["lag"])
    ing["anio_tit"] = ing["anio"] + ing["lag"].astype(int)
    ing = ing[ing["anio_tit"].between(ANIO_TIT_MIN, ANIO_TIT_MAX)].drop(columns=["total_matricula_primer_ano", "duracion_estudio_carrera"])

    tit = t.groupby(["codigo_programa", "anio"], as_index=False)["total_titulaciones"].sum()
    tit = tit.rename(columns={"codigo_programa": "codigo_carrera", "anio": "anio_tit", "total_titulaciones": "titulados"})

    # Atributos del programa: los del último año en que aparece en matrícula
    attrs = (
        m.sort_values("anio")
        .groupby("codigo_carrera")
        .last()[[
            "codigo_de_institucion", "nombre_institucion", "clasificacion_institucion_nivel_3",
            "acreditacion_institucional", "region", "nombre_sede", "nombre_carrera",
            "area_del_conocimiento", "carrera_clasificacion_nivel_1", "modalidad", "jornada",
            "duracion_estudio_carrera", "acreditacion_carrera",
        ]]
    )

    c = ing.merge(tit, on=["codigo_carrera", "anio_tit"], how="left").fillna({"titulados": 0})
    return c.merge(attrs, left_on="codigo_carrera", right_index=True, how="left")


def tasa(df: pd.DataFrame, por: list[str]) -> pd.DataFrame:
    g = df.groupby(por, as_index=False).agg(
        ingreso=("ingreso", "sum"), titulados=("titulados", "sum"), programas=("codigo_carrera", "nunique")
    )
    g = g[g["ingreso"] >= INGRESO_MIN]
    g["titulacion_aparente"] = (g["titulados"] / g["ingreso"]).clip(upper=1)
    g["abandono_aparente"] = 1 - g["titulacion_aparente"]
    return g.sort_values("abandono_aparente", ascending=False)


if __name__ == "__main__":
    RESULTADOS.mkdir(exist_ok=True)
    c = cohortes()
    c.to_parquet(INTERIM / "cohortes.parquet", index=False)

    salidas = {
        "por_programa": ["codigo_carrera", "nombre_institucion", "nombre_carrera", "nombre_sede", "jornada"],
        "por_institucion": ["nombre_institucion", "clasificacion_institucion_nivel_3"],
        "por_tipo_institucion": ["clasificacion_institucion_nivel_3"],
        "por_tipo_carrera": ["carrera_clasificacion_nivel_1"],
        "por_area": ["area_del_conocimiento"],
        "por_jornada": ["jornada"],
        "por_modalidad": ["modalidad"],
        "por_acreditacion_inst": ["acreditacion_institucional"],
        "por_region": ["region"],
        "por_cohorte_y_tipo_inst": ["anio", "clasificacion_institucion_nivel_3"],
    }
    for nombre, por in salidas.items():
        r = tasa(c, por)
        r.to_csv(RESULTADOS / f"abandono_{nombre}.csv", index=False, encoding="utf-8-sig")

    total = tasa(c.assign(todo="total"), ["todo"])
    print("Sistema completo:\n", total.to_string(index=False), "\n")
    for nombre in ["por_tipo_institucion", "por_tipo_carrera", "por_jornada", "por_modalidad", "por_acreditacion_inst", "por_area"]:
        print(pd.read_csv(RESULTADOS / f"abandono_{nombre}.csv").round(3).to_string(index=False), "\n")
