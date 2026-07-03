# COVID-19 · Dashboard CORD-19 (2021)

Dashboard visual, minimalista y reactivo sobre la producción científica de COVID-19
en 2021 (corpus **CORD-19**, `metadata.csv`). Hereda la identidad visual del notebook
de la Fase IV: paleta **azul/teal + ámbar** y tipografía **Poppins / Inter / JetBrains Mono**.

Pensado para que **cualquier persona lo entienda a primera vista**: tarjetas con las cifras
clave, una barra lateral de filtros y cuatro pestañas de gráficos interactivos que se
actualizan al instante al cambiar cualquier filtro.

## Estructura

| Archivo | Qué hace |
|---|---|
| `preprocess.py` | Lee `context/metadata.csv` (~860 MB), filtra **solo 2021** y guarda un parquet ligero (~3 MB) en `data/`. Se ejecuta **una sola vez**. |
| `theme.py` | Identidad visual: paleta, tipografía, plantilla de Plotly y CSS. |
| `app.py` | La aplicación Streamlit (KPIs + filtros + pestañas). |
| `.streamlit/config.toml` | Tema base (colores) de Streamlit. |

## Cómo ejecutarlo

```bash
# 1. Crear entorno e instalar dependencias
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Generar el parquet ligero (una sola vez; tarda ~30-60 s)
python preprocess.py

# 3. Lanzar el dashboard
streamlit run app.py
```

Se abre en `http://localhost:8501`.

## Contenido del dashboard

- **Tarjetas KPI**: nº de artículos, % con resumen, % con DOI, revistas distintas,
  longitud típica del resumen y nº típico de autores (medianas, robustas a valores extremos).
- **📈 Tendencia**: artículos por mes (con el mes pico en ámbar) y total acumulado.
- **🏷️ Categorías**: top 10 fuentes, top 10 revistas y distribución de licencias (acceso).
- **📝 Textos y autores**: distribución de longitud de título, de resumen y nº de autores.
- **🔗 Relaciones**: matriz de correlación y densidad resumen vs. nº de autores.

### Filtros (barra lateral)
Periodo (rango de meses), fuente de datos, licencia, nº de autores y «solo artículos con
resumen». Cualquier cambio recalcula **todas** las cifras y gráficos.

> Nota: el snapshot de `metadata.csv` es de mediados de 2021, por eso el volumen mensual
> cae de forma natural a partir de mayo/junio.
