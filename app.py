"""Dashboard de mortalidad en Colombia, año 2019 (datos DANE, EEVV).

Ejecución local:
    python app.py
Producción (Render):
    gunicorn app:server
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, dash_table, dcc, html

DATA = Path(__file__).parent / "data"

# ---------- Carga de datos ----------
mort = pd.read_csv(DATA / "mortalidad_2019.csv.gz", dtype=str)
mort["mes"] = mort["mes"].astype(int)
municipios = pd.read_csv(DATA / "municipios.csv", dtype=str)
causas = pd.read_csv(DATA / "causas.csv", dtype=str)

nombre_mun = dict(zip(municipios["cod_mun"], municipios["municipio"]))
nombre_dep = dict(zip(municipios["cod_dep"], municipios["departamento"]))
nombre_causa = dict(zip(causas["codigo"], causas["nombre"]))

mort["municipio"] = mort["cod_mun"].map(nombre_mun).fillna(mort["cod_mun"])
mort["departamento"] = mort["cod_dep"].map(nombre_dep)

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
SEXO = {"1": "Hombres", "2": "Mujeres", "3": "Sin dato"}

# Grupos de edad según la tabla de la actividad (códigos DANE de GRUPO_EDAD1).
ETAPAS = [
    ("Mortalidad neonatal", range(0, 5)),
    ("Mortalidad infantil", range(5, 7)),
    ("Primera infancia", range(7, 9)),
    ("Niñez", range(9, 11)),
    ("Adolescencia", range(11, 12)),
    ("Juventud", range(12, 14)),
    ("Adultez temprana", range(14, 17)),
    ("Adultez intermedia", range(17, 20)),
    ("Vejez", range(20, 25)),
    ("Longevidad / Centenarios", range(25, 29)),
    ("Edad desconocida", range(29, 30)),
]
etapa_de = {str(c): nombre for nombre, rango in ETAPAS for c in rango}
ORDEN_ETAPAS = [nombre for nombre, _ in ETAPAS]
mort["etapa"] = mort["grupo_edad"].map(etapa_de).fillna("Edad desconocida")

# Homicidios: agresión con disparo de arma de fuego (códigos X95x).
homicidios = mort[mort["cod_muerte"].str.startswith("X95")]

# Coordenadas por departamento (promedio de sus municipios) para el mapa.
centros = (municipios.assign(lon=municipios["lon"].astype(float),
                             lat=municipios["lat"].astype(float))
           .groupby(["cod_dep", "departamento"], as_index=False)[["lon", "lat"]]
           .mean())
muertes_dep = mort.groupby("cod_dep").size().rename("muertes")
centros = centros.merge(muertes_dep, left_on="cod_dep", right_index=True, how="left")

# ---------- Figuras ----------

def figura_mapa():
    fig = px.scatter_geo(
        centros, lon="lon", lat="lat", size="muertes", color="muertes",
        hover_name="departamento", hover_data={"muertes": True, "lon": False, "lat": False},
        color_continuous_scale="Reds", title="Muertes por departamento (tamaño y color)",
    )
    fig.update_geos(
        scope="south america", lonaxis_range=[-80, -66], lataxis_range=[-4.5, 13],
        showland=True, landcolor="#f4f1ea", showcountries=True,
    )
    fig.update_layout(margin=dict(l=0, r=0, t=50, b=0), height=500)
    return fig


def figura_linea(departamento):
    datos = mort if departamento == "Todos" else mort[mort["cod_dep"] == departamento]
    total = datos.groupby("mes").size().reindex(range(1, 13), fill_value=0)
    fig = px.line(x=MESES, y=total.values, markers=True,
                  labels={"x": "Mes", "y": "Muertes"},
                  title="Muertes por mes en 2019")
    fig.update_traces(line_color="#b91c1c")
    fig.update_layout(height=380)
    return fig


def figura_homicidios():
    top = (homicidios.groupby("cod_mun").size().nlargest(5)
           .rename(index=nombre_mun).sort_values())
    fig = px.bar(x=top.values, y=top.index, orientation="h",
                 labels={"x": "Homicidios (X95)", "y": ""},
                 title="5 ciudades con más homicidios (X95)")
    fig.update_traces(marker_color="#b91c1c")
    fig.update_layout(height=380)
    return fig


def figura_menor_mortalidad():
    conteo = mort.groupby("cod_mun").size().nsmallest(10)
    nombres = conteo.rename(index=nombre_mun)
    fig = px.pie(names=nombres.index, values=nombres.values,
                 title="10 municipios con menor número de muertes")
    fig.update_traces(textinfo="label+value")
    fig.update_layout(height=380, showlegend=False)
    return fig


def figura_sexo_departamento():
    tabla = (mort.assign(sexo_txt=mort["sexo"].map(SEXO).fillna("Sin dato"))
             .groupby(["departamento", "sexo_txt"]).size().reset_index(name="muertes"))
    orden = (tabla.groupby("departamento")["muertes"].sum()
             .sort_values(ascending=False).index.tolist())
    fig = px.bar(tabla, x="departamento", y="muertes", color="sexo_txt",
                 barmode="stack", category_orders={"departamento": orden},
                 labels={"departamento": "", "muertes": "Muertes", "sexo_txt": "Sexo"},
                 title="Muertes por sexo en cada departamento",
                 color_discrete_map={"Hombres": "#1f2937", "Mujeres": "#e11d48",
                                     "Sin dato": "#9ca3af"})
    fig.update_layout(height=480, xaxis_tickangle=-60)
    return fig


def figura_edad():
    fig = px.histogram(mort, x="etapa", category_orders={"etapa": ORDEN_ETAPAS},
                       labels={"etapa": "Etapa de vida", "count": "Muertes"},
                       title="Distribución de muertes por etapa de la vida")
    fig.update_traces(marker_color="#1f2937")
    fig.update_layout(height=420, xaxis_tickangle=-30, yaxis_title="Muertes")
    return fig


def tabla_causas():
    conteo = mort.groupby("cod_muerte").size().nlargest(10)
    return pd.DataFrame({
        "Código": conteo.index,
        "Causa": [nombre_causa.get(c, "Sin nombre en catálogo") for c in conteo.index],
        "Casos": conteo.values,
    })


# ---------- Indicadores ----------
total = len(mort)
total_hom = len(homicidios)
total_sui = int((mort["manera"] == "Suicidio").sum())


def tarjeta(titulo, valor):
    return html.Div([
        html.Div(titulo, style={"fontSize": "14px", "color": "#6b7280"}),
        html.Div(f"{valor:,}".replace(",", "."), style={"fontSize": "28px", "fontWeight": "bold"}),
    ], style={"background": "white", "padding": "16px", "borderRadius": "8px",
              "boxShadow": "0 1px 3px rgba(0,0,0,0.1)", "flex": "1", "minWidth": "180px"})


def seccion(*hijos):
    return html.Div(list(hijos), style={"background": "white", "padding": "16px",
                                         "borderRadius": "8px", "marginBottom": "16px",
                                         "boxShadow": "0 1px 3px rgba(0,0,0,0.1)"})


opciones_dep = [{"label": "Todos los departamentos", "value": "Todos"}] + [
    {"label": nombre, "value": cod}
    for cod, nombre in sorted(nombre_dep.items(), key=lambda x: x[1])
]

# ---------- Aplicación ----------
app = Dash(__name__, title="Mortalidad Colombia 2019")
server = app.server

app.layout = html.Div(style={"fontFamily": "Arial, sans-serif", "background": "#f3f4f6",
                             "padding": "24px", "minHeight": "100vh"}, children=[
    html.H1("Mortalidad en Colombia, 2019", style={"marginTop": "0"}),
    html.P("Fuente: DANE, Estadísticas Vitales (EEVV) 2019. Defunciones no fetales.",
           style={"color": "#4b5563"}),

    html.Div([
        tarjeta("Total de muertes", total),
        tarjeta("Homicidios (X95)", total_hom),
        tarjeta("Suicidios", total_sui),
    ], style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "marginBottom": "16px"}),

    seccion(dcc.Graph(figure=figura_mapa())),

    seccion(
        html.Label("Departamento para la gráfica mensual:"),
        dcc.Dropdown(id="filtro-dep", options=opciones_dep, value="Todos", clearable=False),
        dcc.Graph(id="grafica-mes"),
    ),

    html.Div([
        html.Div(seccion(dcc.Graph(figure=figura_homicidios())), style={"flex": "1", "minWidth": "300px"}),
        html.Div(seccion(dcc.Graph(figure=figura_menor_mortalidad())), style={"flex": "1", "minWidth": "300px"}),
    ], style={"display": "flex", "gap": "16px", "flexWrap": "wrap"}),

    seccion(html.H3("10 principales causas de muerte"),
            dash_table.DataTable(
                data=tabla_causas().to_dict("records"),
                columns=[{"name": c, "id": c} for c in ["Código", "Causa", "Casos"]],
                style_table={"overflowX": "auto"},
                style_cell={"textAlign": "left", "padding": "8px", "fontSize": "14px"},
                style_header={"fontWeight": "bold", "background": "#f9fafb"},
            )),

    seccion(dcc.Graph(figure=figura_sexo_departamento())),
    seccion(dcc.Graph(figure=figura_edad())),
])


@app.callback(Output("grafica-mes", "figure"), Input("filtro-dep", "value"))
def actualizar_mes(departamento):
    return figura_linea(departamento)


if __name__ == "__main__":
    app.run(debug=True)
