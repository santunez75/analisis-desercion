# Análisis de deserción en la educación superior chilena

Trabajo del curso **Estadística Computacional** — Magíster en Ciencia de Datos e
Inteligencia Artificial, Universidad Andrés Bello.

**Autor:** Sebastian Antunez Noguera

## Entrega

**Sumativa 1 — Informe técnico de avance.** Aplica estadística descriptiva,
estimación por intervalos y contraste de hipótesis sobre 9.678 programas de
educación superior, en torno a una pregunta de decisión: dónde concentrar un
presupuesto limitado de retención.

| Entregable | Archivo |
|---|---|
| Informe técnico (6 páginas) | `informe/Sumativa1_Informe_Sebastian_Antunez.pdf` |
| Cuaderno de análisis | `notebooks/Sumativa1_Analisis_Desercion.ipynb` |
| Figuras y tablas generadas | `resultados/` |

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
│   └── base_programas.csv   Conjunto analítico, una fila por programa
├── notebooks/
│   └── Sumativa1_Analisis_Desercion.ipynb   Cuaderno de la Sumativa 1
├── informe/
│   └── Sumativa1_Informe_...pdf/.docx       Informe técnico de avance
├── resultados/
│   ├── figuras/             Cuatro figuras del informe
│   └── tablas/              Diccionario de variables, descriptivos,
│                            estimaciones y contrastes
├── requirements.txt         Dependencias con versiones fijadas
└── README.md
```

## Créditos

Datos publicados por el **Servicio de Información de Educación Superior (SIES)**
del Ministerio de Educación de Chile bajo licencia de datos abiertos. El código
de este repositorio se distribuye con fines académicos.
