"""Prepara los datos del DANE (mortalidad 2019) para la aplicación Dash.

Lee los Excel originales de la carpeta datos_fuente/ y guarda archivos
CSV ligeros en la carpeta data/, que es la que usa app.py.

Uso (desde la carpeta dashboard, con el entorno virtual activo):
    python procesar_datos.py
"""
from pathlib import Path

import pandas as pd

FUENTE = Path("datos_fuente")
SALIDA = Path("data")
SALIDA.mkdir(exist_ok=True)

ARCHIVO_MORTALIDAD = FUENTE / "NoFetal2019.xlsx"
ARCHIVO_CAUSAS = FUENTE / "CodigosDeMuerte.xlsx"
ARCHIVO_DIVIPOLA = FUENTE / "Divipola.xlsx"


def leer_municipios():
    """Une nombres (Hoja1) con coordenadas (Hoja3) de cada municipio."""
    nombres = pd.read_excel(ARCHIVO_DIVIPOLA, sheet_name="Hoja1", dtype=str)
    nombres = nombres[["COD_DANE", "COD_DEPARTAMENTO", "DEPARTAMENTO", "MUNICIPIO"]]
    nombres.columns = ["cod_mun", "cod_dep", "departamento", "municipio"]

    # Hoja3 tiene dos filas de encabezado y las coordenadas usan coma decimal.
    coords = pd.read_excel(ARCHIVO_DIVIPOLA, sheet_name="Hoja3", header=None,
                           dtype=str, skiprows=2)
    coords = coords.iloc[:, [2, 5, 6]]
    coords.columns = ["cod_mun", "lon", "lat"]
    coords["lon"] = coords["lon"].str.replace(",", ".").astype(float)
    coords["lat"] = coords["lat"].str.replace(",", ".").astype(float)

    municipios = nombres.merge(coords, on="cod_mun", how="left")
    municipios.to_csv(SALIDA / "municipios.csv", index=False)
    print(f"Municipios: {len(municipios)}")
    return municipios


def leer_causas():
    """Catálogo CIE-10: código de 3 y de 4 caracteres con su descripción."""
    # La hoja Final tiene 8 filas de texto antes del encabezado.
    catalogo = pd.read_excel(ARCHIVO_CAUSAS, sheet_name="Final", header=8, dtype=str)
    filas = []
    for codigo_col, nombre_col in [(2, 3), (4, 5)]:
        parte = catalogo.iloc[:, [codigo_col, nombre_col]].dropna()
        parte.columns = ["codigo", "nombre"]
        filas.append(parte)
    causas = pd.concat(filas).drop_duplicates("codigo")
    causas["codigo"] = causas["codigo"].str.strip()
    causas.to_csv(SALIDA / "causas.csv", index=False)
    print(f"Causas en catálogo: {len(causas)}")


def leer_mortalidad():
    """Registros de defunciones no fetales de 2019, solo con las columnas usadas."""
    columnas = {
        "COD_DANE": "cod_mun",
        "MES": "mes",
        "SEXO": "sexo",
        "GRUPO_EDAD1": "grupo_edad",
        "MANERA_MUERTE": "manera",
        "COD_MUERTE": "cod_muerte",
    }
    datos = pd.read_excel(ARCHIVO_MORTALIDAD, sheet_name="No_Fetales_2019",
                          usecols=list(columnas), dtype=str)
    datos = datos.rename(columns=columnas)
    datos["cod_muerte"] = datos["cod_muerte"].str.strip()
    datos["cod_dep"] = datos["cod_mun"].str[:2]
    datos.to_csv(SALIDA / "mortalidad_2019.csv.gz", index=False, compression="gzip")
    print(f"Registros de mortalidad: {len(datos)}")


if __name__ == "__main__":
    leer_municipios()
    leer_causas()
    leer_mortalidad()
    print("Listo. Archivos guardados en la carpeta data/")
