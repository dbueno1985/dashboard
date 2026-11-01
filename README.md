# Mortalidad en Colombia 2019: dashboard con Plotly y Dash

Esta actividad fue realizada en equipo por los ingenieros Daniel Palacio y Deicer Bueno



## Introducción del proyecto

Aplicación web interactiva que muestra las defunciones no fetales registradas en Colombia durante 2019, a partir de los datos de Estadísticas Vitales (EEVV) del DANE. Permite ver dónde se concentran las muertes, cuándo ocurren, qué causas las producen y cómo se distribuyen por sexo y por etapa de la vida.

## Objetivo

Identificar patrones demográficos, regionales y temporales de la mortalidad en Colombia en 2019, y presentarlos en gráficos que se entienden sin conocer la estructura de los archivos del DANE.

## Estructura del proyecto

```
dashboard/
├── app.py                  Aplicación Dash (gráficos, tabla y callbacks)
├── procesar_datos.py       Convierte los Excel del DANE en CSV ligeros
├── requirements.txt        Librerías y versiones necesarias
├── Procfile                Comando de arranque para la plataforma de despliegue
├── data/                   Datos listos para la app (generados por procesar_datos.py)
│   ├── mortalidad_2019.csv.gz
│   ├── municipios.csv
│   └── causas.csv
├── datos_fuente/           Excel originales del DANE (no se suben a GitHub)
└── docs/capturas/          Capturas de pantalla usadas en este README
```

## Requisitos

- Python 3.11 o superior
- dash 4.5.0
- plotly 7.1.0
- pandas 3.0.5
- gunicorn 26.2.0 (solo para producción)
- openpyxl 3.1.5 (solo para ejecutar `procesar_datos.py`)

Todas las versiones están fijadas en `requirements.txt`.

## Software

- Python: lenguaje de programación del análisis y de la aplicación.
- pandas: lectura, limpieza y agregación de los registros.
- Plotly: gráficos interactivos (mapa, líneas, barras, circular, histograma).
- Dash: marco para construir la aplicación web y sus callbacks.
- gunicorn: servidor de producción.
- Git y GitHub: control de versiones y repositorio público.

## Instalación

Clonar el repositorio y ejecutar la aplicación localmente:

```bash
git clone https://github.com/USUARIO/dashboard.git
cd dashboard
python -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Abrir http://127.0.0.1:8050 en el navegador.

Si se quieren regenerar los datos desde los Excel originales, colocar los archivos en `datos_fuente/` con estos nombres (`NoFetal2019.xlsx`, `CodigosDeMuerte.xlsx`, `Divipola.xlsx`) y ejecutar:

```bash
python procesar_datos.py
```

## Despliegue en Render

1. Subir el proyecto a GitHub (sin la carpeta `datos_fuente/` ni `.venv/`).
2. En render.com, crear un servicio nuevo de tipo Web Service y conectar el repositorio.
3. Configurar:
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:server`
4. Esperar a que el estado sea "Live" y abrir la URL pública que entrega Render.

El archivo `Procfile` contiene el mismo comando de arranque para otras plataformas.

## Visualizaciones y hallazgos

Los datos cubren 244.355 defunciones no fetales. La captura completa está en `docs/capturas/panel_completo.png`.

**Indicadores generales.** Se registraron 244.355 muertes en 2019. De ellas, 9.273 corresponden a homicidios por arma de fuego (códigos X95) y 2.930 a suicidios. La muerte natural explica el 87,0 % de los casos.

**Mapa por departamento.** Las burbujas son más grandes y más oscuras donde hay más muertes. Bogotá D.C. encabeza con 38.760 casos (15,9 % del total), seguida de Antioquia con 34.473 y Valle del Cauca con 28.443. Como el mapa muestra conteos y no tasas, los departamentos más poblados aparecen arriba por tamaño, no solo por riesgo. Para comparar riesgos habría que dividir entre la población de cada departamento, dato que no está en los archivos entregados.

**Gráfico de líneas por mes.** El total mensual oscila entre 17.974 (febrero) y 21.678 (diciembre). Febrero es el mes más bajo, pero tiene 28 días; por día, la diferencia es menor. Con el menú se puede ver la curva de cada departamento.

**Homicidios por ciudad.** Santiago de Cali registra 971 homicidios por arma de fuego, seguida de Bogotá D.C. (601), Medellín (428), Barranquilla (260) y San José de Cúcuta (206). Las cinco suman 2.466 casos, es decir, el 26,6 % de los homicidios por arma de fuego del país.

**Municipios con menor número de muertes.** Son diez municipios con una sola muerte registrada cada uno. Muchos otros municipios tienen también un caso, así que los diez mostrados son una selección entre empates. El gráfico describe el conteo bruto, no una tasa.

**Principales causas de muerte.** El infarto agudo de miocardio encabeza la lista con 35.088 casos, equivalente al 14,4 % del total. Le siguen la enfermedad pulmonar obstructiva crónica (7.210 y 6.445 casos en sus dos códigos) y la neumonía (5.798). El primer homicidio aparece en el puesto siete, con 4.396 casos por disparo de otras armas de fuego.

**Muertes por sexo.** Hombres suman 134.573 muertes (55,1 %) y mujeres 109.689 (44,9 %). El gráfico apilado por departamento permite comparar cada uno; este resumen no calcula diferencias departamento por departamento.

**Distribución por etapa de la vida.** La vejez (60 a 84 años) concentra 115.453 muertes y la longevidad (85 años o más) 56.061. Entre las dos suman el 70,2 % del total. La mortalidad neonatal (4.520) y la infantil (2.771) son pequeñas en número absoluto, pero corresponden a edades donde cada caso tiene un peso social muy alto.

## Notas metodológicas

- Homicidios: se cuentan los registros cuyo código CIE-10 empieza por X95, según indica la actividad.
- Edades: los códigos de GRUPO_EDAD1 se agrupan según la tabla de la actividad.
- Sexo: código 1 hombres, código 2 mujeres y código 3 "sin dato".
- Todos los conteos son de registros, no tasas por cada 100.000 habitantes.
