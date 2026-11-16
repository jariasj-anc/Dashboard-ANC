import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="ANC - Dashboard Estadístico (UIA)", page_icon="⚖️", layout="wide")

st.markdown("""
<div style="background: linear-gradient(90deg, #7f1d1d 0%, #991b1b 60%, #1e293b 100%); padding: 18px 24px; border-radius: 10px; border-left: 6px solid #f59e0b; margin-bottom: 18px;">
    <h2 style="color: white; margin: 0; font-size: 22px;">⚖️ Autoridad Nacional de Control del Poder Judicial</h2>
    <p style="color: #e2e8f0; margin: 4px 0 0 0; font-size: 13px;">Dashboard de Análisis Estadístico, Control de Carga y Proyecciones — Unidad de Inteligencia y Análisis (UIA)</p>
</div>
""", unsafe_allow_html=True)

@st.cache_data
def cargar_datos():
    df = pd.read_excel("data_consolidada_anc.xlsx", sheet_name="Consolidado_ANC")
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df['Anio'] = df['Fecha'].dt.year
    return df

df = cargar_datos()

MESES_ES = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
MESES_CORTO = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun", 7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}

def formato_fecha_es(fecha, corto=False):
    dic = MESES_CORTO if corto else MESES_ES
    return f"{dic[fecha.month]} {fecha.year}"

st.sidebar.header("🏛️ Filtros de Consulta")
lista_sedes = ["TODAS (NIVEL NACIONAL)"] + sorted(df['Sede'].unique().tolist())
sede_seleccionada = st.sidebar.selectbox("Seleccione ODANC / Sede Central:", lista_sedes)
meses_proyeccion = st.sidebar.slider("Meses a proyectar:", 2, 12, 6)

if sede_seleccionada == "TODAS (NIVEL NACIONAL)":
    df_filtrado = df.groupby(['Fecha', 'Anio'])[['Tramite', 'Impugnacion', 'Carga_Total', 'Produccion']].sum().reset_index()
else:
    df_filtrado = df[df['Sede'] == sede_seleccionada].sort_values('Fecha').reset_index(drop=True)

ultimo_mes = df_filtrado.iloc[-1]
penultimo_mes = df_filtrado.iloc[-2]
fecha_ult = ultimo_mes['Fecha']
fecha_pen = penultimo_mes['Fecha']

txt_ult_largo = formato_fecha_es(fecha_ult, corto=False)
txt_ult_corto = formato_fecha_es(fecha_ult, corto=True)
txt_pen_corto = formato_fecha_es(fecha_pen, corto=True)

pct_tramite = (ultimo_mes['Tramite'] / ultimo_mes['Carga_Total'] * 100) if ultimo_mes['Carga_Total'] > 0 else 0
pct_impug = (ultimo_mes['Impugnacion'] / ultimo_mes['Carga_Total'] * 100) if ultimo_mes['Carga_Total'] > 0 else 0

anio_actual = fecha_ult.year
df_anio_actual = df_filtrado[df_filtrado['Anio'] == anio_actual]
prod_acum_actual = int(df_anio_actual['Produccion'].sum())
prom_prod_actual = df_anio_actual['Produccion'].mean()

st.subheader(f"📌 Situación Actual al Cierre de {txt_ult_largo} — {sede_seleccionada}")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Carga Total Activa (Inventario)", f"{int(ultimo_mes['Carga_Total']):,}", f"{int(ultimo_mes['Carga_Total'] - penultimo_mes['Carga_Total']):+,} vs {txt_pen_corto}", delta_color="inverse", border=True)
col2.metric(f"En Trámite ({pct_tramite:.1f}%)", f"{int(ultimo_mes['Tramite']):,}", f"{int(ultimo_mes['Tramite'] - penultimo_mes['Tramite']):+,} vs {txt_pen_corto}", delta_color="inverse", border=True)
col3.metric(f"Resuelto por Impugnar ({pct_impug:.1f}%)", f"{int(ultimo_mes['Impugnacion']):,}", f"{int(ultimo_mes['Impugnacion'] - penultimo_mes['Impugnacion']):+,} vs {txt_pen_corto}", delta_color="inverse", border=True)
col4.metric(f"Producción Acum. (Ene - {txt_ult_corto})", f"{prod_acum_actual:,}", f"{MESES_CORTO[fecha_ult.month]}: {int(ultimo_mes['Produccion']):,} | Prom: {prom_prod_actual:,.0f}/mes", border=True)

st.markdown("---")
tab1, tab2 = st.tabs(["📈 Proyecciones y Tendencias", "📊 Análisis Descriptivo y Ranking"])

layout_movil = dict(
    hovermode="x unified",
    margin=dict(l=10, r=10, t=45, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
)
config_plotly = {"displayModeBar": False}

with tab1:
    def generar_proyeccion(serie, pasos):
        try:
            pred = ExponentialSmoothing(serie, trend='add', damped_trend=True, seasonal='add', seasonal_periods=12).fit().forecast(pasos)
        except:
            pred = ExponentialSmoothing(serie, trend='add', damped_trend=True).fit().forecast(pasos)
        return np.maximum(0, np.round(pred)).astype(int)

    fechas_futuras = pd.date_range(start=df_filtrado['Fecha'].max() + pd.DateOffset(months=1), periods=meses_proyeccion, freq='MS')
    proy_carga = generar_proyeccion(df_filtrado['Carga_Total'].values, meses_proyeccion)
    proy_prod = generar_proyeccion(df_filtrado['Produccion'].values, meses_proyeccion)

    col_izq, col_der = st.columns(2)
    with col_izq:
        st.subheader("📈 Proyección de Carga Total Activa")
        fig_carga = go.Figure()
        fig_carga.add_trace(go.Scatter(x=df_filtrado['Fecha'], y=df_filtrado['Carga_Total'], mode='lines+markers', name='Carga Total Real', line=dict(color='#38bdf8', width=3)))
        fig_carga.add_trace(go.Scatter(x=[df_filtrado['Fecha'].iloc[-1]] + list(fechas_futuras), y=[df_filtrado['Carga_Total'].iloc[-1]] + list(proy_carga), mode='lines+markers', name='Proyección Estimada', line=dict(color='#f59e0b', width=3, dash='dash')))
        fig_carga.update_layout(height=360, **layout_movil)
        st.plotly_chart(fig_carga, use_container_width=True, config=config_plotly, key="graf_carga")

    with col_der:
        st.subheader("📊 Composición de la Carga (Trámite vs Impugnación)")
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(x=df_filtrado['Fecha'], y=df_filtrado['Tramite'], name='En Trámite', marker_color='#0284c7'))
        fig_comp.add_trace(go.Bar(x=df_filtrado['Fecha'], y=df_filtrado['Impugnacion'], name='Resuelto por Impugnar', marker_color='#f97316'))
        fig_comp.update_layout(barmode='stack', height=360, **layout_movil)
        st.plotly_chart(fig_comp, use_container_width=True, config=config_plotly, key="graf_comp")

    st.subheader("⚖️ Histórico y Proyección de Producción de Resoluciones")
    fig_prod = go.Figure()
    fig_prod.add_trace(go.Bar(x=df_filtrado['Fecha'], y=df_filtrado['Produccion'], name='Resoluciones Emitidas (Real)', marker_color='#10b981'))
    fig_prod.add_trace(go.Scatter(x=fechas_futuras, y=proy_prod, mode='lines+markers', name='Proyección Estimada', line=dict(color='#f43f5e', width=3, dash='dot')))
    fig_prod.update_layout(height=340, **layout_movil)
    st.plotly_chart(fig_prod, use_container_width=True, config=config_plotly, key="graf_prod")

    st.subheader("📋 Tabla de Estimaciones Mensuales")
    df_tabla_proy = pd.DataFrame({'Mes Proyectado': fechas_futuras.strftime('%Y-%m'), 'Carga Total Estimada': proy_carga, 'Producción Estimada (Resoluciones)': proy_prod})
    st.dataframe(df_tabla_proy, use_container_width=True, hide_index=True)

    st.info("ℹ️ **Técnica Estadística de Proyección:** Se utiliza el modelo de series de tiempo **Suavizamiento Exponencial de Holt-Winters con Tendencia Amortiguada** (ciclo estacional de 12 meses). Esta metodología analiza el historial mensual desde enero de 2023 otorgando mayor peso al desempeño reciente de cada sede e incorporando las variaciones habituales de cada época del año (como periodos vacacionales o cierres anuales) para estimar el escenario esperado manteniendo las condiciones operativas actuales.")
with tab2:
    col_titulo, col_filtro = st.columns(2)
    anio_min, anio_max = int(df['Anio'].min()), int(df['Anio'].max())
    etiqueta_todos = f"TODOS ({anio_min} - {anio_max})"

    with col_titulo:
        st.subheader(f"📑 Estadísticas Históricas — {sede_seleccionada}")
    with col_filtro:
        anios_disponibles = [etiqueta_todos] + sorted(df['Anio'].unique().tolist())
        anio_sel = st.selectbox("Filtrar análisis descriptivo por Año:", anios_disponibles)

    if anio_sel == etiqueta_todos:
        df_desc = df_filtrado.copy()
        df_sedes_periodo = df.copy()
        fecha_corte_rank = df['Fecha'].max()
    else:
        df_desc = df_filtrado[df_filtrado['Anio'] == anio_sel].copy()
        df_sedes_periodo = df[df['Anio'] == anio_sel].copy()
        fecha_corte_rank = df_sedes_periodo['Fecha'].max()

    texto_corte = formato_fecha_es(fecha_corte_rank, corto=False)
    etiqueta_cierre = f"Carga Cierre ({formato_fecha_es(fecha_corte_rank, corto=True)})"
    fila_cierre = df_desc.iloc[-1]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(etiqueta_cierre, f"{int(fila_cierre['Carga_Total']):,}", f"Trám: {int(fila_cierre['Tramite']):,} | Imp: {int(fila_cierre['Impugnacion']):,}", border=True)
    c2.metric("Prom. Mensual Carga", f"{df_desc['Carga_Total'].mean():,.0f}", border=True)
    c3.metric("Prom. En Trámite", f"{df_desc['Tramite'].mean():,.0f}", border=True)
    c4.metric("Prom. Por Impugnar", f"{df_desc['Impugnacion'].mean():,.0f}", border=True)
    c5.metric(f"Producción Total ({anio_sel})", f"{int(df_desc['Produccion'].sum()):,}", f"Prom: {df_desc['Produccion'].mean():,.0f}/mes", border=True)

    if anio_sel != etiqueta_todos:
        st.subheader(f"📆 Evolución Mensual Detallada — Año {anio_sel}")
        fechas_es_mes = [formato_fecha_es(f, corto=False) for f in df_desc['Fecha']]
        texto_hover_mes = [
            f"<b>{f_es}</b><br>"
            f"🔵 En Trámite: <b>{t:,}</b><br>"
            f"🟠 Resuelto por Impugnar: <b>{i:,}</b><br>"
            f"📊 Carga Total Activa: <b>{tot:,}</b><br>"
            f"🟢 Producción (Resoluciones): <b>{p:,}</b>"
            for f_es, t, i, tot, p in zip(fechas_es_mes, df_desc['Tramite'], df_desc['Impugnacion'], df_desc['Carga_Total'], df_desc['Produccion'])
        ]
        fig_mes = go.Figure()
        fig_mes.add_trace(go.Bar(x=df_desc['Fecha'].dt.strftime('%Y-%m'), y=df_desc['Tramite'], name='En Trámite', marker_color='#0284c7', hovertext=texto_hover_mes, hovertemplate="%{hovertext}<extra></extra>"))
        fig_mes.add_trace(go.Bar(x=df_desc['Fecha'].dt.strftime('%Y-%m'), y=df_desc['Impugnacion'], name='Resuelto por Impugnar', marker_color='#f97316', hovertext=texto_hover_mes, hovertemplate="%{hovertext}<extra></extra>"))
        fig_mes.add_trace(go.Scatter(x=df_desc['Fecha'].dt.strftime('%Y-%m'), y=df_desc['Produccion'], mode='lines+markers', name='Producción (Resoluciones)', line=dict(color='#10b981', width=3), hovertext=texto_hover_mes, hovertemplate="%{hovertext}<extra></extra>"))
        fig_mes.update_layout(barmode='stack', height=380, **layout_movil)
        fig_mes.update_layout(hovermode="closest", hoverlabel=dict(bgcolor="#1e293b", font_size=13, font_color="white", bordercolor="#f59e0b"))
        st.plotly_chart(fig_mes, use_container_width=True, config=config_plotly, key="graf_mensual")

    st.subheader("📅 Resumen Comparativo Anual")
    resumen_anual = df_filtrado.groupby('Anio').agg(
        Meses=('Fecha', 'count'),
        Carga_Cierre=('Carga_Total', 'last'),
        Prom_Carga=('Carga_Total', 'mean'),
        Prom_Tramite=('Tramite', 'mean'),
        Prom_Impug=('Impugnacion', 'mean'),
        Prom_Prod=('Produccion', 'mean'),
        Total_Prod=('Produccion', 'sum')
    ).reset_index()
    resumen_anual['Anio'] = resumen_anual['Anio'].astype(str)
    for col in ['Carga_Cierre', 'Prom_Carga', 'Prom_Tramite', 'Prom_Impug', 'Prom_Prod', 'Total_Prod']:
        resumen_anual[col] = resumen_anual[col].round(0).astype(int)
    resumen_anual.columns = ['Año', 'Meses', 'Carga al Cierre', 'Prom. Carga Total', 'Prom. En Trámite', 'Prom. Por Impugnar', 'Prom. Producción/Mes', 'Total Resoluciones Emitidas']
    st.dataframe(resumen_anual, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader(f"🏆 Ranking 1: Carga Activa a Nivel Nacional (Cierre: {texto_corte})")
    df_ranking = df[df['Fecha'] == fecha_corte_rank].sort_values('Carga_Total', ascending=True)
    colores_tram = ['#f59e0b' if s == sede_seleccionada else '#0284c7' for s in df_ranking['Sede']]
    colores_imp = ['#fbbf24' if s == sede_seleccionada else '#f97316' for s in df_ranking['Sede']]

    fig_rank = go.Figure()
    texto_hover = [
        f"<b>{s}</b><br>"
        f"🔵 En Trámite: <b>{t:,}</b><br>"
        f"🟠 Resuelto por Impugnar: <b>{i:,}</b><br>"
        f"📊 Carga Total Activa: <b>{tot:,}</b>"
        for s, t, i, tot in zip(df_ranking['Sede'], df_ranking['Tramite'], df_ranking['Impugnacion'], df_ranking['Carga_Total'])
    ]
    fig_rank.add_trace(go.Bar(y=df_ranking['Sede'], x=df_ranking['Tramite'], name='En Trámite', orientation='h', marker_color=colores_tram, hovertext=texto_hover, hovertemplate="%{hovertext}<extra></extra>"))
    fig_rank.add_trace(go.Bar(y=df_ranking['Sede'], x=df_ranking['Impugnacion'], name='Resuelto por Impugnar', orientation='h', marker_color=colores_imp, hovertext=texto_hover, hovertemplate="%{hovertext}<extra></extra>"))
    fig_rank.add_trace(go.Scatter(y=df_ranking['Sede'], x=df_ranking['Carga_Total'], text=df_ranking['Carga_Total'].apply(lambda x: f"  {x:,}"), mode='text', textposition='middle right', showlegend=False, hoverinfo='skip'))
    fig_rank.update_layout(barmode='stack', height=720, xaxis_title="Cantidad de Expedientes", xaxis_range=[0, df_ranking['Carga_Total'].max() * 1.12], **layout_movil)
    fig_rank.update_layout(hovermode="closest", hoverlabel=dict(bgcolor="#1e293b", font_size=13, font_color="white", bordercolor="#f59e0b"))
    st.plotly_chart(fig_rank, use_container_width=True, config=config_plotly, key="graf_rank_carga")

    st.markdown("---")
    st.subheader(f"⚖️ Ranking 2: Producción Global a Nivel Nacional ({anio_sel})")
    df_rank_prod = df_sedes_periodo.groupby('Sede')['Produccion'].sum().reset_index().sort_values('Produccion', ascending=False)
    colores_prod = ['#f59e0b' if s == sede_seleccionada else '#10b981' for s in df_rank_prod['Sede']]

    fig_prod_rank = go.Figure()
    fig_prod_rank.add_trace(go.Bar(x=df_rank_prod['Sede'], y=df_rank_prod['Produccion'], text=df_rank_prod['Produccion'].apply(lambda x: f"{x:,}"), textposition='outside', marker_color=colores_prod, name='Resoluciones Emitidas'))
    fig_prod_rank.update_layout(height=480, yaxis_title="Total Resoluciones", xaxis_tickangle=-45, margin=dict(l=10, r=10, t=35, b=110), showlegend=False)
    st.plotly_chart(fig_prod_rank, use_container_width=True, config=config_plotly, key="graf_rank_prod")










