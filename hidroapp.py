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
    df_global = pd.DataFrame()
    resumen_lista = []
    
    for arc in archivos_subidos:
        # Decodificamos el archivo subido a texto directamente
        contenido = arc.getvalue().decode("windows-1252").splitlines()
        
        # Pasamos la lista de líneas de la función
        encabezado, datos = leer_archivo(contenido)
        fechas, caudales = convertir_formatos(datos)
        # Obtenemos las estadísticas reales
        v_medio, v_max, v_min, desv, m_max, m_min = estadisticas(caudales, fechas)
        # Preparamos los datos para el gráfico comparativo
        temp_df = pd.DataFrame({'Fecha': fechas, arc.name: caudales})
        temp_df.set_index('Fecha', inplace=True)
        if df_global.empty:
            df_global = temp_df
        else:
            df_global = df_global.join(temp_df, how='outer')

        # Guardamos la info para la tabla y el Excel
        resumen_lista.append({
            "Estación": arc.name,
            "Caudal Medio (m3/s)": round(v_medio, 2),
            "Máximo Histórico": round(v_max, 2),
            "Mínimo Histórico": round(v_min, 2),
            "Procesamiento": "Relleno con Media"
        })


    #  TABLA DE RESULTADOS
    st.subheader("Resumen estadístico comparativo")
    df_resumen = pd.DataFrame(resumen_lista)
    st.dataframe(df_resumen, use_container_width=True)
    
    #  INTERFAZ VISUAL: GRÁFICO INTERACTIVO
    st.subheader("Hidrogramas de Caudales")
    st.info("💡 Tip: Seleccioná un área del gráfico con el mouse para hacer zoom.")
    st.line_chart(df_global)
    

    #  EXPORTAR A EXCEL 
    st.subheader("📥 Generar informe")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_resumen.to_excel(writer, index=False, sheet_name='Estadisticas')
        
        # Aplicamos un poco de formato al Excel
        workbook  = writer.book
        worksheet = writer.sheets['Estadisticas']
        header_format = workbook.add_format({'bold': True, 'bg_color': '#4F81BD', 'font_color': 'white', 'border': 1})
        
        for col_num, value in enumerate(df_resumen.columns.values):
            worksheet.write(0, col_num, value, header_format)
            worksheet.set_column(col_num, col_num, 20) # Ancho de columna
    
    st.download_button(
        label="Descargar reporte en Excel (.xlsx)",
        data=buffer.getvalue(),
        file_name="reporte_hidrologico.xlsx",
        mime="application/vnd.ms-excel"
    )
    
else:
       st.warning("👈 Por favor, subí al menos un archivo en la barra lateral para comenzar.") 
    
#%% 
    
 
    
 
    
 
    
