# -*- coding: utf-8 -*-
"""
TRABAJO FINAL INTEGRADOR 
ALUMNAS: PENAYO VERÓNICA, BURGOS MARÍA GABRIELA

"""
#===================================================
#    PROGRAMA MODULAR DE ANÁLISIS HIDROMÉTRICO 
#===================================================



import numpy as np
import pandas as pd
from datetime import datetime 
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import calendar 

#----------------------------------
#       MÓDULO DE ENTRADA
#----------------------------------


#>>>>>> LECTURA DE ARCHIVO <<<<<<

# Definimos una función que permita leer un archivo en formato .txt y lo separe en secciones.

def leer_archivo (archivo):
   
    """
    Lee un archivo txt y separa encabezado y datos.
    Parámetro: 
        archivo (archivo txt).
    Retorna: 
        lista: encabezado.
        lista: datos.
    """
    
    # Creamos listas vacías donde se guardará la información del archivo txt.
    encabezado =[]  
    datos =[]
    # Abrimos archivo en modo lectura.
    with open(archivo, "r", encoding="windows-1252") as archivo:
         for linea in archivo:
            linea = linea.strip()

            # Ignoramos líneas vacías
            if not linea:
                continue

            # Si empieza con "#" es encabezado
            if linea.startswith("#"):
                encabezado.append(linea)
                continue

            # Si tiene el patrón típico de columnas (separadas por ";"), guardamos como dato
            partes = linea.split(";")
            if len(partes) == 5 and partes[0].count("-") == 2 and partes[0][:4].isdigit():
                datos.append(partes)
            else:
                encabezado.append(linea)
    return encabezado, datos
    

#>>>>>> CONVERTIR FORMATOS <<<<<<


# Modificamos los formatos de las columnas de datos. 

def convertir_formatos (datos):
  
   """ 
   Convierte la primera columna a datetime.date y la columna de datos a float.
   Ignora valores inválidos (-999.000). 
   Parámetro:
        datos: lista de listas.
   Retorna:
        fechas_array: array de fechas (datetime.date).
        alturas_masked: array de alturas (float) con valores inválidos enmascarados.
   """
   # Creamos listas vacías.        
   fechas = []
   alturas = []

   for fila in datos:
             
        #Convertimos formatos.
        fecha = datetime.strptime(fila[0], "%Y-%m-%d").date()
        valor = float(fila[3]) 
        
        fechas.append(fecha)
        alturas.append(valor)

   # Convertimos listas a arrays.
   fechas_array = np.array(fechas) 
   alturas_array = np.array(alturas)

   # Enmascaramos los valores faltantes.
   alturas_masked = np.ma.masked_values(alturas_array, -999.000)

   return fechas_array, alturas_masked
   
#--------------------------------
#    MÓDULO DE PROCESAMIENTO
#--------------------------------

#>>>>>> CALCULAR PERÍODO Y OBSERVACIONES <<<<<<
   
# Creamos una función para identificar la longitud de la serie y
# el período cubierto por los datos y contar la cantidad de datos observados y la cantidad de datos faltantes.
   
def observaciones (fechas_array, alturas_masked):
    
    """
    Determina la longitud de la serie temporal, el período cubierto por datos y cuenta 
    la cantidad de datos observados y faltantes.
    
    Parámetro: 
        fechas_array: array de fechas (datetime.date).
        alturas_masked (masked array con valores inválidos enmascarados).
    Retorna: 
        longitud (int): longitud de la serie.
        fecha_inicial (datetime.date): Primera fecha de la serie.
        fecha_final (datetime.date): Última fecha de la serie.
        datos_obs (int): Cantidad de datos válidos.
        datos_faltantes (int): Cantidad de datos faltantes (enmascarados).
    """
    
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
    
    """
    Se define una función para calcular las estadísticas básicas de la serie de datos.
    Parámetros:        
       alturas_masked: array de alturas (masked array con valores inválidos enmascarados).
       fechas_array: array de fechas (datetime.date).
   Retorna:
       media, desviación estándar, valor máximo, valor mínimo (float).
       mes de ocurrencia del máximo, mes de ocurrencia del mínimo.
    """
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



# >>>>>> CURVA DE DURACIÓN <<<<<<

def curva_duracion(alturas_masked):
    
    datos = alturas_masked.compressed()  # elimina valores enmascarados
    datos_ordenados = np.sort(datos)[::-1]
    prob_excedencia = np.arange(1, len(datos_ordenados)+1) / len(datos_ordenados) * 100
    
    return datos_ordenados, prob_excedencia



#----------------------------------
#       MÓDULO DE SALIDA
#----------------------------------



# >>>>>> ARCHIVO DE RESULTADOS OBTENIDOS <<<<<<

# Guardar resultados en archivo .txt

#Definimos una función para guardar los resultados.

def resultados_txt(longitud, fecha_inicial, fecha_final, datos_obs, datos_faltantes,
                   valor_medio, desviacion, valor_maximo, valor_minimo, q10, q50, q90, q95, coef_var, stid):
    """
    Guarda resultados en un archivo .txt
    Parámetros:
        longitud, fecha_inicial, fecha_final, datos_obs, datos_faltantes,
        valor_medio, desviacion, valor_maximo, valor_minimo, stid.
    Retorna: 
        Como salida genera un archivo .txt
    """
    nombre_archivo = f"resultados_{stid}.txt"
    with open(nombre_archivo, "w", encoding="utf-8") as archivo:
        archivo.write(f"Resultados de la estación: {stid}\n")
        archivo.write("====================================\n")
        archivo.write(f"Longitud de la serie temporal:{longitud}\n")
        archivo.write(f"Período de datos: {fecha_inicial} a {fecha_final}\n")
        archivo.write(f"Datos observados: {datos_obs}\n")
        archivo.write(f"Datos faltantes: {datos_faltantes}\n")
        archivo.write(f"Media: {round(valor_medio,2)} m³/s\n")
        archivo.write(f"Valor máximo: {round(valor_maximo,2)} m³/s\n")
        archivo.write(f"Valor mínimo: {round(valor_minimo,2)} m³/s\n")
        archivo.write(f"Desviación estándar: {round(desviacion,2)} m³/s\n")
        archivo.write("\nINDICADORES HIDROLÓGICOS\n")
        archivo.write("====================================\n")
        archivo.write(f"Q10: {round(q10,2)} m³/s\n")
        archivo.write(f"Q50 (mediana): {round(q50,2)} m³/s\n")
        archivo.write(f"Q90: {round(q90,2)} m³/s\n")
        archivo.write(f"Q95 (caudal ecológico): {round(q95,2)} m³/s\n")
        archivo.write(f"Coeficiente de variación: {round(coef_var,3)}\n")
    print(f"Archivo 'resultados_{stid}.txt' guardado correctamente.")
    



# >>>>>> GRÁFICOS <<<<<<

   
def graficos(fechas_array, alturas_masked, stid):
    
    """
   Genera los gráficos principales del análisis hidrométrico para una estación determinada.

   Parámetros:
       fechas_array: array de fechas (datetime.date).
       alturas_masked : array enmascarado.
       stid (str): nombre de la estación.
   Retorna:
       La función no retorna ningún valor.
       Muestra en pantalla las siguientes figuras:
       > Serie temporal completa de alturas calculadas.
       > Ciclo anual medio (promedio mensual de los datos observados).
       > Serie temporal con valores interpolados para los datos faltantes.
       > Ciclo anual medio calculado con los valores interpolados.
    """
    
    

    # Convertimos a DataFrame para facilitar operaciones por mes
    df = pd.DataFrame({'fecha': fechas_array, 'caudal': alturas_masked})
    df['fecha'] = pd.to_datetime(df['fecha'])

    # -------------------------------
    # Serie temporal completa
    # -------------------------------
    plt.figure(figsize=(10,5))
    plt.plot(df['fecha'], df['caudal'], color='blue', label='Caudal diario')
    plt.title(f"Evolución de caudales: {stid}")
    plt.xlabel("Fecha")
    plt.ylabel("Caudal (m³/s)")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

    # ----------------
    # Ciclo anual 
    # ----------------
    ciclo_anual = df.groupby(df['fecha'].dt.month)['caudal'].mean()
    plt.figure(figsize=(8,5))
    plt.plot(ciclo_anual.index, ciclo_anual.values, marker='o', color='green')
    plt.title(f"Ciclo anual medio: {stid}")
    plt.xlabel("Meses")
    plt.ylabel("Caudal medio (m³/s)")
    plt.xticks(range(1,13), calendar.month_abbr[1:13])
    plt.tight_layout()
    plt.show()

    # ----------------------------------------------------
    # Serie con interpolación y ciclo anual interpolado
    # ----------------------------------------------------
    df_rellenado  = df.copy()
    df_rellenado ['caudal'] = df_rellenado['caudal'].fillna(
    df_rellenado.groupby(df_rellenado['fecha'].dt.month)['caudal'].transform('mean'))
    
    ciclo_anual_rellenado = df_rellenado.groupby(df_rellenado['fecha'].dt.month)['caudal'].mean()

    # Serie temporal rellenada
    plt.figure(figsize=(10,5))
    plt.plot(df_rellenado['fecha'], df_rellenado['caudal'], color='orange')
    plt.title(f"Serie temporal con valores representativos : {stid}")
    plt.xlabel("Fecha")
    plt.ylabel("Caudal (m³/s)")
    plt.tight_layout()
    plt.show()

    # Ciclo anual rellenado
    plt.figure(figsize=(8,5))
    plt.plot(ciclo_anual_rellenado.index, ciclo_anual_rellenado.values, color='blue', marker='o')
    plt.title(f"Ciclo anual medio (con valores representativos): {stid}")
    plt.xlabel("Meses")
    plt.ylabel("Caudal medio (m³/s)")
    plt.xticks(range(1,13), calendar.month_abbr[1:13])
    plt.tight_layout()
    plt.show()
    
    
    
    # -------------------------------
    # Curva de duración
    # -------------------------------
    datos_ordenados, prob_excedencia = curva_duracion(alturas_masked)

    plt.figure(figsize=(8,5))
    plt.plot(prob_excedencia, datos_ordenados)
    plt.grid(True, which='both', linestyle='--', alpha=0.5)
    plt.xlabel("Probabilidad de excedencia (%)")
    plt.ylabel("Caudal (m³/s)")
    plt.title(f"Curva de duración de caudales: {stid}")
    plt.gca().invert_xaxis()
    plt.tight_layout()
    plt.show()

#-------------------------------------------
#        PROGRAMA PRINCIPAL 
#-------------------------------------------

#Definimos una función que actúa como programa principal.

def analisis_hidrometrico_completo(nombre_archivo, stid):
    
    """
    Realiza el análisis hidrométrico completo de una estación a partir de un archivo de datos.

    Esta función integra todos los módulos del programa (entrada, procesamiento y salida)
    para leer los datos hidrométricos, procesarlos y generar los resultados estadísticos
    y gráficos correspondientes.

    Parámetros:
       nombre_archivo (str)
       stid (str): Identificador o nombre de la estación hidrométrica.

    Retorna:   
        La función no retorna valores directamente. 
        Como salida genera:
        > un archivo de texto con los resultados estadísticos.
        > gráficos de la serie temporal, ciclo anual y serie interpolada.
        
        """
    
    #Módulo de entrada
    
    encabezado, datos = leer_archivo(nombre_archivo)
    fechas_array, alturas_masked = convertir_formatos(datos)
    
    #Módulo de procesamiento 
    
    longitud, fecha_inicial, fecha_final, datos_faltantes, datos_obs = observaciones(fechas_array, alturas_masked)
    valor_medio, valor_maximo, valor_minimo, desviacion, mes_max, mes_min = estadisticas(alturas_masked, fechas_array)
    q10, q50, q90, q95, coef_var, maximos_anuales = indicadores_hidrologicos(alturas_masked, fechas_array)
     
   
    
    #Módulo de salida
    
    resultados_txt(longitud, fecha_inicial, fecha_final, datos_obs, datos_faltantes,
                   valor_medio, desviacion, valor_maximo, valor_minimo, q10, q50, q90, q95, coef_var, stid)
    graficos(fechas_array, alturas_masked, stid)


#-------------------------------------
#           EJECUCIÓN
#-------------------------------------

if __name__ == "__main__":
    analisis_hidrometrico_completo("rio paraguay.txt","Río Paraguay")




#%%

    
    
    
    
   
    
    
      
    
    
    
    
    
    
    
    
    
    
    
    
    
    
                                
             
             
             
             
             
             
             
             
             
             
             
             
             
             
             
             
             
             
             
             
             
             
             
             
   
             
             
             
             
             
             
             
             
             
             
             
             
             
             
             
             
             
             
             
             
             
             
             
             
             
  
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
    