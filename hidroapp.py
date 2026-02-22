import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
# Importamos funciones originales
from analisis_hidrometrico import leer_archivo, convertir_formatos, estadisticas

st.set_page_config(page_title="Soluciones digitales", layout="wide")

st.title("Sistema de análisis e intercomparación de estaciones hidrométricas")
st.markdown("Cargá los archivos para generar el tablero de control.")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("Configuración")
    archivos_subidos = st.file_uploader("Subí archivos .txt", type="txt", accept_multiple_files=True)
    st.info("Podés subir varios archivos a la vez para compararlos.")

if archivos_subidos:
    resumen_datos = []
    fig, ax = plt.subplots(figsize=(12, 5))
    
    # Procesamiento de cada archivo
    for archivo in archivos_subidos:
        with open("temp.txt", "wb") as f:
            f.write(archivo.getbuffer())
        
        encabezado, datos = leer_archivo("temp.txt")
        fechas, alturas = convertir_formatos(datos)
        v_medio, v_max, v_min, desv, m_max, m_min = estadisticas(alturas, fechas)
        
        # Guardamos datos para la tabla (Agregamos las fechas de los extremos)
        resumen_datos.append({
            "Estación": archivo.name,
            "Caudal Medio (m³/s)": round(v_medio, 2),
            "Máximo Histórico": round(v_max, 2),
            "Fecha Máximo": m_max,
            "Mínimo Histórico": round(v_min, 2),
            "Fecha Mínimo": m_min
        })
        
        # Agregamos al gráfico
        ax.plot(fechas, alturas, label=f"{archivo.name}", alpha=0.8, linewidth=1)

    # --- 1. TABLA DE RESUMEN ---
    st.subheader("Resumen estadístico comparativo")
    df_resumen = pd.DataFrame(resumen_datos)
    st.dataframe(df_resumen, use_container_width=True) # Una tabla más moderna
    
    
    
    # --- GRÁFICO INTERACTIVO ---
st.subheader("Hidrogramas comparativos")
st.info("💡 Tip: Podés hacer zoom seleccionando un área con el mouse o doble clic para volver al inicio.")

# Creamos un DataFrame que una todas las series por fecha
if archivos_subidos:
    df_grafico = pd.DataFrame()
    for arc in archivos_subidos:
        # Usamos las funciones conocidas
        encabezado, datos = leer_archivo(f"temp_{arc.name}.txt") # Usamos nombres únicos
        fechas, caudales = convertir_formatos(datos)
        
        # Creamos una serie temporal para esta estación
        serie_estacion = pd.Series(caudales, index=fechas, name=arc.name)
        
        if df_grafico.empty:
            df_grafico = serie_estacion.to_frame()
        else:
            df_grafico = df_grafico.join(serie_estacion, how='outer')

    # Gráfico interactivo
    st.line_chart(df_grafico)


    # --- 3. EXPORTACIÓN ---
    st.subheader("📥 Generar informe")
    
    # Creamos el Excel en memoria
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_resumen.to_excel(writer, index=False, sheet_name='Estadisticas')
        
        # Aplicamos un poco de formato al Excel
        workbook  = writer.book
        worksheet = writer.sheets['Estadisticas']
        header_format = workbook.add_format({'bold': True, 'bg_color': '#4F81BD', 'font_color': 'white', 'border': 1})
        
        for col_num, value in enumerate(df_resumen.columns.values):
            worksheet.write(0, col_num, value, header_format)
            worksheet.set_column(col_num, col_num, 20) # Ancho de columna

    st.download_button(
        label="Descargar reporte(.xlsx)",
        data=output.getvalue(),
        file_name="reporte_hidrológico.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.warning("👈 Por favor, subí al menos un archivo en la barra lateral para comenzar.")