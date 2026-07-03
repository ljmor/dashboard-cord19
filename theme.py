"""
Identidad visual del dashboard — extraída del notebook (Fase IV).
Paleta, tipografía (Poppins / Inter / JetBrains Mono), plantilla de Plotly y CSS.
"""
from __future__ import annotations
import plotly.graph_objects as go
import plotly.io as pio

# ---- Paleta (idéntica al notebook) ----------------------------------------
PALETA = {
    "ink":     "#14213D",  # texto principal / títulos
    "slate":   "#5B6B7B",  # texto secundario / ejes
    "muted":   "#8A99A8",  # texto terciario / anotaciones
    "bg":      "#F4F7FA",  # fondo general
    "surface": "#FFFFFF",  # tarjetas y áreas de gráfico
    "grid":    "#E2E8F0",  # líneas de cuadrícula
    "primary": "#1D6FB8",  # azul de marca
    "teal":    "#17A2A6",  # verde-azulado
    "mint":    "#6FCF97",  # verde menta
    "violet":  "#9B5DE5",  # violeta
    "amber":   "#F2994A",  # acento cálido -> destacar
    "coral":   "#EB5757",  # alerta
    "ok":      "#27AE60",  # semántico positivo
    "warning": "#E0A800",  # semántico atención
}

# Paleta categórica ordenada por contraste (igual que el notebook)
CATEGORICAL = [
    PALETA["primary"], PALETA["teal"], PALETA["amber"],
    PALETA["mint"], PALETA["violet"], PALETA["coral"], PALETA["slate"],
]

# Escala secuencial azul (equivalente a CMAP_SEC del notebook)
CMAP_SEC = [
    [0.0, "#EAF2F9"], [0.25, "#A9CCE8"], [0.5, "#5B9BD5"],
    [0.75, PALETA["primary"]], [1.0, PALETA["ink"]],
]

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

FONT_CUERPO = "Inter, 'Helvetica Neue', Arial, sans-serif"
FONT_TITULO = "Poppins, 'Segoe UI', Helvetica, Arial, sans-serif"
FONT_MONO = "'JetBrains Mono', 'Roboto Mono', ui-monospace, monospace"


def registrar_template() -> str:
    """Registra y devuelve el nombre de una plantilla Plotly con la identidad."""
    tpl = go.layout.Template()
    tpl.layout = go.Layout(
        font=dict(family=FONT_CUERPO, color=PALETA["slate"], size=13),
        title=dict(font=dict(family=FONT_TITULO, color=PALETA["ink"], size=17), x=0.01),
        paper_bgcolor=PALETA["surface"],
        plot_bgcolor=PALETA["surface"],
        colorway=CATEGORICAL,
        xaxis=dict(gridcolor=PALETA["grid"], linecolor=PALETA["grid"],
                   zerolinecolor=PALETA["grid"], tickfont=dict(size=12)),
        yaxis=dict(gridcolor=PALETA["grid"], linecolor=PALETA["grid"],
                   zerolinecolor=PALETA["grid"], tickfont=dict(size=12)),
        hoverlabel=dict(font=dict(family=FONT_CUERPO, size=13),
                        bgcolor=PALETA["ink"], bordercolor=PALETA["ink"]),
        margin=dict(l=10, r=10, t=48, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    pio.templates["cord19"] = tpl
    return "cord19"


def inyectar_css() -> str:
    """CSS global: fuentes de Google, fondo, tarjetas KPI y detalles finos."""
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;700&display=swap');

    .stApp {{ background: {PALETA['bg']}; }}
    html, body, [class*="css"] {{ font-family: {FONT_CUERPO}; color: {PALETA['ink']}; }}
    h1, h2, h3, h4 {{ font-family: {FONT_TITULO} !important; color: {PALETA['ink']} !important; letter-spacing: -0.2px; }}

    /* Encabezado del dashboard */
    .hero-title {{ font-family: {FONT_TITULO}; font-weight: 700; font-size: 30px;
                   color: {PALETA['ink']}; margin: 0; line-height: 1.1; }}
    .hero-sub {{ font-family: {FONT_CUERPO}; font-size: 14px; color: {PALETA['slate']}; margin-top: 4px; }}

    /* Tarjetas KPI */
    .kpi-card {{ background: {PALETA['surface']}; border: 1px solid {PALETA['grid']};
                 border-radius: 16px; padding: 16px 18px; position: relative; overflow: hidden;
                 box-shadow: 0 1px 2px rgba(20,33,61,0.04); height: 100%; }}
    .kpi-bar {{ position: absolute; left: 0; top: 0; bottom: 0; width: 6px; border-radius: 16px 0 0 16px; }}
    .kpi-label {{ font-family: {FONT_CUERPO}; font-size: 12.5px; color: {PALETA['slate']};
                  font-weight: 500; text-transform: uppercase; letter-spacing: 0.4px; }}
    .kpi-value {{ font-family: {FONT_MONO}; font-weight: 700; font-size: 34px;
                  color: {PALETA['ink']}; line-height: 1.1; margin-top: 6px; }}
    .kpi-hint {{ font-family: {FONT_CUERPO}; font-size: 12px; color: {PALETA['muted']}; margin-top: 2px; }}

    /* Contenedores de gráficos como tarjetas */
    div[data-testid="stVerticalBlockBorderWrapper"] {{ background: {PALETA['surface']};
        border-radius: 16px; border: 1px solid {PALETA['grid']} !important; }}

    /* Pestañas */
    .stTabs [data-baseweb="tab-list"] {{ gap: 6px; }}
    .stTabs [data-baseweb="tab"] {{ font-family: {FONT_TITULO}; font-weight: 500;
        background: {PALETA['surface']}; border: 1px solid {PALETA['grid']};
        border-radius: 10px; padding: 8px 16px; color: {PALETA['slate']}; }}
    .stTabs [aria-selected="true"] {{ background: {PALETA['primary']} !important;
        color: white !important; border-color: {PALETA['primary']} !important; }}

    /* Barra lateral */
    section[data-testid="stSidebar"] {{ background: {PALETA['surface']}; border-right: 1px solid {PALETA['grid']}; }}
    section[data-testid="stSidebar"] h2 {{ font-size: 18px; }}

    #MainMenu, footer {{ visibility: hidden; }}
    </style>
    """


def kpi_card(label: str, value: str, color: str, hint: str = "") -> str:
    """HTML de una tarjeta KPI con cifra en monoespaciada."""
    return f"""
    <div class="kpi-card">
      <div class="kpi-bar" style="background:{color};"></div>
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}</div>
      <div class="kpi-hint">{hint}</div>
    </div>
    """
