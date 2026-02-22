import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import calendar
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Análisis Hidrométrico", layout="wide")

# --- FUNCIONES DE PROCESAMIENTO ---

def leer_archivo_streamlit(file_content):
    encabezado = []
    datos = []
    # Decodificamos el contenido del archivo subido
    lineas = file_content.decode("windows-1252").splitlines()
    
    for linea in lineas:
        linea = linea.strip()
        if not linea: continue
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

#>>>>>> CALCULAR PERÍODO Y OBSERVACIONES <<<<<<
   
# Creamos una función para identificar la longitud de la serie y
# el período cubierto por los datos y contar la cantidad de datos observados y la cantidad de datos faltantes.
   
def observaciones (fechas_array, alturas_masked):
       
    # Calculamos la longitud de la serie temporal.
    longitud = len(fechas_array)
    
    # Calculamos el período cubierto por datos.
    fecha_inicial = min(fechas_array)
    fecha_final = max(fechas_array)
    
    #Contamos la cantidad de datos observados y datos faltantes.     
    datos_faltantes = alturas_masked.mask.sum()   # cuenta los valores enmascarados (-999.000)
    datos_obs = alturas_masked.count()       
            
    return longitud, fecha_inicial, fecha_final, datos_faltantes, datos_obs


# >>>>>> ESTADÍSTICAS BÁSICAS <<<<<<

def estadisticas (alturas_masked, fechas_array):
    
    # Calculamos estadísticas ignorando los valores enmascarados.    
    valor_medio = (alturas_masked.mean())
    valor_maximo =  (alturas_masked.max())
    valor_minimo = (alturas_masked.min())
    desviacion = (np.std(alturas_masked))
    indice_max = np.argmax(alturas_masked)
    indice_min = np.argmin(alturas_masked)
    mes_max = fechas_array [indice_max]
    mes_min = fechas_array [indice_min]
    
    return valor_medio,valor_maximo,valor_minimo, desviacion, mes_max, mes_min


# >>>>>> INDICADORES HIDROLÓGICOS <<<<<<

def indicadores_hidrologicos(alturas_masked, fechas_array):
    
    
    df = pd.DataFrame({
        'fecha': pd.to_datetime(fechas_array),
        'caudal': alturas_masked})
    
    df = df.dropna()

    # Percentiles importantes
    q10 = df['caudal'].quantile(0.10)
    q50 = df['caudal'].quantile(0.50)
    q90 = df['caudal'].quantile(0.90)
    q95 = df['caudal'].quantile(0.05)
    
    # Coeficiente de variación
    coef_var = df['caudal'].std() / df['caudal'].mean()

    # Máximos anuales
    maximos_anuales = df.groupby(df['fecha'].dt.year)['caudal'].max()

    return q10, q50, q90, q95, coef_var, maximos_anuales 


# --- INTERFAZ DE USUARIO CON STREAMLIT ---

st.title("Programa de análisis hidrométrico")
st.markdown("Sube tu archivo de datos para generar estadísticas y gráficos automáticos.")

# Sidebar
archivos_subidos = st.sidebar.file_uploader("Selecciona archivos .txt", type=["txt"], accept_multiple_files=True)

if archivos_subidos:
    resumen_para_excel = []
    dict_hojas = {}

    for archivo in archivos_subidos:
        # Procesamiento
        nombre_estacion = archivo.name.replace(".txt", "").upper()
        enc, dat = leer_archivo_streamlit(archivo.read())
        fec, alt = convertir_formatos(dat)
        
        # Cálculos
        lon, f_ini, f_fin, falt, obs = observaciones(fec, alt)
        q10, q50, q90, q95, cv, maximos_anuales = indicadores_hidrologicos(alt, fec)
        media = alt.mean()
        maximo = alt.max()
        minimo = alt.min()

        # --- DISEÑO IGUAL A TU IMAGEN ---
        st.header(f"Resultados: {nombre_estacion}")
        
        # Fila 1 de Métricas
        col1, col2, col3 = st.columns(3)
        col1.metric("Media", f"{media:.2f} m³/s")
        col2.metric("Máximo", f"{maximo:.2f} m³/s")
        col3.metric("Datos faltantes", int(falt))

        # Fila 2 de Métricas
        col4, col5, col6 = st.columns(3)
        col4.metric("Q50 (Mediana)", f"{q50:.2f} m³/s")
        col5.metric("Mínimo", f"{minimo:.2f} m³/s")
        col6.metric("Datos observados", int(obs))

        # Pestañas de Gráficos (Tal cual tu imagen)
        tab1, tab2, tab3 = st.tabs(["Evolución temporal", "Ciclo anual", "Curva de duración"])
        
        df_plot = pd.DataFrame({'fecha': pd.to_datetime(fec), 'caudal': alt})

        with tab1:
            fig1, ax1 = plt.subplots(figsize=(10, 4))
            ax1.plot(df_plot['fecha'], df_plot['caudal'], color='blue')
            st.pyplot(fig1)

        with tab2:
            ciclo = df_plot.groupby(df_plot['fecha'].dt.month)['caudal'].mean()
            fig2, ax2 = plt.subplots(figsize=(10, 4))
            ax2.plot(ciclo.index, ciclo.values, marker='o', color='green')
            ax2.set_xticks(range(1, 13))
            ax2.set_xticklabels(calendar.month_abbr[1:13])
            st.pyplot(fig2)

        with tab3:
            datos_sort = np.sort(alt.compressed())[::-1]
            prob = np.arange(1, len(datos_sort) + 1) / len(datos_sort) * 100
            fig3, ax3 = plt.subplots(figsize=(10, 4))
            ax3.plot(prob, datos_sort)
            ax3.invert_xaxis()
            ax3.set_title("Curva de Duración")
            st.pyplot(fig3)
        
        st.divider() # Separador entre estaciones

        # Guardar para Excel
        resumen_para_excel.append({
            "Estación": nombre_estacion, "Media": media, "Máximo": maximo, 
            "Mínimo": minimo, "Q50": q50, "Faltantes": falt, "Observados": obs
        })
        dict_hojas[nombre_estacion] = df_plot

    # --- BOTÓN EXCEL EN SIDEBAR ---
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        pd.DataFrame(resumen_para_excel).to_excel(writer, sheet_name='Resumen', index=False)
        for nom, df in dict_hojas.items():
            df.to_excel(writer, sheet_name=nom[:31], index=False)   

    st.sidebar.markdown("---")
    st.sidebar.download_button(
        label="📥 Descargar todo en Excel",
        data=output.getvalue(),
        file_name="Analisis_Hidrometrico.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("👈 Por favor, sube un archivo .txt desde la barra lateral.")
























































