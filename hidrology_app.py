import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import calendar
import io
from scipy import stats

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Análisis Hidrométrico", layout="wide")

# --- FUNCIONES DE PROCESAMIENTO ---

def leer_archivo_streamlit(file_content):
    encabezado = []
    datos = []
    lineas = file_content.decode("windows-1252").splitlines()
    for linea in lineas:
        linea = linea.strip()
        if not linea:
            continue
        if linea.startswith("#"):
            encabezado.append(linea)
            continue
        partes = linea.split(";")
        if len(partes) == 5 and partes[0].count("-") == 2 and partes[0][:4].isdigit():
            datos.append(partes)
        else:
            encabezado.append(linea)
    return encabezado, datos


def convertir_formatos(datos):
    fechas = []
    alturas = []
    for fila in datos:
        fecha = datetime.strptime(fila[0], "%Y-%m-%d").date()
        valor = float(fila[3])
        fechas.append(fecha)
        alturas.append(valor)
    fechas_array = np.array(fechas)
    alturas_masked = np.ma.masked_values(np.array(alturas), -999.000)
    return fechas_array, alturas_masked


def observaciones(fechas_array, alturas_masked):
    longitud = len(fechas_array)
    fecha_inicial = min(fechas_array)
    fecha_final = max(fechas_array)
    datos_faltantes = alturas_masked.mask.sum()
    datos_obs = alturas_masked.count()
    return longitud, fecha_inicial, fecha_final, datos_faltantes, datos_obs


def estadisticas(alturas_masked, fechas_array):
    valor_medio = alturas_masked.mean()
    valor_maximo = alturas_masked.max()
    valor_minimo = alturas_masked.min()
    desviacion = np.std(alturas_masked)
    indice_max = np.argmax(alturas_masked)
    indice_min = np.argmin(alturas_masked)
    mes_max = fechas_array[indice_max]
    mes_min = fechas_array[indice_min]
    return valor_medio, valor_maximo, valor_minimo, desviacion, mes_max, mes_min


def indicadores_hidrologicos(alturas_masked, fechas_array):
    df = pd.DataFrame({
        'fecha': pd.to_datetime(fechas_array),
        'caudal': alturas_masked
    })
    df = df.dropna()

    q10 = df['caudal'].quantile(0.10)
    q50 = df['caudal'].quantile(0.50)
    q90 = df['caudal'].quantile(0.90)
    q95 = df['caudal'].quantile(0.95)   # ← bug corregido (antes era 0.05)
    coef_var = df['caudal'].std() / df['caudal'].mean()
    maximos_anuales = df.groupby(df['fecha'].dt.year)['caudal'].max()

    return q10, q50, q90, q95, coef_var, maximos_anuales


# >>>>>> ANÁLISIS DE FRECUENCIA DE CRECIDAS (GUMBEL) <<<<<<

def analisis_frecuencia_gumbel(maximos_anuales):
    """
    Ajusta la distribución de Gumbel (GEV tipo I) a la serie de máximos anuales
    y estima caudales para distintos períodos de retorno.

    La distribución de Gumbel se parametriza a partir de la media (mu) y el
    desvío estándar (sigma) de los máximos anuales usando el método de momentos:
        alpha = sigma * sqrt(6) / pi       (parámetro de escala)
        u     = mu - 0.5772 * alpha        (parámetro de posición, constante de Euler)

    El cuantil para un período de retorno T es:
        Q(T) = u - alpha * ln(-ln(1 - 1/T))
    """
    serie = maximos_anuales.dropna().values
    n = len(serie)

    if n < 5:
        return None, None, None

    mu = serie.mean()
    sigma = serie.std(ddof=1)

    # Parámetros de Gumbel por método de momentos
    alpha = sigma * np.sqrt(6) / np.pi
    u = mu - 0.5772 * alpha

    # Períodos de retorno de interés para diseño hidráulico
    periodos = [2, 5, 10, 25, 50, 100, 200, 500]
    caudales_T = {}
    for T in periodos:
        yT = -np.log(-np.log(1 - 1 / T))       # variable reducida de Gumbel
        QT = u + alpha * yT
        caudales_T[T] = round(QT, 2)

    # Test de bondad de ajuste Kolmogorov-Smirnov
    # Transformamos la serie a la CDF de Gumbel para comparar con la empírica
    cdf_teorica = np.exp(-np.exp(-(serie - u) / alpha))
    serie_ord = np.sort(serie)
    cdf_empirica = np.arange(1, n + 1) / (n + 1)   # fórmula de Weibull
    ks_stat = np.max(np.abs(np.sort(cdf_teorica) - cdf_empirica))
    ks_critico_95 = 1.36 / np.sqrt(n)               # valor crítico al 95%
    ajuste_ok = ks_stat < ks_critico_95

    info_ajuste = {
        "n": n,
        "mu": round(mu, 2),
        "sigma": round(sigma, 2),
        "alpha": round(alpha, 2),
        "u": round(u, 2),
        "ks_stat": round(ks_stat, 4),
        "ks_critico": round(ks_critico_95, 4),
        "ajuste_ok": ajuste_ok
    }

    return caudales_T, serie_ord, info_ajuste


def grafico_gumbel(serie_ord, info_ajuste, nombre_estacion):
    """
    Genera el gráfico de papel de probabilidad de Gumbel:
    eje X = variable reducida y = -ln(-ln(F)), eje Y = caudal.
    Los puntos son los máximos anuales observados, la línea es el ajuste teórico.
    """
    n = info_ajuste["n"]
    u = info_ajuste["u"]
    alpha = info_ajuste["alpha"]

    # Variable reducida empírica (Weibull)
    F_emp = np.arange(1, n + 1) / (n + 1)
    y_emp = -np.log(-np.log(F_emp))

    # Línea teórica
    y_teo = np.linspace(-1.5, 7, 200)
    Q_teo = u + alpha * y_teo

    # Marcas de período de retorno en eje X superior
    T_marks = [2, 5, 10, 25, 50, 100, 200, 500]
    y_T = [-np.log(-np.log(1 - 1 / T)) for T in T_marks]

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(y_teo, Q_teo, color='steelblue', linewidth=2, label='Ajuste Gumbel', zorder=2)
    ax.scatter(y_emp, serie_ord, color='tomato', zorder=3, s=40, label='Máximos anuales obs.')

    # Líneas verticales punteadas en los T marcados
    for yT, T in zip(y_T, T_marks):
        ax.axvline(yT, color='gray', linestyle='--', linewidth=0.6, alpha=0.6)
        ax.text(yT, ax.get_ylim()[0] if ax.get_ylim()[0] > 0 else serie_ord.min() * 0.95,
                f'T={T}', ha='center', va='bottom', fontsize=7, color='gray')

    ax.set_xlabel("Variable reducida de Gumbel  y = -ln(-ln(F))", fontsize=10)
    ax.set_ylabel("Caudal máximo anual (m³/s)", fontsize=10)
    ax.set_title(f"Papel de probabilidad de Gumbel — {nombre_estacion}", fontsize=11)
    ax.legend(fontsize=9)
    ax.grid(True, linestyle='--', alpha=0.4)

    plt.tight_layout()
    return fig


# --- INTERFAZ DE USUARIO ---

st.title("Programa de análisis hidrométrico")
st.markdown("Sube tu archivo de datos para generar estadísticas y gráficos automáticos.")

archivos_subidos = st.sidebar.file_uploader(
    "Selecciona archivos .txt", type=["txt"], accept_multiple_files=True
)

if archivos_subidos:
    resumen_para_excel = []
    resumen_frecuencia = []
    dict_hojas = {}

    for archivo in archivos_subidos:
        nombre_estacion = archivo.name.replace(".txt", "").upper()

        # --- Lectura y cálculos con manejo de errores ---
        try:
            enc, dat = leer_archivo_streamlit(archivo.read())
            fec, alt = convertir_formatos(dat)
        except Exception as e:
            st.error(f"❌ No se pudo leer el archivo **{archivo.name}**: {e}")
            continue

        lon, f_ini, f_fin, falt, obs = observaciones(fec, alt)
        q10, q50, q90, q95, cv, maximos_anuales = indicadores_hidrologicos(alt, fec)
        media = alt.mean()
        maximo = alt.max()
        minimo = alt.min()

        # --- Análisis de frecuencia ---
        caudales_T, serie_ord, info_ajuste = analisis_frecuencia_gumbel(maximos_anuales)

        # --- DISEÑO ---
        st.header(f"Resultados: {nombre_estacion}")
        st.caption(f"Período: {f_ini} → {f_fin}  |  {len(maximos_anuales)} años de datos")

        col1, col2, col3 = st.columns(3)
        col1.metric("Media", f"{media:.2f} m³/s")
        col2.metric("Máximo", f"{maximo:.2f} m³/s")
        col3.metric("Datos faltantes", int(falt))

        col4, col5, col6 = st.columns(3)
        col4.metric("Q50 (Mediana)", f"{q50:.2f} m³/s")
        col5.metric("Mínimo", f"{minimo:.2f} m³/s")
        col6.metric("Datos observados", int(obs))

        # --- Pestañas ---
        tab1, tab2, tab3, tab4 = st.tabs([
            "Evolución temporal", "Ciclo anual", "Curva de duración", "Frecuencia de crecidas"
        ])

        df_plot = pd.DataFrame({'fecha': pd.to_datetime(fec), 'caudal': alt})

        with tab1:
            fig1, ax1 = plt.subplots(figsize=(10, 4))
            ax1.plot(df_plot['fecha'], df_plot['caudal'], color='steelblue', linewidth=0.8)
            ax1.set_ylabel("Caudal (m³/s)")
            ax1.set_title(f"Serie temporal — {nombre_estacion}")
            ax1.grid(True, linestyle='--', alpha=0.4)
            plt.tight_layout()
            st.pyplot(fig1)

        with tab2:
            ciclo = df_plot.groupby(df_plot['fecha'].dt.month)['caudal'].mean()
            fig2, ax2 = plt.subplots(figsize=(10, 4))
            ax2.bar(ciclo.index, ciclo.values, color='steelblue', alpha=0.7, edgecolor='white')
            ax2.plot(ciclo.index, ciclo.values, marker='o', color='navy', linewidth=1.5)
            ax2.set_xticks(range(1, 13))
            ax2.set_xticklabels(calendar.month_abbr[1:13])
            ax2.set_ylabel("Caudal medio mensual (m³/s)")
            ax2.set_title(f"Ciclo anual — {nombre_estacion}")
            ax2.grid(True, linestyle='--', alpha=0.4, axis='y')
            plt.tight_layout()
            st.pyplot(fig2)

        with tab3:
            datos_sort = np.sort(alt.compressed())[::-1]
            prob = np.arange(1, len(datos_sort) + 1) / len(datos_sort) * 100
            fig3, ax3 = plt.subplots(figsize=(10, 4))
            ax3.plot(prob, datos_sort, color='steelblue', linewidth=1.2)
            ax3.invert_xaxis()
            ax3.set_xlabel("Porcentaje del tiempo excedido (%)")
            ax3.set_ylabel("Caudal (m³/s)")
            ax3.set_title(f"Curva de duración — {nombre_estacion}")
            ax3.grid(True, linestyle='--', alpha=0.4)
            plt.tight_layout()
            st.pyplot(fig3)

        with tab4:
            if caudales_T is None:
                st.warning("Se necesitan al menos 5 años de datos para el análisis de frecuencia.")
            else:
                st.subheader("Ajuste distribución de Gumbel (método de momentos)")

                # Parámetros del ajuste
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Años de datos (n)", info_ajuste["n"])
                col_b.metric("Media máximos anuales", f"{info_ajuste['mu']} m³/s")
                col_c.metric("Desvío estándar", f"{info_ajuste['sigma']} m³/s")

                col_d, col_e, col_f = st.columns(3)
                col_d.metric("Parámetro α (escala)", f"{info_ajuste['alpha']}")
                col_e.metric("Parámetro u (posición)", f"{info_ajuste['u']}")
                ajuste_texto = "✅ Ajuste aceptable" if info_ajuste["ajuste_ok"] else "⚠️ Ajuste cuestionable"
                col_f.metric("Test KS (95%)", ajuste_texto,
                             delta=f"D={info_ajuste['ks_stat']} < {info_ajuste['ks_critico']}"
                             if info_ajuste["ajuste_ok"]
                             else f"D={info_ajuste['ks_stat']} > {info_ajuste['ks_critico']}")

                st.markdown("---")

                # Tabla de caudales de diseño
                st.subheader("Caudales de diseño por período de retorno")
                df_T = pd.DataFrame({
                    "Período de retorno T (años)": list(caudales_T.keys()),
                    "Probabilidad de excedencia (1/T)": [f"{1/T:.3f}" for T in caudales_T.keys()],
                    "Caudal de diseño Q(T) (m³/s)": list(caudales_T.values())
                })
                st.dataframe(df_T, use_container_width=True, hide_index=True)

                # Gráfico papel de probabilidad
                st.subheader("Papel de probabilidad de Gumbel")
                fig4 = grafico_gumbel(serie_ord, info_ajuste, nombre_estacion)
                st.pyplot(fig4)

                st.caption(
                    "ℹ️ El test de Kolmogorov-Smirnov compara la distribución empírica con la teórica. "
                    "Si D < D_crítico al 95%, no se rechaza el ajuste de Gumbel."
                )

                # Guardar para Excel
                resumen_frecuencia.append({
                    "Estación": nombre_estacion,
                    **{f"Q{T} (m³/s)": q for T, q in caudales_T.items()},
                    "n años": info_ajuste["n"],
                    "KS stat": info_ajuste["ks_stat"],
                    "KS crítico 95%": info_ajuste["ks_critico"],
                    "Ajuste OK": info_ajuste["ajuste_ok"]
                })

        st.divider()

        resumen_para_excel.append({
            "Estación": nombre_estacion,
            "Media": media,
            "Máximo": maximo,
            "Mínimo": minimo,
            "Q50": q50,
            "Q10": q10,
            "Q90": q90,
            "Q95": q95,
            "CV": round(cv, 3),
            "Faltantes": falt,
            "Observados": obs
        })
        dict_hojas[nombre_estacion] = df_plot

    # --- EXPORTAR EXCEL ---
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        pd.DataFrame(resumen_para_excel).to_excel(writer, sheet_name='Resumen estadístico', index=False)
        if resumen_frecuencia:
            pd.DataFrame(resumen_frecuencia).to_excel(writer, sheet_name='Frecuencia de crecidas', index=False)
        for nom, df in dict_hojas.items():
            df.to_excel(writer, sheet_name=nom[:31], index=False)

    st.sidebar.markdown("---")
    st.sidebar.download_button(
        label="📥 Descargar informe en Excel",
        data=output.getvalue(),
        file_name="Analisis_Hidrometrico.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("👈 Por favor, sube un archivo .txt desde la barra lateral.")