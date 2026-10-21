# Análisis de deserción en la educación superior chilena

Trabajo del curso **Estadística Computacional** — Magíster en Ciencia de Datos e
Inteligencia Artificial, Universidad Andrés Bello.

**Autores:** María Fassler Neumann · Sebastian Antunez Noguera — Grupo 4
**Profesor:** Jean Paul Maidana

## Entregas

**Sumativa 3 — Modelamiento predictivo integrado.** Cierra la cadena: cada
decisión metodológica de esta fase proviene de un resultado documentado en las
anteriores. Cubre el tratamiento de datos faltantes, la clasificación por
regresión logística con tres criterios de selección de variables —dominio,
stepwise por AIC y reducida—, la evaluación de estabilidad por bootstrap y el
análisis del impacto de la imputación. La partición es 70/30 estratificada con
semilla fija.

| Entregable | Archivo |
|---|---|
| Informe técnico | `S3/informe/Sumativa3_Informe_Maria_Fassler_Sebastian_Antunez.docx` |
| Cuaderno maestro | `S3/Sumativa3_Proyecto_Integrado.ipynb` |
| Presentación con guion cronometrado | `S3/presentacion/Sumativa3_Presentacion_Grupo4.pptx` |
| Figuras y tablas generadas | `S3/resultados/` |

El conjunto no tiene datos faltantes ni los tuvo, porque cada fila es un
agregado por programa. En lugar de inventar el problema, se monta un
experimento controlado de ausencia bajo los tres mecanismos de Rubin, que
permite medir el error contra los valores verdaderos: la imputación por
regresión conserva el 100 % de la muestra frente al 47,5 % que deja la
eliminación, y preserva mejor las correlaciones de la Sumativa 1.

Hallazgo central: **dos bootstraps que responden preguntas distintas**. El
estándar, que remuestrea observaciones, reproduce los intervalos clásicos con
una razón de amplitudes de **1,00 a 1,12**, de modo que la precisión declarada
es correcta bajo muestreo independiente. El que remuestrea **instituciones**,
como la Sumativa 2 advirtió que correspondía, los ensancha **entre 1,62 y 3,01
veces**, y siete de los veinte coeficientes pierden la determinación de su
signo. Los programas de una misma institución no son independientes, y esa es
la fuente de incertidumbre que el ajuste clásico no ve.

Frente a la línea base —el clasificador trivial que predice siempre la clase
mayoritaria, con exactitud 0,549 y F1 0,709— el modelo final suma **12,9 puntos
de exactitud** y eleva el AUC de 0,500 a **0,730**, aunque su F1 mejora solo en
0,011: la ganancia está en la discriminación, no en la sensibilidad.

**Sumativa 2 — Validación por remuestreo y simulación.** Somete los resultados
de la Sumativa 1 a métodos que no dependen de supuestos distribucionales:
bootstrap de los intervalos, test de permutación, estabilidad de las
correlaciones, simulación Monte Carlo de la decisión de focalización y análisis
de robustez. Todos los procedimientos emplean 10.000 repeticiones.

| Entregable | Archivo |
|---|---|
| Informe técnico | `S2/informe/Sumativa2_Informe_Maria_Fassler_Sebastian_Antunez.pdf` |
| Cuaderno de validación | `S2/Sumativa2_Validacion_Remuestreo.ipynb` |
| Resultados validados para la S3 | `resultados_validados.csv` |

Hallazgo central: los intervalos bootstrap reproducen los clásicos con una
discrepancia inferior al 1 %, de modo que los supuestos de la fase anterior se
sostienen. Y la simulación cuantifica lo que la Sumativa 1 solo había
enunciado: focalizar por el abandono medido alcanza a un **38,9 % más de
estudiantes** que focalizar por acreditación, ventaja que persiste en los
dieciséis escenarios examinados.

**Sumativa 1 — Informe técnico de avance.** Aplica estadística descriptiva,
estimación por intervalos y contraste de hipótesis sobre 9.678 programas de
educación superior, en torno a una pregunta de decisión: dónde concentrar un
presupuesto limitado de retención.

| Entregable | Archivo |
|---|---|
| Informe técnico | `S1/informe/Sumativa1_Informe_Maria_Fassler_Sebastian_Antunez.pdf` |
| Cuaderno de análisis | `S1/Sumativa1_Analisis_Desercion.ipynb` |
| Figuras y tablas generadas | `S1/resultados/` |

Hallazgo central: los tres contrastes rechazan la hipótesis nula con valores p
entre 10⁻²⁰ y 10⁻⁷⁸, pero sus tamaños del efecto van de grande (d = 0,80 para
la acreditación institucional) a despreciable (η² = 0,040 para el área del
conocimiento). Con casi diez mil observaciones el valor p deja de discriminar,
de modo que solo uno de los tres criterios sirve para focalizar.

## Datos

`datos/base_programas.csv` — **9.678 programas × 25 variables**, construido a
partir de las bases abiertas del SIES de matrícula (2007–2026) y titulados
(2007–2025).

La unidad de análisis es el **programa** (carrera, sede, jornada y modalidad),
no el estudiante: las bases del SIES vienen agregadas por programa y año, sin
registros individuales. La variable respuesta es `abandono`, la proporción de
una cohorte que no llega a titularse.

Esa agregación impone el alcance del trabajo. Las conclusiones se refieren a
programas y no a personas, y describen **factores asociados** al abandono, no
sus causas: no hay grupo de control ni seguimiento individual.

### Cómo se construyó

El cruce entre ambas bases no es por el mismo año: a una cohorte que ingresa en
el año *y* le corresponden los titulados de *y + L*, siendo *L* la duración
formal de la carrera. De 280.160 filas de matrícula y 234.074 de titulados se
llega a 151.645 pares programa-año de egreso, que al colapsarse por programa
—promediando las variables explicativas con el ingreso de cada año como peso—
dan los 9.678 programas de la base analítica.

Los cuatro scripts que producen `base_programas.csv` y
`diagnostico_extremos.csv` están en [`datos/origen/`](datos/origen/), junto con
una [descripción paso a paso](datos/origen/README.md) del cruce, los filtros
aplicados y lo que esa construcción implica para interpretar los resultados.
No forman parte del flujo de este repositorio: operan sobre las bases completas
del SIES, que no se versionan por tamaño.

| Fuente | Cobertura | Origen |
|---|---|---|
| Matrícula en educación superior | 2007–2026 | https://datosabiertos.mineduc.cl/ |
| Titulados de educación superior | 2007–2025 | https://datosabiertos.mineduc.cl/ |

Las bases originales (149 MB y 39 MB) no se versionan por el límite de 100 MB
por archivo de GitHub. El conjunto analítico ya agregado sí: pesa 3 MB y hace
que el repositorio se pueda ejecutar sin descargar nada.

## Instalación

Requiere Python 3.11 o superior.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m ipykernel install --user --name analisis-desercion --display-name "Python (analisis-desercion)"
```

El entorno debe quedar **dentro de la carpeta del proyecto**, en
`analisis-desercion/.venv`.

Para abrir los notebooks, con el entorno activado:

```powershell
jupyter lab
```

## Estructura

```
analisis-desercion/
├── datos/
│   ├── base_programas.csv        Conjunto analítico, una fila por programa
│   ├── diagnostico_extremos.csv  Auditoría de los valores 0 y 1
│   └── origen/                   Scripts y documentación de su construcción
├── S1/
│   ├── Sumativa1_Analisis_Desercion.ipynb
│   ├── informe/                  Informe de la Sumativa 1 y el logo
│   └── resultados/figuras, tablas
├── S2/
│   ├── Sumativa2_Validacion_Remuestreo.ipynb
│   ├── informe/                  Informe de la Sumativa 2
│   └── resultados/figuras, tablas
├── S3/
│   ├── Sumativa3_Proyecto_Integrado.ipynb
│   ├── informe/                  Informe de la Sumativa 3
│   ├── presentacion/             Diapositivas con el guion en las notas
│   └── resultados/figuras, tablas
├── resultados_validados.csv      Entrada de la Sumativa 2 a la Sumativa 3
├── requirements.txt              Dependencias con versiones fijadas
└── README.md
```

## Créditos

Datos publicados por el **Servicio de Información de Educación Superior (SIES)**
del Ministerio de Educación de Chile bajo licencia de datos abiertos. El código
de este repositorio se distribuye con fines académicos.
