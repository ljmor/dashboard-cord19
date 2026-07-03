"""
Dashboard COVID-19 · CORD-19 (2021)
Visual, minimalista y reactivo. Identidad visual heredada del notebook (Fase IV).

Ejecutar:
    streamlit run app.py
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from theme import (
    PALETA, CATEGORICAL, CMAP_SEC, MESES,
    registrar_template, inyectar_css, kpi_card,
)

AQUI = os.path.dirname(os.path.abspath(__file__))
RUTA_PARQUET = os.path.join(AQUI, "data", "cord19_2021.parquet")
TEMPLATE = registrar_template()

st.set_page_config(
    page_title="COVID-19 · Dashboard 2021",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(inyectar_css(), unsafe_allow_html=True)

PLOTLY_CFG = {"displayModeBar": False, "responsive": True}


# --------------------------------------------------------------------------
# Datos
# --------------------------------------------------------------------------
@st.cache_data(show_spinner="Cargando datos…")
def cargar_datos() -> pd.DataFrame:
    df = pd.read_parquet(RUTA_PARQUET)
    # Tipos numéricos "normales" (float/int) para graficar sin fricción
    for c in ("publish_month", "title_len", "abstract_len", "n_authors",
              "has_abstract", "has_doi", "has_pmcid", "has_journal"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ("source_x", "journal", "license"):
        df[c] = df[c].astype("object")
    return df


if not os.path.exists(RUTA_PARQUET):
    st.error(
        "No se encontró `data/cord19_2021.parquet`.\n\n"
        "Genera primero el archivo con:  `python preprocess.py`"
    )
    st.stop()

df = cargar_datos()

# --------------------------------------------------------------------------
# Barra lateral de filtros
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🧬 Filtros")
    st.caption("Todo el tablero se actualiza al instante al cambiar un filtro.")

    if st.button("↺  Restablecer filtros", width="stretch"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

    st.divider()

    # --- Rango de meses ---
    st.markdown("**Periodo (2021)**")
    m_ini, m_fin = st.select_slider(
        "Rango de meses",
        options=list(range(1, 13)),
        value=(1, 12),
        format_func=lambda m: MESES[m - 1],
        label_visibility="collapsed",
    )

    # --- Fuente ---
    fuentes = sorted(df["source_x"].dropna().unique().tolist())
    sel_fuentes = st.multiselect(
        "Fuente de datos", fuentes, default=[],
        placeholder="Todas las fuentes",
        help="De dónde proviene cada artículo (PubMed, PMC, etc.).",
    )

    # --- Licencia ---
    licencias = sorted(df["license"].fillna("desconocida").unique().tolist())
    sel_lic = st.multiselect(
        "Licencia", licencias, default=[],
        placeholder="Todas las licencias",
        help="Tipo de permiso de uso del artículo.",
    )

    # --- Nº de autores ---
    max_aut = int(np.nanpercentile(df["n_authors"], 99))
    r_aut = st.slider(
        "Nº de autores por artículo", 0, max_aut, (0, max_aut),
        help=f"Acotado al percentil 99 ({max_aut} autores) para ignorar casos extremos.",
    )

    # --- Solo con resumen ---
    solo_abstract = st.toggle(
        "Solo artículos con resumen", value=False,
        help="Muestra únicamente los que tienen 'abstract'.",
    )


# --------------------------------------------------------------------------
# Aplicar filtros
# --------------------------------------------------------------------------
def aplicar_filtros(d: pd.DataFrame) -> pd.DataFrame:
    d = d[d["publish_month"].between(m_ini, m_fin)]
    if sel_fuentes:
        d = d[d["source_x"].isin(sel_fuentes)]
    if sel_lic:
        d = d[d["license"].fillna("desconocida").isin(sel_lic)]
    d = d[d["n_authors"].between(r_aut[0], r_aut[1])]
    if solo_abstract:
        d = d[d["has_abstract"] == 1]
    return d


dff = aplicar_filtros(df)

# --------------------------------------------------------------------------
# Encabezado
# --------------------------------------------------------------------------
c1, c2 = st.columns([0.75, 0.25])
with c1:
    st.markdown(
        '<div class="hero-title">COVID-19 · Producción científica 2021</div>'
        '<div class="hero-sub">Corpus CORD-19 — explora cuánto, quién y cómo se publicó '
        'sobre COVID-19 durante 2021.</div>',
        unsafe_allow_html=True,
    )
with c2:
    pct = len(dff) / len(df) * 100 if len(df) else 0
    st.markdown(
        f'<div style="text-align:right; padding-top:6px;">'
        f'<span class="kpi-value" style="font-size:26px;">{len(dff):,}</span><br>'
        f'<span class="kpi-hint">de {len(df):,} artículos ({pct:.0f}%) con los filtros actuales</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

if dff.empty:
    st.warning("Ningún artículo cumple los filtros seleccionados. Prueba a ampliarlos.")
    st.stop()

st.write("")

# --------------------------------------------------------------------------
# Fila de KPIs
# --------------------------------------------------------------------------
kpis = [
    ("Artículos", f"{len(dff):,}", PALETA["primary"], "publicados en el periodo"),
    ("Con resumen", f"{dff['has_abstract'].mean()*100:.0f}%", PALETA["teal"], "incluyen 'abstract'"),
    ("Con DOI", f"{dff['has_doi'].mean()*100:.0f}%", PALETA["violet"], "identificador permanente"),
    ("Revistas", f"{dff['journal'].nunique():,}", PALETA["mint"], "publicaciones distintas"),
    ("Resumen típico", f"{int(dff['abstract_len'].median()) if dff['abstract_len'].notna().any() else 0}",
     PALETA["amber"], "caracteres (mediana)"),
    ("Autores típicos", f"{int(dff['n_authors'].median())}", PALETA["coral"], "por artículo (mediana)"),
]
cols = st.columns(len(kpis))
for col, (label, value, color, hint) in zip(cols, kpis):
    with col:
        st.markdown(kpi_card(label, value, color, hint), unsafe_allow_html=True)

st.write("")

# --------------------------------------------------------------------------
# Funciones de gráficos
# --------------------------------------------------------------------------
def fig_vacia(titulo: str, height: int = 340) -> go.Figure:
    """Figura con la identidad visual y un mensaje cuando no hay datos."""
    fig = go.Figure()
    fig.add_annotation(text="Sin datos suficientes para este gráfico",
                       showarrow=False, font=dict(color=PALETA["muted"], size=14))
    fig.update_layout(template=TEMPLATE, height=height, title=titulo,
                      xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig


def fig_serie_mensual(d: pd.DataFrame) -> go.Figure:
    por_mes = (d.groupby("publish_month").size()
               .reindex(range(1, 13), fill_value=0))
    x = [MESES[m - 1] for m in por_mes.index]
    y = por_mes.values
    pico = int(np.argmax(y))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="lines", line=dict(color=PALETA["primary"], width=0),
        fill="tozeroy", fillcolor="rgba(29,111,184,0.16)", hoverinfo="skip",
        showlegend=False))
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="lines+markers", name="Artículos",
        line=dict(color=PALETA["primary"], width=3),
        marker=dict(size=8, color=PALETA["surface"],
                    line=dict(color=PALETA["primary"], width=2)),
        hovertemplate="<b>%{x}</b><br>%{y:,} artículos<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=[x[pico]], y=[y[pico]], mode="markers+text",
        marker=dict(size=15, color=PALETA["amber"], line=dict(color="white", width=2)),
        text=[f"  pico: {x[pico]}"], textposition="top center",
        textfont=dict(color=PALETA["amber"], family="Poppins", size=13),
        hovertemplate=f"<b>Mes pico: {x[pico]}</b><br>%{{y:,}} artículos<extra></extra>",
        showlegend=False))
    fig.update_layout(template=TEMPLATE, height=360,
                      title="Artículos publicados por mes",
                      yaxis_title="Nº de artículos", showlegend=False)
    return fig


def fig_acumulado(d: pd.DataFrame) -> go.Figure:
    por_mes = (d.groupby("publish_month").size()
               .reindex(range(1, 13), fill_value=0))
    x = [MESES[m - 1] for m in por_mes.index]
    y = por_mes.cumsum().values
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="lines", line=dict(color=PALETA["teal"], width=0),
        fill="tozeroy", fillcolor="rgba(23,162,166,0.16)", hoverinfo="skip",
        showlegend=False))
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="lines+markers", line=dict(color=PALETA["teal"], width=3),
        marker=dict(size=7, color=PALETA["surface"],
                    line=dict(color=PALETA["teal"], width=2)),
        hovertemplate="<b>Hasta %{x}</b><br>%{y:,} artículos acumulados<extra></extra>"))
    fig.update_layout(template=TEMPLATE, height=360,
                      title="Total acumulado en el año",
                      yaxis_title="Artículos acumulados", showlegend=False)
    return fig


def fig_ranking(serie: pd.Series, titulo: str, n: int = 10) -> go.Figure:
    top = serie.value_counts().head(n).iloc[::-1]
    if top.empty:
        return fig_vacia(titulo, height=380)
    colores = [PALETA["primary"]] * len(top)
    if len(colores):
        colores[-1] = PALETA["amber"]  # líder resaltado en ámbar
    etiquetas = [str(x)[:42] + ("…" if len(str(x)) > 42 else "") for x in top.index]
    fig = go.Figure(go.Bar(
        x=top.values, y=etiquetas, orientation="h",
        marker=dict(color=colores, line=dict(color="white", width=1)),
        text=[f" {v:,}" for v in top.values], textposition="outside",
        textfont=dict(family="JetBrains Mono", size=11, color=PALETA["slate"]),
        hovertemplate="<b>%{y}</b><br>%{x:,} artículos<extra></extra>"))
    fig.update_layout(template=TEMPLATE, height=380, title=titulo,
                      xaxis_title="Nº de artículos",
                      margin=dict(l=10, r=60, t=48, b=10))
    fig.update_xaxes(range=[0, top.values.max() * 1.15])
    return fig


def fig_licencias(d: pd.DataFrame) -> go.Figure:
    lic = d["license"].fillna("desconocida").value_counts()
    if lic.empty:
        return fig_vacia("Tipo de licencia (acceso)", height=380)
    top = lic.head(6)
    otras = lic.iloc[6:].sum()
    if otras > 0:
        top = pd.concat([top, pd.Series({"otras": otras})])
    fig = go.Figure(go.Pie(
        labels=top.index, values=top.values, hole=0.62, sort=False,
        direction="clockwise", rotation=90,
        marker=dict(colors=CATEGORICAL[:len(top)],
                    line=dict(color=PALETA["surface"], width=2)),
        textinfo="percent", textfont=dict(family="Inter", size=12),
        hovertemplate="<b>%{label}</b><br>%{value:,} artículos (%{percent})<extra></extra>"))
    fig.update_layout(
        template=TEMPLATE, height=380, title="Tipo de licencia (acceso)",
        annotations=[dict(text=f"<b>{len(d):,}</b><br>artículos", x=0.5, y=0.5,
                          font=dict(family="JetBrains Mono", size=16, color=PALETA["ink"]),
                          showarrow=False)],
        legend=dict(orientation="v", x=1.0, y=0.5))
    return fig


def fig_histograma(serie: pd.Series, titulo: str, color: str,
                   tope: int, unidad: str) -> go.Figure:
    s = serie.dropna().clip(upper=tope)
    if s.empty:
        return fig_vacia(titulo)
    med = s.median()
    fig = go.Figure(go.Histogram(
        x=s, nbinsx=45, marker=dict(color=color, line=dict(color="white", width=0.5)),
        hovertemplate=f"%{{x}} {unidad}<br>%{{y:,}} artículos<extra></extra>"))
    fig.add_vline(x=med, line=dict(color=PALETA["amber"], width=2.5, dash="solid"),
                  annotation_text=f"mediana: {med:.0f}", annotation_position="top",
                  annotation_font=dict(color=PALETA["amber"], family="Poppins", size=12))
    fig.update_layout(template=TEMPLATE, height=340, title=titulo,
                      xaxis_title=unidad, yaxis_title="Nº de artículos", bargap=0.02)
    return fig


def fig_correlacion(d: pd.DataFrame) -> go.Figure:
    cols = ["title_len", "abstract_len", "n_authors", "has_abstract", "has_doi", "has_pmcid"]
    etiquetas = ["Long. título", "Long. resumen", "Nº autores",
                 "Tiene resumen", "Tiene DOI", "Tiene PMCID"]
    corr = d[cols].corr().round(2)
    fig = go.Figure(go.Heatmap(
        z=corr.values, x=etiquetas, y=etiquetas,
        colorscale=CMAP_SEC, zmin=-1, zmax=1,
        text=corr.values, texttemplate="%{text:.2f}",
        textfont=dict(family="JetBrains Mono", size=11),
        hovertemplate="%{x} ↔ %{y}<br>correlación: %{z:.2f}<extra></extra>",
        colorbar=dict(title="corr", thickness=12)))
    fig.update_layout(template=TEMPLATE, height=420,
                      title="¿Se relacionan las variables?", xaxis=dict(tickangle=-30))
    return fig


def fig_densidad(d: pd.DataFrame) -> go.Figure:
    sub = d[(d["abstract_len"].notna()) & (d["n_authors"] > 0)].copy()
    if sub.empty:
        return fig_vacia("Extensión del resumen vs. nº de autores", height=420)
    sub["abstract_len"] = sub["abstract_len"].clip(upper=4000)
    sub["n_authors"] = sub["n_authors"].clip(upper=30)
    fig = go.Figure(go.Histogram2d(
        x=sub["abstract_len"], y=sub["n_authors"], nbinsx=35, nbinsy=30,
        colorscale=CMAP_SEC, colorbar=dict(title="nº art.", thickness=12),
        hovertemplate="Resumen ~%{x} car.<br>~%{y} autores<br>%{z:,} artículos<extra></extra>"))
    fig.update_layout(template=TEMPLATE, height=420,
                      title="Extensión del resumen vs. nº de autores",
                      xaxis_title="Longitud del resumen (caracteres)",
                      yaxis_title="Nº de autores")
    return fig


# --------------------------------------------------------------------------
# Pestañas
# --------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📈  Tendencia", "🏷️  Categorías", "📝  Textos y autores", "🔗  Relaciones",
])

with tab1:
    a, b = st.columns([0.58, 0.42])
    with a:
        with st.container(border=True):
            st.plotly_chart(fig_serie_mensual(dff), width="stretch", config=PLOTLY_CFG)
            st.caption("El punto **ámbar** marca el mes con más publicaciones. Pasa el cursor por la línea para ver el detalle.")
    with b:
        with st.container(border=True):
            st.plotly_chart(fig_acumulado(dff), width="stretch", config=PLOTLY_CFG)
            st.caption("Cuánto se había publicado en total conforme avanzaba el año.")

with tab2:
    a, b = st.columns(2)
    with a:
        with st.container(border=True):
            st.plotly_chart(fig_ranking(dff["source_x"], "Top 10 fuentes de datos"),
                            width="stretch", config=PLOTLY_CFG)
            st.caption("La barra **ámbar** es la fuente que más aporta.")
    with b:
        with st.container(border=True):
            st.plotly_chart(fig_ranking(dff["journal"].dropna(), "Top 10 revistas"),
                            width="stretch", config=PLOTLY_CFG)
            st.caption("Revistas científicas con más artículos sobre COVID-19.")
    with st.container(border=True):
        left, right = st.columns([0.5, 0.5])
        with left:
            st.plotly_chart(fig_licencias(dff), width="stretch", config=PLOTLY_CFG)
        with right:
            st.markdown("#### ¿Qué es la licencia?")
            st.write(
                "Indica **cómo se puede usar** cada artículo. Las licencias `cc-by` y "
                "similares son de **acceso abierto**: cualquiera puede leerlas y reutilizarlas. "
                "La mayoría del corpus de 2021 es abierto, lo que facilita la investigación."
            )
            st.caption("El anillo muestra las 6 licencias más comunes; el resto se agrupa en «otras».")

with tab3:
    a, b = st.columns(2)
    with a:
        with st.container(border=True):
            st.plotly_chart(
                fig_histograma(dff["title_len"], "Longitud del título",
                               PALETA["primary"], 400, "caracteres"),
                width="stretch", config=PLOTLY_CFG)
    with b:
        with st.container(border=True):
            st.plotly_chart(
                fig_histograma(dff["abstract_len"], "Longitud del resumen",
                               PALETA["teal"], 4000, "caracteres"),
                width="stretch", config=PLOTLY_CFG)
    with st.container(border=True):
        st.plotly_chart(
            fig_histograma(dff["n_authors"], "Número de autores por artículo",
                           PALETA["violet"], 30, "autores"),
            width="stretch", config=PLOTLY_CFG)
        st.caption("La línea **ámbar** marca el valor típico (mediana). Usamos la mediana porque "
                   "resiste bien los casos extremos (títulos larguísimos o equipos enormes).")

with tab4:
    a, b = st.columns(2)
    with a:
        with st.container(border=True):
            st.plotly_chart(fig_correlacion(dff), width="stretch", config=PLOTLY_CFG)
            st.caption("Cercano a **0** = sin relación; a **1** = suben juntas; a **-1** = una sube y la otra baja. "
                       "Aquí las relaciones son débiles: los datos son bastante independientes.")
    with b:
        with st.container(border=True):
            st.plotly_chart(fig_densidad(dff), width="stretch", config=PLOTLY_CFG)
            st.caption("Cada celda es más oscura cuanto más artículos caen ahí. No hay un patrón claro "
                       "entre lo largo del resumen y cuántos autores firman.")

st.write("")
st.caption(
    "Fuente: CORD-19 (`metadata.csv`), subconjunto con fecha de publicación en 2021 · "
    "Identidad visual: paleta azul/teal + ámbar y tipografía Poppins/Inter/JetBrains Mono (Fase IV)."
)
