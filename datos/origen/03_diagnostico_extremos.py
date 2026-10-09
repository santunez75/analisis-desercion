"""Diagnostico de los programas que quedan en los extremos de la escala.

El abandono se acota en [0, 1] al construirse, de modo que conviene saber si
esos extremos reflejan el fenomeno o un desajuste entre las dos bases. Para
cada programa con abandono exactamente 0 o 1 se registra el ultimo anio en
que aparecio en matricula, el anio de egreso esperado de su ultima cohorte y
las titulaciones que acumulo en cualquier anio.

Produce datos/diagnostico_extremos.csv, que el cuaderno lee para reproducir
la comprobacion sin necesitar las bases completas del SIES.
"""
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]      # proyecto-abandono
INTERIM = RAIZ / "datos" / "interim"
RESULTADOS = RAIZ / "resultados"
SALIDA = Path(__file__).resolve().parents[1] / "diagnostico_extremos.csv"


def diagnostico() -> pd.DataFrame:
    base = pd.read_csv(RESULTADOS / "base_programas.csv")
    cohortes = pd.read_parquet(INTERIM / "cohortes.parquet")
    matricula = pd.read_parquet(INTERIM / "matricula.parquet",
                                columns=["anio", "codigo_carrera"])
    titulados = pd.read_parquet(INTERIM / "titulados.parquet",
                                columns=["codigo_programa", "total_titulaciones"])

    extremos = base.loc[base.abandono.isin([0, 1]),
                        ["codigo_carrera", "abandono", "ingreso", "titulados"]].copy()

    ultimo_anio = matricula.groupby("codigo_carrera")["anio"].max()
    egreso_esperado = cohortes.groupby("codigo_carrera")["anio_tit"].max()
    acumuladas = titulados.groupby("codigo_programa")["total_titulaciones"].sum()

    extremos["ultimo_anio_matricula"] = extremos.codigo_carrera.map(ultimo_anio).astype("Int64")
    extremos["anio_egreso_esperado"] = extremos.codigo_carrera.map(egreso_esperado).astype("Int64")
    # Si el programa seguia matriculando despues del egreso esperado, el cero no
    # puede atribuirse a un cierre: apunta a un desfase de la ventana observada.
    extremos["seguia_matriculando"] = (extremos.ultimo_anio_matricula
                                       > extremos.anio_egreso_esperado)
    extremos["titulaciones_en_cualquier_anio"] = (
        extremos.codigo_carrera.map(acumuladas).fillna(0).astype(int))
    return extremos


if __name__ == "__main__":
    e = diagnostico()
    e.to_csv(SALIDA, index=False, encoding="utf-8-sig")
    print(f"{SALIDA.name}: {len(e)} programas")
    for valor, etiqueta in ((1.0, "abandono = 1"), (0.0, "abandono = 0")):
        g = e[e.abandono == valor]
        print(f"\n{etiqueta}: {len(g)} programas")
        print(f"  seguian matriculando tras el egreso esperado: "
              f"{int(g.seguia_matriculando.sum())} ({100*g.seguia_matriculando.mean():.0f} %)")
        print(f"  con titulaciones en algun anio: "
              f"{int((g.titulaciones_en_cualquier_anio > 0).sum())}")
