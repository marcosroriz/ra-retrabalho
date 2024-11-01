#!/usr/bin/env python
# coding: utf-8

# Cores do plotly
import plotly.express as px

# Arquivo com icones e cores do tema
# Ícones
ICONE_INDICADOR_SUBINDO = "emojione-monotone:up-right-arrow"
ICONE_INDICADOR_DESCENDO = "emojione-monotone:down-right-arrow"
ICONE_INDICADOR_PADRAO = "pajamas:dash"
ICONE_INDICADOR_TAMANHO = "radix-icons:size"
ICONE_ESTRADA = "vaadin:road"
ICONE_MEDIA = "icon-park:average"
ICONE_ONIBUS = "mdi:bus"
ICONE_FROTA_ONIBUS = "mdi:bus-multiple"
ICONE_VIAGEM = "bx:trip"
ICONE_DUVIDA = "mingcute:question-fill"
ICONE_ERRO = "material-symbols:error"

# Cores do tema Set2
# https://loading.io/color/feature/Pastel2-8/
# https://loading.io/color/feature/Set2-8/
# https://loading.io/color/feature/Dark2-8/
FONTE_GRAFICOS = "Source Sans Pro"
FONTE_TAMANHO = 14
PALETA_CORES_QUALITATIVA = px.colors.qualitative.D3
CORES_GRAFICO_PIZZA = px.colors.qualitative.D3
PASTEL2_COLORS = ["#b3e2cd", "#fdcdac", "#cbd5e8", "#f4cae4", "#e6f5c9", "#fff2ae", "#f1e2cc", "#cccccc"]
SET2_COLORS = ["#66c2a5", "#fc8d62", "#8da0cb", "#e78ac3", "#a6d854", "#ffd92f", "#e5c494", "#b3b3b3"]
DARK2_COLORS = ["#1b9e77", "#d95f02", "#7570b3", "#e7298a", "#66a61e", "#e6ab02", "#a6761d", "#666666"]

COR_SUCESSO = PASTEL2_COLORS[4]
COR_SUCESSO_1 = SET2_COLORS[4]
COR_SUCESSO_2 = DARK2_COLORS[4]

COR_ERRO = PASTEL2_COLORS[1]
COR_ERRO_1 = SET2_COLORS[1]
COR_ERRO_2 = DARK2_COLORS[1]

COR_BASELINE = PASTEL2_COLORS[2]
COR_BASELINE_1 = SET2_COLORS[2]
COR_BASELINE_2 = DARK2_COLORS[2]

COR_ALERTA = PASTEL2_COLORS[5]
COR_ALERTA_1 = SET2_COLORS[5]
COR_ALERTA_2 = DARK2_COLORS[5]
