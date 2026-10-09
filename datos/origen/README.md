# Procedencia del conjunto analítico

Esta carpeta documenta cómo se llegó desde las dos bases abiertas del SIES
hasta los archivos que consume el análisis: `datos/base_programas.csv` y
`datos/diagnostico_extremos.csv`.

Los scripts se incluyen tal como se ejecutaron. **No forman parte del flujo de
este repositorio**: operan sobre las bases completas del SIES (188 MB) y sobre
artefactos intermedios que, por tamaño, no están versionados. Se conservan aquí
para que la construcción del dato sea auditable y no haya que creer en la
palabra del informe.

## Las dos fuentes

| Archivo original | Formato | Peso | Filas | Columnas |
|---|---|---|---|---|
| `Matricula_2007_2026_WEB_10_07_2026.csv` | CSV `;`, latin-1 | 149 MB | 280.160 | 58 |
| `TITULADO_2007-2025_web_27_05_2026_E-1.xlsx` | Excel | 39 MB | 234.074 | 42 |

Ambas se publican **agregadas por programa y año**: no hay registros por
estudiante. Esa es la restricción que determina todo lo demás.

## La cadena, paso a paso

### 1. `00_cargar.py` — normalizar

Lee los dos archivos y uniforma los nombres de columna: quita tildes, pasa a
minúsculas y reemplaza por guión bajo todo lo que no sea alfanumérico, de modo
que `Año` y `Código Carrera` pasen a ser `anio` y `codigo_carrera`. Extrae el
año con una expresión regular, porque el campo original a veces trae texto.
Guarda ambas bases en Parquet.

### 2. `01_tasa_abandono.py` — el cruce temporal

Es el paso que da origen a la variable respuesta, y no es un cruce por el mismo
año. A una cohorte que **ingresa** en el año *y* le corresponden los
**titulados** del año *y + L*, donde *L* es la duración formal de la carrera:

```python
ing["lag"] = np.ceil(ing["duracion_estudio_carrera"] / 2)   # semestres -> años
ing["anio_tit"] = ing["anio"] + ing["lag"]
c = ing.merge(tit, on=["codigo_carrera", "anio_tit"], how="left").fillna({"titulados": 0})
```

La llave es el **código de programa más ese año desplazado**. En la base de
titulados la columna se llama `codigo_programa` y se renombra antes de unir.

Filtros aplicados antes del cruce: nivel Pregrado, plan regular, y los tres
tipos de carrera (técnico de nivel superior, profesional con licenciatura y
profesional sin licenciatura). Se retienen los años de titulación 2010–2025,
porque antes de 2010 menos del 90 % de los titulados cruza con matrícula.

Los atributos del programa —institución, región, área, jornada— se toman del
**último año** en que aparece en matrícula.

Resultado: `cohortes.parquet`, **151.645 filas** (una por programa y año de
titulación esperado) sobre **28.741 programas distintos**.

### 3. `02_factores.py` — colapsar a una fila por programa

De la matrícula se derivan las variables explicativas año a año —proporción de
mujeres, de egreso municipal, particular pagado y técnico-profesional, edad
media, estado de acreditación y matrícula total— y se pegan a las cohortes.
Después se agrupa por programa con un **promedio ponderado por el ingreso de
cada año**:

```python
out = {k: np.average(d[k], weights=d["ingreso"]) for k in num}
out["ingreso"] = w.sum()
out["titulados"] = d["titulados"].sum()
```

De ahí viene que `inst_acreditada` no sea 0 o 1 sino cualquier valor
intermedio: es el promedio del estado de acreditación a lo largo de los años de
cohorte, y un programa cuya institución perdió la acreditación a mitad del
período recibe un valor fraccionario.

Finalmente se exige un ingreso acumulado de al menos 100 estudiantes, para que
el cociente no dependa de unas pocas personas, y se calcula la respuesta:

```python
p["abandono"] = 1 - (p["titulados"] / p["ingreso"]).clip(upper=1)
```

El `clip` es el origen del apilamiento en cero: un programa que titula a más
personas de las que ingresaron en la ventana queda registrado con abandono
exactamente cero.

Resultado: **`base_programas.csv`, 9.678 programas × 25 variables**, de los
28.741 iniciales.

### 4. `03_diagnostico_extremos.py` — auditar los extremos

Para cada uno de los 465 programas con abandono exactamente 0 o 1, registra el
último año en que apareció en matrícula, el año de egreso esperado de su última
cohorte y las titulaciones acumuladas en cualquier año. Permite distinguir un
cierre real de un desajuste entre las bases.

Resultado: **`diagnostico_extremos.csv`, 465 filas × 8 columnas**.

## Resumen de la reducción

| Etapa | Unidad | Filas |
|---|---|---|
| Matrícula original | programa-año | 280.160 |
| Titulados original | programa-año | 234.074 |
| Cohortes cruzadas | programa-año de egreso | 151.645 |
| Base analítica | programa | **9.678** |
| Diagnóstico de extremos | programa | 465 |

## Lo que esta construcción implica

El abandono resultante es **aparente**, no observado. Con datos agregados,
quien se cambia de carrera o de institución y se titula en otra parte cuenta
aquí como abandono, y quien se titula fuera de la ventana queda sin registrar.
La cifra es una cota superior, y el apartado 3.1 del informe cuantifica cuánto
de los casos extremos corresponde a cada causa.
