#!/usr/bin/env python
# coding: utf-8

# Dashboard de RETRABALHO para o projeto RA / CEIA-UFG

# Dotenv
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Importar bibliotecas do dash
import dash
from dash import Dash, _dash_renderer, html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
import plotly.express as px
import plotly.io as pio
import plotly.graph_objs as go

# Extensões
import dash_mantine_components as dmc
from dash.exceptions import PreventUpdate
from dash_iconify import DashIconify

# Tema
import tema

# Locale
import locale

# Locale
locale.setlocale(locale.LC_ALL, "pt_BR")

# Versão do React
_dash_renderer._set_react_version("18.2.0")

# Configurações de cores e temas
TEMA = dbc.themes.LUMEN
pio.templates.default = "plotly"
pio.templates["plotly"]["layout"]["colorway"] = tema.PALETA_CORES_QUALITATIVA

# Stylesheets do Mantine + nosso tema
stylesheets = [
    TEMA,
    "https://unpkg.com/@mantine/dates@7/styles.css",
    "https://unpkg.com/@mantine/code-highlight@7/styles.css",
    "https://unpkg.com/@mantine/charts@7/styles.css",
    "https://unpkg.com/@mantine/carousel@7/styles.css",
    "https://unpkg.com/@mantine/notifications@7/styles.css",
    "https://unpkg.com/@mantine/nprogress@7/styles.css",
]

# Scripts
scripts = [
    "https://cdnjs.cloudflare.com/ajax/libs/dayjs/1.10.8/dayjs.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/dayjs/1.10.8/locale/pt.min.js",
    "https://cdn.plot.ly/plotly-locale-pt-br-latest.js",
]

# Seta o tema padrão do plotly
pio.templates["tema"] = go.layout.Template(
    layout=go.Layout(
        font=dict(
            family=tema.FONTE_GRAFICOS,
            size=tema.FONTE_TAMANHO,  # Default font size
        ),
        colorway=tema.PALETA_CORES_QUALITATIVA,
    )
)

# Seta o tema
pio.templates.default = "tema"

# Dash
app = Dash("Dashboard de OSs", external_stylesheets=stylesheets, external_scripts=scripts, use_pages=True)

# Server
server = app.server

# Cabeçalho
header = dmc.Group(
    [
        dmc.Burger(id="burger-button", opened=False, hiddenFrom="md"),
        html.Img(src=app.get_asset_url("logo.png"), height=40),
        dmc.Text(["RA-UFG"], size="2rem", fw=700),
    ],
    justify="flex-start",
)

# Menu
navbar = dcc.Loading(
    dmc.ScrollArea(
        [
            dbc.Nav(
                [
                    dbc.NavLink(page["name"], href=page["relative_path"], active="exact")
                    for page in dash.page_registry.values()
                ],
                vertical=True,
                pills=True,
            )
        ],
        # [
        #     dmc.NavLink(
        #         label=page["name"], href=page["relative_path"], leftSection=DashIconify(icon=page["icon"], width=16), fs="xl"
        #     )
        #     for page in dash.page_registry.values()
        # ],
        # [
        #     dbc.Nav(
        #         [
        #             dbc.NavLink(page["name"], href=page["relative_path"], active="exact")
        #             for page in dash.page_registry.values()
        #         ],
        #         vertical=True,
        #         pills=True,
        #     )
        # ],
        offsetScrollbars=True,
        type="scroll",
        style={"height": "100%"},
    ),
)

# Corpo do app
app_shell = dmc.AppShell(
    [
        dmc.AppShellHeader(header, p=24, style={"background-color": "#f8f9fa"}),
        dmc.AppShellNavbar(
            navbar,
            p=24,
            # style={
            #     "background-color": "#f8f9fa",
            # },
        ),
        dmc.AppShellMain(
            dmc.DatesProvider(children=dbc.Container([dash.page_container], fluid=True), settings={"locale": "pt"}),
        ),
    ],
    header={"height": 90},
    padding="xl",
    navbar={
        "width": 300,
        "breakpoint": "md",
        "collapsed": {"mobile": True},
    },
    id="app-shell",
)

app.layout = dmc.MantineProvider(app_shell)


@callback(
    Output("app-shell", "navbar"),
    Input("burger-button", "opened"),
    State("app-shell", "navbar"),
)
def navbar_is_open(opened, navbar):
    navbar["collapsed"] = {"mobile": not opened}
    return navbar


if __name__ == "__main__":
    APP_DEBUG = bool(os.getenv("APP_DEBUG", "True"))
    APP_PORT = os.getenv("APP_PORT", 8050)

    app.run(debug=APP_DEBUG, port=APP_PORT)

# if __name__ == '__main__':
#     port = int(os.environ.get("PORT", 8050))
#     print(f"Running on port {port}")
#     app.run_server(debug=False, host='0.0.0.0', port=port)
