"""Factores asociados al abandono aparente a nivel de programa.

Unidad de análisis: programa (código de carrera), con la tasa calculada en 01_tasa_abandono.py.
Las variables explicativas se promedian sobre los años de cohorte usados, ponderando por ingreso.

Dos modelos complementarios:
  1. Regresión lineal ponderada (WLS) con errores agrupados por institución: efectos
     "manteniendo lo demás constante", interpretables en puntos porcentuales.
  2. Gradient boosting + importancia por permutación: qué variables aportan más poder
     predictivo, admitiendo no linealidades e interacciones.

Ambos describen asociaciones, no causas.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.model_selection import GroupShuffleSplit

RAIZ = Path(__file__).resolve().parents[1]
INTERIM = RAIZ / "datos" / "interim"
RESULTADOS = RAIZ / "resultados"

INGRESO_MIN = 100


def a_numero(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype(str).str.replace("%", "").str.replace(",", "."), errors="coerce")


def variables_matricula() -> pd.DataFrame:
    m = pd.read_parquet(INTERIM / "matricula.parquet")
    m = m[m["nivel_global"] == "Pregrado"]
    tes = m["total_tes"].where(m["total_tes"] > 0)
    return pd.DataFrame({
        "anio": m["anio"],
        "codigo_carrera": m["codigo_carrera"],
        "pct_municipal": m["tes_municipal_servicio_local_educacion"].fillna(0) / tes,
        "pct_pagado": m["tes_particular_pagado"].fillna(0) / tes,
        "pct_tp": m["tipo_establecimiento_tp"].fillna(0) / tes,
        "pct_mujeres": m["total_matricula_mujeres"].fillna(0) / m["total_matricula"],
        "edad_promedio": a_numero(m["promedio_edad_carrera"]),
        "inst_acreditada": (m["acreditacion_institucional"] == "ACREDITADA").astype(float),
        "carrera_acreditada": (m["acreditacion_carrera"] == "ACREDITADA").astype(float),
        "matricula_total": m["total_matricula"],
    })


def base_programas() -> pd.DataFrame:
    c = pd.read_parquet(INTERIM / "cohortes.parquet")
    v = variables_matricula()
    c = c.merge(v, on=["anio", "codigo_carrera"], how="left")

    num = ["pct_municipal", "pct_pagado", "pct_tp", "pct_mujeres", "edad_promedio",
           "inst_acreditada", "carrera_acreditada", "matricula_total"]

    def promedio_ponderado(d: pd.DataFrame) -> pd.Series:
        w = d["ingreso"]
        out = {k: np.average(d[k].fillna(d[k].mean()), weights=w) if w.sum() > 0 and d[k].notna().any() else np.nan
               for k in num}
        out["ingreso"] = w.sum()
        out["titulados"] = d["titulados"].sum()
        return pd.Series(out)

    p = c.groupby("codigo_carrera").apply(promedio_ponderado, include_groups=False).reset_index()
    cat = ["nombre_institucion", "codigo_de_institucion", "clasificacion_institucion_nivel_3", "region",
           "area_del_conocimiento", "carrera_clasificacion_nivel_1", "modalidad", "jornada", "duracion_estudio_carrera"]
    p = p.merge(c.drop_duplicates("codigo_carrera")[["codigo_carrera"] + cat], on="codigo_carrera")

    # Instituciones que ya no tienen matrícula en 2026 (cerradas o en cierre)
    m26 = pd.read_parquet(INTERIM / "matricula.parquet", columns=["anio", "codigo_de_institucion"])
    vigentes = set(m26.loc[m26["anio"] == 2026, "codigo_de_institucion"])
    p["inst_cerrada"] = (~p["codigo_de_institucion"].isin(vigentes)).astype(float)

    p = p[p["ingreso"] >= INGRESO_MIN].copy()
    p["abandono"] = 1 - (p["titulados"] / p["ingreso"]).clip(upper=1)
    p["metropolitana"] = (p["region"] == "Metropolitana").astype(float)
    p["log_matricula"] = np.log(p["matricula_total"].clip(lower=1))
    p["duracion_anios"] = p["duracion_estudio_carrera"] / 2
    p["jornada"] = p["jornada"].where(p["jornada"].isin(["Diurna", "Vespertina"]), "Otra")
    for k in ["pct_municipal", "pct_pagado", "pct_tp", "pct_mujeres", "edad_promedio"]:
        p[k] = p[k].fillna(p[k].median())
    return p.dropna(subset=["duracion_anios", "log_matricula", "clasificacion_institucion_nivel_3",
                            "carrera_clasificacion_nivel_1", "modalidad", "area_del_conocimiento"])


FORMULA = (
    "abandono ~ pct_municipal + pct_pagado + pct_tp + pct_mujeres + edad_promedio"
    " + inst_acreditada + carrera_acreditada + inst_cerrada + log_matricula + duracion_anios + metropolitana"
    " + C(clasificacion_institucion_nivel_3, Treatment('Universidades Estatales CRUCH'))"
    " + C(carrera_clasificacion_nivel_1, Treatment('Profesional Con Licenciatura'))"
    " + C(jornada, Treatment('Diurna')) + C(modalidad, Treatment('Presencial'))"
    " + C(area_del_conocimiento, Treatment('Salud'))"
)


def regresion(p: pd.DataFrame) -> pd.DataFrame:
    mod = smf.wls(FORMULA, data=p, weights=p["ingreso"]).fit(
        cov_type="cluster", cov_kwds={"groups": p["codigo_de_institucion"]}
    )
    print(f"WLS: n={int(mod.nobs)} programas, R² = {mod.rsquared:.3f}\n")
    t = pd.DataFrame({"coef": mod.params, "ic_inf": mod.conf_int()[0], "ic_sup": mod.conf_int()[1], "p_valor": mod.pvalues})
    return t.drop(index="Intercept")


def boosting(p: pd.DataFrame) -> pd.DataFrame:
    num = ["pct_municipal", "pct_pagado", "pct_tp", "pct_mujeres", "edad_promedio", "inst_acreditada",
           "carrera_acreditada", "inst_cerrada", "log_matricula", "duracion_anios", "metropolitana"]
    cat = ["clasificacion_institucion_nivel_3", "carrera_clasificacion_nivel_1", "jornada", "modalidad",
           "area_del_conocimiento"]
    X = p[num + cat].copy()
    for k in cat:
        X[k] = X[k].astype("category")
    y, w = p["abandono"], p["ingreso"]

    # Separación por institución para no medir memorización de la misma universidad
    tr, te = next(GroupShuffleSplit(test_size=0.25, random_state=0).split(X, y, p["codigo_de_institucion"]))
    gbm = HistGradientBoostingRegressor(categorical_features="from_dtype", max_iter=400, learning_rate=0.05,
                                        min_samples_leaf=40, random_state=0)
    gbm.fit(X.iloc[tr], y.iloc[tr], sample_weight=w.iloc[tr])
    r2 = gbm.score(X.iloc[te], y.iloc[te], sample_weight=w.iloc[te])
    print(f"Boosting: R² en instituciones no vistas = {r2:.3f}\n")

    imp = permutation_importance(gbm, X.iloc[te], y.iloc[te], sample_weight=w.iloc[te],
                                 n_repeats=20, random_state=0)
    return pd.DataFrame({"importancia": imp.importances_mean, "desv": imp.importances_std},
                        index=X.columns).sort_values("importancia", ascending=False)


if __name__ == "__main__":
    p = base_programas()
    p.to_csv(RESULTADOS / "base_programas.csv", index=False, encoding="utf-8-sig")

    coef = regresion(p)
    coef.to_csv(RESULTADOS / "factores_regresion.csv", encoding="utf-8-sig")
    print((coef.round(3)).to_string(), "\n")

    imp = boosting(p)
    imp.to_csv(RESULTADOS / "factores_importancia.csv", encoding="utf-8-sig")
    print(imp.round(4).to_string())
