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
    <h2 style="color: white; margin: 0;">⚖️ Autoridad Nacional de Control del Poder Judicial</h2>
    <p style="color: #e2e8f0; margin: 4px 0 0 0; font-size: 14px;">Dashboard de Análisis Estadístico, Control de Carga y Proyecciones — Unidad de Inteligencia y Análisis (UIA)</p>
</div>
""", unsafe_allow_html=True)

@st.cache_data
def cargar_datos():
    df = pd.read_excel("data_consolidada_anc.xlsx", sheet_name="Consolidado_ANC")
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df['Anio'] = df['Fecha'].dt.year
    return df

df = cargar_datos()

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
pct_tramite = (ultimo_mes['Tramite'] / ultimo_mes['Carga_Total'] * 100) if ultimo_mes['Carga_Total'] > 0 else 0
pct_impug = (ultimo_mes['Impugnacion'] / ultimo_mes['Carga_Total'] * 100) if ultimo_mes['Carga_Total'] > 0 else 0

df_2026 = df_filtrado[df_filtrado['Anio'] == 2026]
prod_acum_2026 = int(df_2026['Produccion'].sum())
prom_prod_2026 = df_2026['Produccion'].mean()

st.subheader(f"📌 Situación Actual al Cierre de Octubre 2026 — {sede_seleccionada}")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Carga Total Activa (Inventario)", f"{int(ultimo_mes['Carga_Total']):,}", f"{int(ultimo_mes['Carga_Total'] - penultimo_mes['Carga_Total']):+,} vs Sep 2026", delta_color="inverse", border=True)
col2.metric(f"En Trámite ({pct_tramite:.1f}%)", f"{int(ultimo_mes['Tramite']):,}", f"{int(ultimo_mes['Tramite'] - penultimo_mes['Tramite']):+,} vs Sep 2026", delta_color="inverse", border=True)
col3.metric(f"Resuelto por Impugnar ({pct_impug:.1f}%)", f"{int(ultimo_mes['Impugnacion']):,}", f"{int(ultimo_mes['Impugnacion'] - penultimo_mes['Impugnacion']):+,} vs Sep 2026", delta_color="inverse", border=True)
col4.metric("Producción Acum. (Ene - Oct 2026)", f"{prod_acum_2026:,}", f"Oct: {int(ultimo_mes['Produccion']):,} | Prom: {prom_prod_2026:,.0f}/mes", border=True)

st.markdown("---")
tab1, tab2 = st.tabs(["📈 Proyecciones y Tendencias", "📊 Análisis Descriptivo y Ranking"])

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
        fig_carga.update_layout(height=400, hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_carga, use_container_width=True)

    with col_der:
        st.subheader("📊 Composición de la Carga (Trámite vs Impugnación)")
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(x=df_filtrado['Fecha'], y=df_filtrado['Tramite'], name='En Trámite', marker_color='#0284c7'))
        fig_comp.add_trace(go.Bar(x=df_filtrado['Fecha'], y=df_filtrado['Impugnacion'], name='Resuelto por Impugnar', marker_color='#f97316'))
        fig_comp.update_layout(barmode='stack', height=400, hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_comp, use_container_width=True)

    st.subheader("⚖️ Histórico y Proyección de Producción de Resoluciones")
    fig_prod = go.Figure()
    fig_prod.add_trace(go.Bar(x=df_filtrado['Fecha'], y=df_filtrado['Produccion'], name='Resoluciones Emitidas (Real)', marker_color='#10b981'))
    fig_prod.add_trace(go.Scatter(x=fechas_futuras, y=proy_prod, mode='lines+markers', name='Proyección Estimada', line=dict(color='#f43f5e', width=3, dash='dot')))
    fig_prod.update_layout(height=350, hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig_prod, use_container_width=True)

    st.subheader("📋 Tabla de Estimaciones Mensuales")
    df_tabla_proy = pd.DataFrame({
        'Mes Proyectado': fechas_futuras.strftime('%Y-%m'),
        'Carga Total Estimada': proy_carga,
        'Producción Estimada (Resoluciones)': proy_prod
    })
    st.dataframe(df_tabla_proy, use_container_width=True, hide_index=True)

    st.info("ℹ️ **Técnica Estadística de Proyección:** Se utiliza el modelo de series de tiempo **Suavizamiento Exponencial de Holt-Winters con Tendencia Amortiguada** (ciclo estacional de 12 meses). Esta metodología analiza el historial mensual desde enero de 2023 otorgando mayor peso al desempeño reciente de cada sede e incorporando las variaciones habituales de cada época del año (como periodos vacacionales o cierres anuales) para estimar el escenario esperado manteniendo las condiciones operativas actuales.")

with tab2:
    col_titulo, col_filtro = st.columns(2)
    with col_titulo:
        st.subheader(f"📑 Estadísticas Históricas — {sede_seleccionada}")
    with col_filtro:
        anios_disponibles = ["TODOS (2023 - 2026)"] + sorted(df['Anio'].unique().tolist())
        anio_sel = st.selectbox("Filtrar análisis descriptivo por Año:", anios_disponibles)

    if anio_sel == "TODOS (2023 - 2026)":
        df_desc = df_filtrado.copy()
        fecha_corte_rank = df['Fecha'].max()
        texto_corte = "Octubre 2026"
    else:
        df_desc = df_filtrado[df_filtrado['Anio'] == anio_sel].copy()
        fecha_corte_rank = df[df['Anio'] == anio_sel]['Fecha'].max()
        texto_corte = fecha_corte_rank.strftime('%B %Y').capitalize()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Prom. Carga ({anio_sel})", f"{df_desc['Carga_Total'].mean():,.0f}", border=True)
    c2.metric("Prom. En Trámite", f"{df_desc['Tramite'].mean():,.0f}", border=True)
    c3.metric("Prom. Por Impugnar", f"{df_desc['Impugnacion'].mean():,.0f}", border=True)
    c4.metric(f"Producción Total ({anio_sel})", f"{int(df_desc['Produccion'].sum()):,}", f"Prom: {df_desc['Produccion'].mean():,.0f}/mes", border=True)

    if anio_sel != "TODOS (2023 - 2026)":
        st.subheader(f"📆 Evolución Mensual Detallada — Año {anio_sel}")
        fig_mes = go.Figure()
        fig_mes.add_trace(go.Bar(x=df_desc['Fecha'].dt.strftime('%Y-%m'), y=df_desc['Tramite'], name='En Trámite', marker_color='#0284c7'))
        fig_mes.add_trace(go.Bar(x=df_desc['Fecha'].dt.strftime('%Y-%m'), y=df_desc['Impugnacion'], name='Resuelto por Impugnar', marker_color='#f97316'))
        fig_mes.add_trace(go.Scatter(x=df_desc['Fecha'].dt.strftime('%Y-%m'), y=df_desc['Produccion'], mode='lines+markers', name='Producción (Resoluciones)', line=dict(color='#10b981', width=3)))
        fig_mes.update_layout(barmode='stack', height=380, hovermode="x unified", margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_mes, use_container_width=True)

    st.subheader("📅 Resumen Comparativo Anual")
    resumen_anual = df_filtrado.groupby('Anio').agg(Meses=('Fecha', 'count'), Prom_Carga=('Carga_Total', 'mean'), Prom_Tramite=('Tramite', 'mean'), Prom_Impug=('Impugnacion', 'mean'), Prom_Prod=('Produccion', 'mean'), Total_Prod=('Produccion', 'sum')).reset_index()
    resumen_anual['Anio'] = resumen_anual['Anio'].astype(str)
    for col in ['Prom_Carga', 'Prom_Tramite', 'Prom_Impug', 'Prom_Prod', 'Total_Prod']:
        resumen_anual[col] = resumen_anual[col].round(0).astype(int)
    resumen_anual.columns = ['Año', 'Meses', 'Prom. Carga Total', 'Prom. En Trámite', 'Prom. Por Impugnar', 'Prom. Producción/Mes', 'Total Resoluciones Emitidas']
    st.dataframe(resumen_anual, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader(f"🏆 Ranking Nacional de Carga Activa por ODANC (Cierre: {texto_corte})")
    df_ranking = df[df['Fecha'] == fecha_corte_rank].sort_values('Carga_Total', ascending=True)
    fig_rank = go.Figure()
    fig_rank.add_trace(go.Bar(y=df_ranking['Sede'], x=df_ranking['Tramite'], name='En Trámite', orientation='h', marker_color='#0284c7'))
    fig_rank.add_trace(go.Bar(y=df_ranking['Sede'], x=df_ranking['Impugnacion'], name='Resuelto por Impugnar', orientation='h', marker_color='#f97316'))


