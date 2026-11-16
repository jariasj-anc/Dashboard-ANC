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
    def generar_proyeccion_avanzada(serie, pasos):
        try:
            modelo = ExponentialSmoothing(serie, trend='add', damped_trend=True, seasonal='add', seasonal_periods=12).fit()
        except:
            modelo = ExponentialSmoothing(serie, trend='add', damped_trend=True).fit()
        
        pred = modelo.forecast(pasos)
        ajustados = modelo.fittedvalues
        residuos = serie - ajustados
        sigma = np.std(residuos, ddof=1)
        margen = 1.96 * sigma * np.sqrt(np.arange(1, pasos + 1) * 0.35 + 0.65)
        
        mask = serie > 0
        mape = np.mean(np.abs((serie[mask] - ajustados[mask]) / serie[mask])) * 100 if np.any(mask) else 0.0
        precision = max(0.0, 100.0 - mape)
        
        est = np.maximum(0, np.round(pred)).astype(int)
        lim_inf = np.maximum(0, np.round(pred - margen)).astype(int)
        lim_sup = np.maximum(0, np.round(pred + margen)).astype(int)
        return est, lim_inf, lim_sup, precision, mape

    fechas_futuras = pd.date_range(start=df_filtrado['Fecha'].max() + pd.DateOffset(months=1), periods=meses_proyeccion, freq='MS')
    proy_carga, carga_inf, carga_sup, prec_carga, mape_carga = generar_proyeccion_avanzada(df_filtrado['Carga_Total'].values, meses_proyeccion)
    proy_prod, prod_inf, prod_sup, prec_prod, mape_prod = generar_proyeccion_avanzada(df_filtrado['Produccion'].values, meses_proyeccion)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Precisión Modelo — Carga Activa", f"{prec_carga:.1f}%", f"Margen error medio: {mape_carga:.1f}%", border=True)
    var_proy_fin = proy_carga[-1] - int(ultimo_mes['Carga_Total'])
    m2.metric(f"Carga Activa Est. ({formato_fecha_es(fechas_futuras[-1], corto=True)})", f"{proy_carga[-1]:,} exp.", f"{var_proy_fin:+,} exp. vs hoy", delta_color="inverse", border=True)
    
    m3.metric("Precisión Modelo — Producción", f"{prec_prod:.1f}%", f"Margen error medio: {mape_prod:.1f}%", border=True)
    total_proy_prod = int(np.sum(proy_prod))
    prom_proy_prod = np.mean(proy_prod)
    m4.metric(f"Producción Est. ({meses_proyeccion} meses)", f"{total_proy_prod:,} prod.", f"Prom: {prom_proy_prod:,.0f} prod./mes", border=True)

    estilo_hover = dict(bgcolor="#1e293b", font_size=13, font_color="white", bordercolor="#f59e0b")
    fechas_hist_es = [formato_fecha_es(f, corto=False) for f in df_filtrado['Fecha']]
    fechas_fut_es = [formato_fecha_es(f, corto=False) for f in fechas_futuras]

    col_izq, col_der = st.columns(2)
    with col_izq:
        st.subheader("📈 Proyección de Carga Total Activa")
        fig_carga = go.Figure()
        x_banda = list(fechas_futuras) + list(fechas_futuras)[::-1]
        y_banda_carga = list(carga_sup) + list(carga_inf)[::-1]
        fig_carga.add_trace(go.Scatter(x=x_banda, y=y_banda_carga, fill='toself', fillcolor='rgba(245, 158, 11, 0.18)', line=dict(color='rgba(255,255,255,0)'), name='Rango Esperado (95%)', hoverinfo='skip'))
        
        hover_carga_real = [f"<b>{f_es}</b><br>🔵 Carga Total Real: <b>{int(c):,}</b>" for f_es, c in zip(fechas_hist_es, df_filtrado['Carga_Total'])]
        fig_carga.add_trace(go.Scatter(x=df_filtrado['Fecha'], y=df_filtrado['Carga_Total'], mode='lines+markers', name='Carga Total Real', line=dict(color='#38bdf8', width=3), hovertext=hover_carga_real, hovertemplate="%{hovertext}<extra></extra>"))
        
        hover_carga_proy = [f"<b>{fechas_hist_es[-1]} (Cierre Real)</b><br>🔵 Carga Total: <b>{int(df_filtrado['Carga_Total'].iloc[-1]):,}</b>"] + [
            f"<b>{f_es} (Proyectado)</b><br>🟡 Proyección Central: <b>{c:,}</b><br>📐 Rango (95%): <b>{inf:,} — {sup:,}</b>"
            for f_es, c, inf, sup in zip(fechas_fut_es, proy_carga, carga_inf, carga_sup)
        ]
        fig_carga.add_trace(go.Scatter(x=[df_filtrado['Fecha'].iloc[-1]] + list(fechas_futuras), y=[df_filtrado['Carga_Total'].iloc[-1]] + list(proy_carga), mode='lines+markers', name='Proyección Central', line=dict(color='#f59e0b', width=3, dash='dash'), hovertext=hover_carga_proy, hovertemplate="%{hovertext}<extra></extra>"))
        fig_carga.update_layout(height=360, **layout_movil)
        fig_carga.update_layout(hovermode="closest", hoverlabel=estilo_hover)
        st.plotly_chart(fig_carga, use_container_width=True, config=config_plotly, key="graf_carga")

    with col_der:
        st.subheader("📊 Composición de la Carga (Trámite vs Impugnación)")
        hover_comp = []
        for f_es, t, i, tot in zip(fechas_hist_es, df_filtrado['Tramite'], df_filtrado['Impugnacion'], df_filtrado['Carga_Total']):
            pt = (t / tot * 100) if tot > 0 else 0
            pi = (i / tot * 100) if tot > 0 else 0
            hover_comp.append(
                f"<b>{f_es}</b><br>"
                f"🔵 En Trámite: <b>{int(t):,} ({pt:.1f}%)</b><br>"
                f"🟠 Resuelto por Impugnar: <b>{int(i):,} ({pi:.1f}%)</b><br>"
                f"📊 Carga Total Activa: <b>{int(tot):,}</b>"
            )
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(x=df_filtrado['Fecha'], y=df_filtrado['Tramite'], name='En Trámite', marker_color='#0284c7', hovertext=hover_comp, hovertemplate="%{hovertext}<extra></extra>"))
        fig_comp.add_trace(go.Bar(x=df_filtrado['Fecha'], y=df_filtrado['Impugnacion'], name='Resuelto por Impugnar', marker_color='#f97316', hovertext=hover_comp, hovertemplate="%{hovertext}<extra></extra>"))
        fig_comp.update_layout(barmode='stack', height=360, **layout_movil)
        fig_comp.update_layout(hovermode="closest", hoverlabel=estilo_hover)
        st.plotly_chart(fig_comp, use_container_width=True, config=config_plotly, key="graf_comp")

    st.subheader("⚖️ Histórico y Proyección de Producción")
    fig_prod = go.Figure()
    y_banda_prod = list(prod_sup) + list(prod_inf)[::-1]
    fig_prod.add_trace(go.Scatter(x=x_banda, y=y_banda_prod, fill='toself', fillcolor='rgba(244, 63, 94, 0.16)', line=dict(color='rgba(255,255,255,0)'), name='Rango Esperado (95%)', hoverinfo='skip'))
    
    hover_prod_real = [f"<b>{f_es}</b><br>🟢 Producción (Real): <b>{int(p):,}</b>" for f_es, p in zip(fechas_hist_es, df_filtrado['Produccion'])]
    fig_prod.add_trace(go.Bar(x=df_filtrado['Fecha'], y=df_filtrado['Produccion'], name='Producción (Real)', marker_color='#10b981', hovertext=hover_prod_real, hovertemplate="%{hovertext}<extra></extra>"))
    
    hover_prod_proy = [
        f"<b>{f_es} (Proyectado)</b><br>🔴 Proyección Central: <b>{p:,}</b><br>📐 Rango (95%): <b>{inf:,} — {sup:,}</b>"
        for f_es, p, inf, sup in zip(fechas_fut_es, proy_prod, prod_inf, prod_sup)
    ]
    fig_prod.add_trace(go.Scatter(x=fechas_futuras, y=proy_prod, mode='lines+markers', name='Proyección Central', line=dict(color='#f43f5e', width=3, dash='dot'), hovertext=hover_prod_proy, hovertemplate="%{hovertext}<extra></extra>"))
    fig_prod.update_layout(height=340, **layout_movil)
    fig_prod.update_layout(hovermode="closest", hoverlabel=estilo_hover)
    st.plotly_chart(fig_prod, use_container_width=True, config=config_plotly, key="graf_prod")


    st.subheader("📋 Tabla de Estimaciones Mensuales e Intervalos de Confianza (95%)")
    df_tabla_proy = pd.DataFrame({
        'Mes Proyectado': [formato_fecha_es(f, corto=False) for f in fechas_futuras],
        'Carga Estimada (Central)': [f"{x:,}" for x in proy_carga],
        'Rango Carga Esperada (95%)': [f"{inf:,}  —  {sup:,}" for inf, sup in zip(carga_inf, carga_sup)],
        'Producción Estimada (Central)': [f"{x:,}" for x in proy_prod],
        'Rango Producción Esperada (95%)': [f"{inf:,}  —  {sup:,}" for inf, sup in zip(prod_inf, prod_sup)]
    })
    st.dataframe(df_tabla_proy, use_container_width=True, hide_index=True)

    st.info("ℹ️ **Técnica Estadística de Proyección:** Se utiliza el modelo de series de tiempo **Suavizamiento Exponencial de Holt-Winters con Tendencia Amortiguada** (ciclo estacional de 12 meses), complementado con intervalos de confianza al 95% y evaluación de ajuste histórico para estimar el escenario esperado manteniendo las condiciones operativas actuales.")
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
            f"<b>{f_es}</b><br>🔵 En Trámite: <b>{t:,}</b><br>🟠 Resuelto por Impugnar: <b>{i:,}</b><br>📊 Carga Total Activa: <b>{tot:,}</b><br>🟢 Producción: <b>{p:,}</b>"
            for f_es, t, i, tot, p in zip(fechas_es_mes, df_desc['Tramite'], df_desc['Impugnacion'], df_desc['Carga_Total'], df_desc['Produccion'])
        ]
        fig_mes = go.Figure()
        fig_mes.add_trace(go.Bar(x=df_desc['Fecha'].dt.strftime('%Y-%m'), y=df_desc['Tramite'], name='En Trámite', marker_color='#0284c7', hovertext=texto_hover_mes, hovertemplate="%{hovertext}<extra></extra>"))
        fig_mes.add_trace(go.Bar(x=df_desc['Fecha'].dt.strftime('%Y-%m'), y=df_desc['Impugnacion'], name='Resuelto por Impugnar', marker_color='#f97316', hovertext=texto_hover_mes, hovertemplate="%{hovertext}<extra></extra>"))
        fig_mes.add_trace(go.Scatter(x=df_desc['Fecha'].dt.strftime('%Y-%m'), y=df_desc['Produccion'], mode='lines+markers', name='Producción', line=dict(color='#10b981', width=3), hovertext=texto_hover_mes, hovertemplate="%{hovertext}<extra></extra>"))
        fig_mes.update_layout(barmode='stack', height=380, **layout_movil)
        fig_mes.update_layout(hovermode="closest", hoverlabel=dict(bgcolor="#1e293b", font_size=13, font_color="white", bordercolor="#f59e0b"))
        st.plotly_chart(fig_mes, use_container_width=True, config=config_plotly, key="graf_mensual")

    st.subheader("📅 Resumen Comparativo Anual")
    resumen_anual = df_filtrado.groupby('Anio').agg(Meses=('Fecha', 'count'), Carga_Cierre=('Carga_Total', 'last'), Prom_Carga=('Carga_Total', 'mean'), Prom_Tramite=('Tramite', 'mean'), Prom_Impug=('Impugnacion', 'mean'), Prom_Prod=('Produccion', 'mean'), Total_Prod=('Produccion', 'sum')).reset_index()
    resumen_anual['Anio'] = resumen_anual['Anio'].astype(str)
    for col in ['Carga_Cierre', 'Prom_Carga', 'Prom_Tramite', 'Prom_Impug', 'Prom_Prod', 'Total_Prod']:
        resumen_anual[col] = resumen_anual[col].round(0).astype(int)
    resumen_anual.columns = ['Año', 'Meses', 'Carga al Cierre', 'Prom. Carga Total', 'Prom. En Trámite', 'Prom. Por Impugnar', 'Prom. Producción/Mes', 'Total Producción']
    st.dataframe(resumen_anual, use_container_width=True, hide_index=True)

    st.subheader(f"📐 Indicadores Estadísticos de Dispersión y Posición ({anio_sel})")
    variables_est = [('Carga_Total', 'Carga Total Activa'), ('Tramite', 'Expedientes En Trámite'), ('Impugnacion', 'Resuelto por Impugnar'), ('Produccion', 'Producción')]
    filas_est = []
    stats_dict = {}
    for col_var, nombre_var in variables_est:
        serie = df_desc[col_var]
        media, mediana = serie.mean(), serie.median()
        desv = serie.std(ddof=1) if len(serie) > 1 else 0.0
        cv = (desv / media * 100) if media > 0 else 0.0
        idx_min, idx_max = serie.idxmin(), serie.idxmax()
        val_min, val_max = int(serie.loc[idx_min]), int(serie.loc[idx_max])
        mes_min, mes_max = formato_fecha_es(df_desc.loc[idx_min, 'Fecha'], corto=True), formato_fecha_es(df_desc.loc[idx_max, 'Fecha'], corto=True)
        stats_dict[col_var] = {'mediana': mediana, 'desv': desv, 'cv': cv, 'min': f"{val_min:,} ({mes_min})", 'max': f"{val_max:,} ({mes_max})"}
        filas_est.append({'Indicador Evaluado': nombre_var, 'Promedio (Media)': f"{media:,.0f}", 'Mediana (Mes Típico)': f"{mediana:,.0f}", 'Desviación Estándar': f"{desv:,.0f}", 'Coef. Variación (CV)': f"{cv:.1f}%", 'Mínimo Registrado': f"{val_min:,} ({mes_min})", 'Máximo Registrado': f"{val_max:,} ({mes_max})"})
    st.dataframe(pd.DataFrame(filas_est), use_container_width=True, hide_index=True)

    st.caption(
        "ℹ️ **Criterio de Lectura del Coeficiente de Variación (CV):** "
        "**< 20% (Estabilidad Alta):** Ritmo muy parejo y constante sin sobresaltos | "
        "**20% a 35% (Variabilidad Moderada):** Fluctuaciones normales por el calendario judicial | "
        "**> 35% (Fluctuación Alta):** Ritmo irregular con picos fuertes y meses bajos."
    )

    carga_ini = int(next(iter(df_desc['Carga_Total'])))
    carga_fin = int(fila_cierre['Carga_Total'])
    var_carga = carga_fin - carga_ini
    pct_var_carga = (var_carga / carga_ini * 100) if carga_ini > 0 else 0.0
    texto_tendencia = f"una **reducción neta de {var_carga:,} expedientes ({pct_var_carga:.1f}%)**" if var_carga < 0 else (f"un **incremento neto de +{var_carga:,} expedientes (+{pct_var_carga:.1f}%)**" if var_carga > 0 else "una **variación neta nula (0%)**")

    media_carga = df_desc['Carga_Total'].mean()
    desv_carga, cv_carga = stats_dict['Carga_Total']['desv'], stats_dict['Carga_Total']['cv']
    rango_carga_inf = max(0, int(round(media_carga - desv_carga)))
    rango_carga_sup = int(round(media_carga + desv_carga))
    if cv_carga < 20:
        frase_cv_carga = f"es decir, el volumen apenas varía un **{cv_carga:.1f}% de un mes a otro**, demostrando **una gestión muy estable y sin sobresaltos**"
    elif cv_carga <= 35:
        frase_cv_carga = f"es decir, el volumen varía moderadamente en un **{cv_carga:.1f}% de un mes a otro**, reflejando **fluctuaciones normales del movimiento procesal**"
    else:
        frase_cv_carga = f"es decir, el volumen varía hasta en un **{cv_carga:.1f}% de un mes a otro**, evidenciando **cambios marcados en el inventario mensual**"

    media_prod = df_desc['Produccion'].mean()
    desv_prod, cv_prod = stats_dict['Produccion']['desv'], stats_dict['Produccion']['cv']
    rango_prod_inf = max(0, int(round(media_prod - desv_prod)))
    rango_prod_sup = int(round(media_prod + desv_prod))
    if cv_prod < 20:
        frase_cv_prod = f"es decir, la producción apenas varía un **{cv_prod:.1f}% de un mes a otro**, demostrando **un ritmo muy parejo y constante todo el año**"
    elif cv_prod <= 35:
        frase_cv_prod = f"es decir, la producción varía moderadamente en un **{cv_prod:.1f}% de un mes a otro**, mostrando **variaciones normales por el calendario judicial**"
    else:
        frase_cv_prod = f"es decir, la producción varía hasta en un **{cv_prod:.1f}% de un mes a otro**, evidenciando **un ritmo irregular con picos fuertes y meses bajos**"

    pct_tram_cierre = (fila_cierre['Tramite'] / carga_fin * 100) if carga_fin > 0 else 0.0
    pct_imp_cierre = (fila_cierre['Impugnacion'] / carga_fin * 100) if carga_fin > 0 else 0.0

    st.success(
        f"🔍 **Hallazgos Clave — {sede_seleccionada} ({anio_sel}):**\n\n"
        f"* **Evolución de la Carga Activa:** Entre el inicio y el cierre del periodo evaluado, la carga total registró {texto_tendencia}, cerrando en **{carga_fin:,} expedientes activos**. Sobre un promedio de **{media_carga:,.0f} expedientes**, lo habitual es que cada mes se mantenga entre **{rango_carga_inf:,} y {rango_carga_sup:,} expedientes**; {frase_cv_carga}.\n"
        f"* **Regularidad de la Producción:** Sobre un promedio de **{media_prod:,.0f} prod. por mes**, lo habitual es registrar entre **{rango_prod_inf:,} y {rango_prod_sup:,} prod. mensuales**; {frase_cv_prod}. Su rendimiento típico es de **{stats_dict['Produccion']['mediana']:,.0f} prod. por mes**, alcanzando su mayor nivel en **{stats_dict['Produccion']['max']}** y el más bajo en **{stats_dict['Produccion']['min']}**.\n"
        f"* **Composición al Cierre ({formato_fecha_es(fecha_corte_rank, corto=True)}):** Del inventario activo final, el **{pct_tram_cierre:.1f}%** corresponde a expedientes **En Trámite** y el **{pct_imp_cierre:.1f}%** a expedientes **Resueltos por Impugnar**."
    )

    st.markdown("---")
    st.subheader(f"🏆 Ranking 1: Carga Activa a Nivel Nacional (Cierre: {texto_corte})")
    df_ranking = df[df['Fecha'] == fecha_corte_rank].sort_values('Carga_Total', ascending=True)
    total_nac_carga = df_ranking['Carga_Total'].sum()
    df_ranking['Pct_Nac'] = (df_ranking['Carga_Total'] / total_nac_carga * 100) if total_nac_carga > 0 else 0.0

    colores_tram = ['#f59e0b' if s == sede_seleccionada else '#0284c7' for s in df_ranking['Sede']]
    colores_imp = ['#fbbf24' if s == sede_seleccionada else '#f97316' for s in df_ranking['Sede']]

    fig_rank = go.Figure()
    texto_hover = [f"<b>{s}</b><br>🔵 En Trámite: <b>{t:,}</b><br>🟠 Resuelto por Impugnar: <b>{i:,}</b><br>📊 Carga Total Activa: <b>{tot:,} ({pct:.1f}% nacional)</b>" for s, t, i, tot, pct in zip(df_ranking['Sede'], df_ranking['Tramite'], df_ranking['Impugnacion'], df_ranking['Carga_Total'], df_ranking['Pct_Nac'])]
    etiquetas_barra_carga = [f"  {tot:,} ({pct:.1f}%)" for tot, pct in zip(df_ranking['Carga_Total'], df_ranking['Pct_Nac'])]

    fig_rank.add_trace(go.Bar(y=df_ranking['Sede'], x=df_ranking['Tramite'], name='En Trámite', orientation='h', marker_color=colores_tram, hovertext=texto_hover, hovertemplate="%{hovertext}<extra></extra>"))
    fig_rank.add_trace(go.Bar(y=df_ranking['Sede'], x=df_ranking['Impugnacion'], name='Resuelto por Impugnar', orientation='h', marker_color=colores_imp, hovertext=texto_hover, hovertemplate="%{hovertext}<extra></extra>"))
    fig_rank.add_trace(go.Scatter(y=df_ranking['Sede'], x=df_ranking['Carga_Total'], text=etiquetas_barra_carga, mode='text', textposition='middle right', showlegend=False, hoverinfo='skip'))
    fig_rank.update_layout(barmode='stack', height=720, xaxis_title="Cantidad de Expedientes", xaxis_range=[0, df_ranking['Carga_Total'].max() * 1.18], **layout_movil)
    fig_rank.update_layout(hovermode="closest", hoverlabel=dict(bgcolor="#1e293b", font_size=13, font_color="white", bordercolor="#f59e0b"))
    st.plotly_chart(fig_rank, use_container_width=True, config=config_plotly, key="graf_rank_carga")

    st.markdown("---")
    st.subheader(f"⚖️ Ranking 2: Producción Global a Nivel Nacional ({anio_sel})")
    df_rank_prod = df_sedes_periodo.groupby('Sede')['Produccion'].sum().reset_index().sort_values('Produccion', ascending=False)
    total_nac_prod = df_rank_prod['Produccion'].sum()
    df_rank_prod['Pct_Nac'] = (df_rank_prod['Produccion'] / total_nac_prod * 100) if total_nac_prod > 0 else 0.0
    colores_prod = ['#f59e0b' if s == sede_seleccionada else '#10b981' for s in df_rank_prod['Sede']]

    texto_hover_prod = [f"<b>{s}</b><br>🟢 Producción: <b>{p:,}</b><br>📈 Participación Nacional: <b>{pct:.1f}%</b>" for s, p, pct in zip(df_rank_prod['Sede'], df_rank_prod['Produccion'], df_rank_prod['Pct_Nac'])]

    fig_prod_rank = go.Figure()
    fig_prod_rank.add_trace(go.Bar(
        x=df_rank_prod['Sede'],
        y=df_rank_prod['Produccion'],
        text=df_rank_prod['Produccion'].apply(lambda x: f"{x:,}"),
        textposition='outside',
        marker_color=colores_prod,
        name='Producción',
        hovertext=texto_hover_prod,
        hovertemplate="%{hovertext}<extra></extra>"
    ))
    fig_prod_rank.update_layout(height=460, yaxis_title="Total Producción", xaxis_tickangle=-45, margin=dict(l=10, r=10, t=35, b=110), showlegend=False)
    fig_prod_rank.update_layout(hovermode="closest", hoverlabel=dict(bgcolor="#1e293b", font_size=13, font_color="white", bordercolor="#f59e0b"))
    st.plotly_chart(fig_prod_rank, use_container_width=True, config=config_plotly, key="graf_rank_prod")
import io
from generador_pdf import construir_pdf_completo

nombre_sede_limpio = sede_seleccionada.replace(" ", "_").replace("(", "").replace(")", "").replace(".", "")

pdf_bytes = construir_pdf_completo(
    sede_seleccionada, txt_ult_largo, ultimo_mes, pct_tramite, pct_impug,
    anio_actual, prod_acum_actual, df_filtrado, fechas_futuras, proy_carga,
    carga_inf, carga_sup, proy_prod, prod_inf, prod_sup, prec_carga, prec_prod,
    anio_sel, fecha_corte_rank, fila_cierre, df_desc, resumen_anual, filas_est,
    carga_fin, media_carga, rango_carga_inf, rango_carga_sup, cv_carga,
    media_prod, rango_prod_inf, rango_prod_sup, cv_prod, stats_dict,
    pct_tram_cierre, pct_imp_cierre, df_ranking, texto_corte, df_rank_prod,
    formato_fecha_es
)

buffer_excel = io.BytesIO()
with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
    df_tabla_proy.to_excel(writer, sheet_name='Proyecciones_95', index=False)
    resumen_anual.to_excel(writer, sheet_name='Resumen_Anual', index=False)
    pd.DataFrame(filas_est).to_excel(writer, sheet_name='Indicadores_Estadisticos', index=False)
    df_ranking[['Sede', 'Tramite', 'Impugnacion', 'Carga_Total', 'Pct_Nac']].sort_values('Carga_Total', ascending=False).to_excel(writer, sheet_name='Ranking_Nacional_Carga', index=False)
    df_rank_prod[['Sede', 'Produccion', 'Pct_Nac']].to_excel(writer, sheet_name='Ranking_Nacional_Prod', index=False)

with st.sidebar:
    st.markdown("---")
    st.subheader("📥 Exportar Reportes")

    st.download_button(
        label="🖨️ Descargar Reporte en PDF",
        data=bytes(pdf_bytes) if pdf_bytes is not None else b"",
        file_name=f"Reporte_Ejecutivo_ANC_{nombre_sede_limpio}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

    st.download_button(
        label="📊 Descargar Datos en Excel",
        data=buffer_excel.getvalue(),
        file_name=f"Datos_ANC_{nombre_sede_limpio}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
