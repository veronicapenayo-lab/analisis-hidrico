# 💧 Hydrology App — Análisis Hidrométrico

Aplicación web interactiva para el análisis de series de caudales a partir de archivos del **Global Runoff Data Centre (GRDC)**. Desarrollada en Python con Streamlit.

🔗 **[Ver aplicación en vivo](https://hydrologyapp.streamlit.app/)**  
📁 **[Repositorio GitHub](https://github.com/veronicapenayo-lab)**

---

## ¿Qué hace?

Permite cargar una o más series hidrométric as en formato `.txt` (GRDC) y genera automáticamente:

- **Estadísticas básicas** — media, máximo, mínimo, mediana, coeficiente de variación
- **Control de calidad** — conteo de datos observados y faltantes
- **Evolución temporal** — serie completa de caudales diarios
- **Ciclo anual** — caudal medio mensual
- **Curva de duración** — porcentaje del tiempo excedido
- **Análisis de frecuencia de crecidas** — ajuste de distribución de Gumbel con estimación de caudales de diseño para T = 2, 5, 10, 25, 50, 100, 200 y 500 años
- **Exportación** — informe completo descargable en formato Excel

---

## Análisis de frecuencia de crecidas

El módulo de frecuencia extrae los **máximos anuales** de la serie y ajusta una distribución de **Gumbel (GEV tipo I)** por el método de momentos.

Los parámetros se estiman como:

```
α = σ · √6 / π       (parámetro de escala)
u = μ - 0.5772 · α   (parámetro de posición)
```

El caudal asociado a un período de retorno T es:

```
Q(T) = u + α · (-ln(-ln(1 - 1/T)))
```

La bondad del ajuste se evalúa con el **test de Kolmogorov-Smirnov al 95%**. Los resultados se presentan en una tabla de caudales de diseño y en un gráfico de papel de probabilidad de Gumbel.

---

## Formato de datos

La app acepta archivos `.txt` en formato estándar GRDC, con separador `;` y valores faltantes codificados como `-999`. Ejemplo:

```
# Station: RIO EJEMPLO
# ...encabezado GRDC...
1980-01-01;  1;  1;  432.50;  ---
1980-01-02;  1;  2;  -999.000;  ---
1980-01-03;  1;  3;  418.20;  ---
```

---

## Instalación local

```bash
git clone https://github.com/veronicapenayo-lab/hydrology-app
cd hydrology-app
pip install -r requirements.txt
streamlit run hidrology_app.py
```

**requirements.txt**
```
streamlit
numpy
pandas
matplotlib
scipy
```

---

## Tecnologías

| Herramienta | Uso |
|-------------|-----|
| Python 3.x | Lenguaje principal |
| Streamlit | Interfaz web |
| Pandas / NumPy | Procesamiento de datos |
| Matplotlib | Visualizaciones |
| SciPy | Estadística |

---

## Próximas mejoras

- [ ] Comparación visual entre estaciones (superposición de series y curvas de duración)
- [ ] Interpretación automática del régimen hidrológico (pluvial / nival / mixto)
- [ ] Ajuste de distribución Log-Pearson III como alternativa a Gumbel
- [ ] Mejoras visuales de interfaz

---

## Sobre el proyecto

Desarrollado por **Verónica Penayo** como herramienta de análisis hidrométrico aplicada a datos reales de cuencas sudamericanas.  
Estudiante de Ingeniería en Recursos Hídricos — Facultad de Ingeniería y Ciencias Hídricas, Universidad Nacional del Litoral (FICH-UNL).

---

*Los datos de ejemplo utilizados pertenecen a estaciones del GRDC (Global Runoff Data Centre, BfG, Koblenz, Alemania).*
