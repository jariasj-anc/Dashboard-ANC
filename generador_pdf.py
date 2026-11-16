import os
import tempfile
import matplotlib.pyplot as plt
from fpdf import FPDF

def txt_latin(texto):
    reemplazos = {"—": "-", "–": "-", "•": "*", "±": "+/-"}
    for orig, dest in reemplazos.items():
        texto = str(texto).replace(orig, dest)
    return texto.encode("latin-1", "replace").decode("latin-1")

def construir_pdf_completo(
    sede_seleccionada, txt_ult_largo, ultimo_mes, pct_tramite, pct_impug,
    anio_actual, prod_acum_actual, df_filtrado, fechas_futuras, proy_carga,
    carga_inf, carga_sup, proy_prod, prod_inf, prod_sup, prec_carga, prec_prod,
    anio_sel, fecha_corte_rank, fila_cierre, df_desc, resumen_anual, filas_est,
    carga_fin, media_carga, rango_carga_inf, rango_carga_sup, cv_carga,
    media_prod, rango_prod_inf, rango_prod_sup, cv_prod, stats_dict,
    pct_tram_cierre, pct_imp_cierre, df_ranking, texto_corte, df_rank_prod,
    formato_fecha_es
):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)

    pdf.add_page()
    pdf.set_fill_color(127, 29, 29)
    pdf.rect(10, 10, 190, 21, style="F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 12.5)
    pdf.set_xy(14, 13)
    pdf.cell(0, 6, txt_latin("AUTORIDAD NACIONAL DE CONTROL DEL PODER JUDICIAL"), ln=True)
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_x(14)
    pdf.cell(0, 5, txt_latin(f"Reporte Ejecutivo Integral - {sede_seleccionada}"), ln=True)

    pdf.set_text_color(30, 41, 59)
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.set_xy(10, 35)
    pdf.cell(0, 6, txt_latin(f"1. Situación Actual al Cierre de {txt_ult_largo}"), ln=True)

    kpis_p1 = [
        ("Carga Total Activa", f"{int(ultimo_mes['Carga_Total']):,} exp."),
        (f"En Trámite ({pct_tramite:.1f}%)", f"{int(ultimo_mes['Tramite']):,} exp."),
        (f"Por Impugnar ({pct_impug:.1f}%)", f"{int(ultimo_mes['Impugnacion']):,} exp."),
        (f"Prod. Acum. ({anio_actual})", f"{prod_acum_actual:,} prod.")
    ]
    for idx, (titulo_k, val_k) in enumerate(kpis_p1):
        x_k = 10 + idx * 48
        pdf.set_fill_color(248, 250, 252)
        pdf.set_draw_color(203, 213, 225)
        pdf.rect(x_k, 43, 45.5, 16, style="DF")
        pdf.set_xy(x_k + 2, 45)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(41, 4, txt_latin(titulo_k), ln=True)
        pdf.set_x(x_k + 2)
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(41, 6, txt_latin(val_k), ln=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3.5), dpi=180)
        fig1.patch.set_facecolor("white")

        ax1.plot(df_filtrado['Fecha'], df_filtrado['Carga_Total'], color="#0284c7", linewidth=2, label="Real")
        f_link = [df_filtrado['Fecha'].iloc[-1]] + list(fechas_futuras)
        c_link = [df_filtrado['Carga_Total'].iloc[-1]] + list(proy_carga)
        ax1.plot(f_link, c_link, color="#d97706", linestyle="--", linewidth=2, label="Proyección")
        ax1.fill_between(fechas_futuras, carga_inf, carga_sup, color="#f59e0b", alpha=0.2, label="Rango 95%")
        ax1.set_title("Proyección de Carga Activa", fontsize=10, fontweight="bold", color="#1e293b")
        ax1.grid(True, linestyle=":", alpha=0.5)
        ax1.tick_params(axis='x', rotation=30, labelsize=7.5)
        ax1.tick_params(axis='y', labelsize=8)
        ax1.legend(fontsize=7.5, loc="best")

        ax2.bar(df_filtrado['Fecha'], df_filtrado['Produccion'], width=20, color="#10b981", alpha=0.85, label="Real")
        ax2.plot(fechas_futuras, proy_prod, color="#e11d48", marker="o", markersize=4, linestyle="--", linewidth=1.8, label="Proyección")
        ax2.fill_between(fechas_futuras, prod_inf, prod_sup, color="#f43f5e", alpha=0.18, label="Rango 95%")
        ax2.set_title("Histórico y Proyección de Producción", fontsize=10, fontweight="bold", color="#1e293b")
        ax2.grid(True, linestyle=":", alpha=0.5)
        ax2.tick_params(axis='x', rotation=30, labelsize=7.5)
        ax2.tick_params(axis='y', labelsize=8)
        ax2.legend(fontsize=7.5, loc="best")

        plt.tight_layout()
        ruta_img1 = os.path.join(tmpdir, "graf_p1.png")
        plt.savefig(ruta_img1, facecolor="white")
        plt.close(fig1)
        pdf.image(ruta_img1, x=10, y=63, w=190)

        pdf.set_xy(10, 133)
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 6, txt_latin(f"2. Proyecciones Mensuales e Intervalos al 95% (Precisión Carga: {prec_carga:.1f}% | Prod: {prec_prod:.1f}%)"), ln=True)

        pdf.set_fill_color(30, 41, 59)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 8.5)
        anchos = (42, 34, 42, 34, 38)
        headers = ["Mes Proyectado", "Carga Estimada", "Rango Carga (95%)", "Prod. Estimada", "Rango Prod. (95%)"]
        for w, h in zip(anchos, headers):
            pdf.cell(w, 7, txt_latin(h), border=1, align="C", fill=True)
        pdf.ln()

        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(15, 23, 42)
        for idx in range(len(fechas_futuras)):
            fill_row = idx % 2 == 1
            pdf.set_fill_color(248, 250, 252) if fill_row else pdf.set_fill_color(255, 255, 255)
            fila_txt = [
                formato_fecha_es(fechas_futuras[idx], corto=False),
                f"{proy_carga[idx]:,}",
                f"{carga_inf[idx]:,} - {carga_sup[idx]:,}",
                f"{proy_prod[idx]:,}",
                f"{prod_inf[idx]:,} - {prod_sup[idx]:,}"
            ]
            for w, val in zip(anchos, fila_txt):
                pdf.cell(w, 6.5, txt_latin(val), border=1, align="C", fill=fill_row)
            pdf.ln()
        pdf.add_page()
        pdf.set_fill_color(30, 41, 59)
        pdf.rect(10, 10, 190, 14, style="F")
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_xy(13, 14)
        pdf.cell(0, 6, txt_latin(f"3. Estadísticas Históricas ({anio_sel}) - {sede_seleccionada}"), ln=True)

        kpis_p2 = [
            (f"Cierre ({formato_fecha_es(fecha_corte_rank, corto=True)})", f"{int(fila_cierre['Carga_Total']):,}"),
            ("Prom. Carga", f"{df_desc['Carga_Total'].mean():,.0f}"),
            ("Prom. Trámite", f"{df_desc['Tramite'].mean():,.0f}"),
            ("Prom. Impugnar", f"{df_desc['Impugnacion'].mean():,.0f}"),
            ("Prod. Total", f"{int(df_desc['Produccion'].sum()):,}")
        ]
        for idx, (tk2, vk2) in enumerate(kpis_p2):
            xk2 = 10 + idx * 38.4
            pdf.set_fill_color(248, 250, 252)
            pdf.set_draw_color(203, 213, 225)
            pdf.rect(xk2, 27, 36.4, 15, style="DF")
            pdf.set_xy(xk2 + 1.5, 28.5)
            pdf.set_font("Helvetica", "", 7.5)
            pdf.set_text_color(100, 116, 139)
            pdf.cell(33, 4, txt_latin(tk2), ln=True)
            pdf.set_x(xk2 + 1.5)
            pdf.set_font("Helvetica", "B", 9.5)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(33, 5.5, txt_latin(vk2), ln=True)

        pdf.set_xy(10, 46)
        pdf.set_text_color(30, 41, 59)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, txt_latin("Resumen Comparativo Anual"), ln=True)

        pdf.set_fill_color(127, 29, 29)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 7.5)
        w_anual = (16, 16, 26, 26, 26, 26, 27, 27)
        h_anual = ["Año", "Meses", "Carga Cierre", "Prom. Carga", "Prom. Trám.", "Prom. Impug.", "Prom. Prod.", "Total Prod."]
        for w, h in zip(w_anual, h_anual):
            pdf.cell(w, 6.5, txt_latin(h), border=1, align="C", fill=True)
        pdf.ln()

        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(15, 23, 42)
        for r_idx, row in resumen_anual.iterrows():
            fill_r = r_idx % 2 == 1
            pdf.set_fill_color(248, 250, 252) if fill_r else pdf.set_fill_color(255, 255, 255)
            vals = [
                str(row['Año']), str(row['Meses']), f"{row['Carga al Cierre']:,}",
                f"{row['Prom. Carga Total']:,}", f"{row['Prom. En Trámite']:,}",
                f"{row['Prom. Por Impugnar']:,}", f"{row['Prom. Producción/Mes']:,}", f"{row['Total Producción']:,}"
            ]
            for w, v in zip(w_anual, vals):
                pdf.cell(w, 6, txt_latin(v), border=1, align="C", fill=fill_r)
            pdf.ln()

        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 6, txt_latin(f"Indicadores Estadísticos de Dispersión y Posición ({anio_sel})"), ln=True)

        pdf.set_fill_color(30, 41, 59)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 7.5)
        w_est = (42, 22, 24, 22, 20, 30, 30)
        h_est = ["Indicador Evaluado", "Promedio", "Mediana", "Desv. Est.", "CV (%)", "Mínimo", "Máximo"]
        for w, h in zip(w_est, h_est):
            pdf.cell(w, 6.5, txt_latin(h), border=1, align="C", fill=True)
        pdf.ln()

        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(15, 23, 42)
        for f_idx, f_dic in enumerate(filas_est):
            fill_f = f_idx % 2 == 1
            pdf.set_fill_color(248, 250, 252) if fill_f else pdf.set_fill_color(255, 255, 255)
            vals_e = [
                f_dic['Indicador Evaluado'], f_dic['Promedio (Media)'],
                f_dic['Mediana (Mes Típico)'], f_dic['Desviación Estándar'],
                f_dic['Coef. Variación (CV)'], f_dic['Mínimo Registrado'],
                f_dic['Máximo Registrado']
            ]
            for w, v in zip(w_est, vals_e):
                pdf.cell(w, 6, txt_latin(v), border=1, align="C", fill=fill_f)
            pdf.ln()

        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(127, 29, 29)
        pdf.cell(0, 6, txt_latin(f"4. Hallazgos Clave - {sede_seleccionada} ({anio_sel})"), ln=True)

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(30, 41, 59)
        h_txt1 = txt_latin(
            f"* Evolución de la Carga Activa: Cerrando en {carga_fin:,} expedientes activos. Sobre un promedio de {media_carga:,.0f} expedientes, "
            f"lo habitual es que cada mes se mantenga entre {rango_carga_inf:,} y {rango_carga_sup:,} expedientes (CV: {cv_carga:.1f}%)."
        )
        h_txt2 = txt_latin(
            f"* Regularidad de la Producción: Sobre un promedio de {media_prod:,.0f} prod. por mes, lo habitual es registrar entre "
            f"{rango_prod_inf:,} y {rango_prod_sup:,} prod. mensuales (CV: {cv_prod:.1f}%). Rendimiento típico: {stats_dict['Produccion']['mediana']:,.0f} prod./mes."
        )
        h_txt3 = txt_latin(
            f"* Composición al Cierre ({formato_fecha_es(fecha_corte_rank, corto=True)}): El {pct_tram_cierre:.1f}% corresponde a expedientes "
            f"En Trámite y el {pct_imp_cierre:.1f}% a expedientes Resueltos por Impugnar."
        )
        for parrafo_h in (h_txt1, h_txt2, h_txt3):
            pdf.multi_cell(0, 5, parrafo_h)
            pdf.ln(1.5)

        pdf.add_page()
        pdf.set_fill_color(127, 29, 29)
        pdf.rect(10, 10, 190, 14, style="F")
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.set_xy(13, 14)
        pdf.cell(0, 6, txt_latin(f"5. Rankings Comparativos a Nivel Nacional ({anio_sel})"), ln=True)

        fig2, (ax_r1, ax_r2) = plt.subplots(1, 2, figsize=(11, 7.2), dpi=180)
        fig2.patch.set_facecolor("white")

        c_r1 = ['#f59e0b' if s == sede_seleccionada else '#0284c7' for s in df_ranking['Sede']]
        ax_r1.barh(df_ranking['Sede'], df_ranking['Carga_Total'], color=c_r1)
        ax_r1.set_title(f"Ranking 1: Carga Activa ({texto_corte})", fontsize=9.5, fontweight="bold", color="#1e293b")
        ax_r1.tick_params(axis='y', labelsize=6.5)
        ax_r1.tick_params(axis='x', labelsize=7.5)
        ax_r1.set_xlim(0, df_ranking['Carga_Total'].max() * 1.25)
        ax_r1.grid(axis='x', linestyle=":", alpha=0.5)
        for idx_b, (tot_b, pct_b) in enumerate(zip(df_ranking['Carga_Total'], df_ranking['Pct_Nac'])):
            ax_r1.text(tot_b + (df_ranking['Carga_Total'].max() * 0.015), idx_b, f"{int(tot_b):,} ({pct_b:.1f}%)", va='center', fontsize=5.8, color="#1e293b")

        df_r2_ord = df_rank_prod.sort_values('Produccion', ascending=True)
        c_r2 = ['#f59e0b' if s == sede_seleccionada else '#10b981' for s in df_r2_ord['Sede']]
        ax_r2.barh(df_r2_ord['Sede'], df_r2_ord['Produccion'], color=c_r2)
        ax_r2.set_title(f"Ranking 2: Producción Global ({anio_sel})", fontsize=9.5, fontweight="bold", color="#1e293b")
        ax_r2.tick_params(axis='y', labelsize=6.5)
        ax_r2.tick_params(axis='x', labelsize=7.5)
        ax_r2.set_xlim(0, df_r2_ord['Produccion'].max() * 1.25)
        ax_r2.grid(axis='x', linestyle=":", alpha=0.5)
        for idx_p, (tot_p, pct_p) in enumerate(zip(df_r2_ord['Produccion'], df_r2_ord['Pct_Nac'])):
            ax_r2.text(tot_p + (df_r2_ord['Produccion'].max() * 0.015), idx_p, f"{int(tot_p):,} ({pct_p:.1f}%)", va='center', fontsize=5.8, color="#1e293b")

        plt.tight_layout()
        ruta_img2 = os.path.join(tmpdir, "graf_p3.png")
        plt.savefig(ruta_img2, facecolor="white")
        plt.close(fig2)
        pdf.image(ruta_img2, x=10, y=28, w=190)

        pdf.set_xy(10, 272)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 4, txt_latin("Fuente: Unidad de Inteligencia y Análisis (UIA) - ANC-PJ. Documento generado automáticamente desde el Dashboard Institucional."))

    return bytes(pdf.output())

