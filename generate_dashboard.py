"""Dashboard LEM — visualizações Plotly/Dash sobre indicadores mensais do LEM.

Lê o CSV consolidado (gerado pelo script de padronização a partir das
planilhas anuais em Excel), calcula KPIs de topo e monta um conjunto de
gráficos interativos filtráveis por ano: saúde, atendimentos, ranking de
categorias, educação, dinâmica populacional, profissionalização e perfil
de interfaces de rede.
"""

import pandas as pd
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output


BG = "#0F1117"
CARD_BG = "#1A1D27"
BORDER = "#2A2D3E"
TEXT = "#E8EAF6"
MUTED = "#7B7F9E"

MONTHS = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]
YEARS = [2021, 2022, 2023, 2024, 2025]
YEAR_COLORS = {2021: "#4E9AF1", 2022: "#F4A261", 2023: "#2A9D8F", 2024: "#E76F51", 2025: "#8338EC"}

# Categorias de saúde (chave normalizada -> rótulo de exibição), na ordem
# em que devem aparecer dentro de cada mês no gráfico de saúde.
HEALTH_CATEGORIES = [
    ("INTERNACOES", "Internações"),
    ("SAUDE CLINICA", "Saúde Clínica"),
    ("SAUDE MENTAL", "Saúde Mental"),
]


def load_data(path: str = "IPP_LEMs.csv") -> pd.DataFrame:
    """Carrega o CSV consolidado gerado pelo script de padronização.

    Args:
        path: Caminho para o arquivo CSV com as colunas categorias,
            JAN..DEZ, TOTAL e ANO.

    Returns:
        pd.DataFrame: Dados consolidados de todos os anos disponíveis.
    """
    return pd.read_csv(path)


def get_macro_area(categoria: str) -> str:
    """Classifica uma categoria bruta em uma macroárea temática do LEM.

    Usada para agrupar categorias individuais (ex.: "SAUDE MENTAL",
    "NOVOS INGRESSOS") em grandes temas (ex.: "Saúde", "Dinâmica
    Populacional"), útil para análises ou visualizações agregadas por tema.

    Args:
        categoria: Nome da categoria já normalizado (maiúsculo, sem acento).

    Returns:
        str: Nome da macroárea correspondente, ou "Outros / Gestão" caso
        nenhuma regra corresponda.
    """
    categoria = str(categoria).upper()
    if "INTERFACE" in categoria:
        return "Interfaces de Rede"
    elif "ATENDIMENTO" in categoria or "VISITAS" in categoria or "PIAS" in categoria:
        return "Atendimentos e Relatórios"
    elif "SAUDE" in categoria or "INTERNACOES" in categoria:
        return "Saúde"
    elif "ENSINO" in categoria or "SCFV" in categoria or "REFORCO" in categoria:
        return "Educação"
    elif "CURSO" in categoria or "MERCADO" in categoria:
        return "Profissionalização"
    elif "INGRESSOS" in categoria or "DESLIGAMENTOS" in categoria or "EVASAO" in categoria or "TRANSFERENCIAS" in categoria:
        return "Dinâmica Populacional"
    return "Outros / Gestão"


def kpis(df: pd.DataFrame) -> tuple:
    """Calcula os KPIs exibidos nos cartões de topo do dashboard.

    Args:
        df: DataFrame consolidado com as colunas categorias e TOTAL.

    Returns:
        tuple: (atendimentos, ingressos, desligamentos, matrículas), todos
        somados sobre todo o período disponível em `df`.
    """
    def total(cat):
        return int(df.loc[df.categorias == cat, "TOTAL"].sum())

    atend = total("ATENDIMENTOS INDVIDUAL") + total("ATEDIMENTO FAMILIAR")
    ingr = total("NOVOS INGRESSOS")
    desl = total("DESLIGAMENTOS")
    mats = df[df.categorias.str.contains("MATRICULADOS", na=False)]["TOTAL"].sum()
    return atend, ingr, desl, int(mats)


def _apply_theme(fig: go.Figure, title: str, **layout_kwargs) -> go.Figure:
    """Aplica o tema visual padrão (fundo escuro, fontes, grid) do dashboard.

    Centraliza as opções de estilo compartilhadas por todos os gráficos,
    garantindo consistência visual entre eles e evitando repetição de
    código nas funções `fig_*`.

    Args:
        fig: Figura Plotly a ser estilizada (alterada in-place).
        title: Título exibido no topo do gráfico.
        **layout_kwargs: Parâmetros adicionais de `update_layout` (ex.:
            xaxis, yaxis, legend, barmode, polar), mesclados por cima do
            tema padrão — uma chave passada aqui substitui a equivalente
            do tema base.

    Returns:
        go.Figure: A mesma figura recebida, já estilizada.
    """
    base = dict(
        title=dict(text=title, font=dict(size=15, color=TEXT)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT, size=11),
        hoverlabel=dict(bgcolor=CARD_BG, bordercolor=BORDER, font=dict(color=TEXT)),
        margin=dict(t=50, l=10, r=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, font=dict(size=9)),
    )
    base.update(layout_kwargs)
    fig.update_layout(**base)
    return fig


def fig_saude_mensal(df: pd.DataFrame, anos: list) -> go.Figure:
    """Gráfico de Barras Empilhadas e Agrupadas dos indicadores de Saúde.

    Para cada mês do ano são exibidas 3 barras distintas — uma para cada
    indicador de saúde (Internações, Saúde Clínica e Saúde Mental) — e,
    dentro de cada uma delas, os valores aparecem empilhados por ano
    (segmento colorido = ano). Isso permite comparar, lado a lado dentro
    do mesmo mês, o volume de cada indicador, e ao mesmo tempo ver a
    contribuição de cada ano selecionado para aquele total.

    Args:
        df: DataFrame consolidado com as colunas categorias, JAN..DEZ e ANO.
        anos: Lista de anos a serem empilhados dentro de cada barra.

    Returns:
        go.Figure: Figura Plotly de barras com eixo x em duas camadas
        (mês > indicador) e empilhamento por ano.
    """
    # Eixo x de duas camadas: mês (camada externa) e indicador de saúde
    # (camada interna), repetido para os 12 meses.
    eixo_mes, eixo_categoria = [], []
    for mes in MONTHS:
        for _, label in HEALTH_CATEGORIES:
            eixo_mes.append(mes)
            eixo_categoria.append(label)

    fig = go.Figure()
    for ano in sorted(anos):
        sub = df[df["ANO"] == ano]
        valores = []
        for mes in MONTHS:
            for cat_key, _ in HEALTH_CATEGORIES:
                valor = sub.loc[sub["categorias"] == cat_key, mes].sum()
                valores.append(int(valor) if pd.notna(valor) else 0)
        fig.add_trace(
            go.Bar(
                x=[eixo_mes, eixo_categoria],
                y=valores,
                name=str(ano),
                marker_color=YEAR_COLORS.get(ano, "#4E9AF1"),
                hovertemplate=f"Ano {ano}: " + "%{y}<extra></extra>",
            )
        )

    return _apply_theme(
        fig,
        "Indicadores de Saúde por Mês: Internações, Saúde Clínica e Saúde Mental",
        barmode="stack",
        bargap=0.15,
        bargroupgap=0.08,
        xaxis=dict(gridcolor=BORDER),
        yaxis=dict(title="Quantidade", gridcolor=BORDER),
        legend=dict(title="Ano", orientation="h", yanchor="bottom", y=-0.28, font=dict(size=9)),
    )


def fig_linhas(df: pd.DataFrame, anos: list) -> go.Figure:
    """Gráfico de Linhas para a evolução mensal dos atendimentos.

    Traça duas séries temporais — atendimentos individuais e atendimentos
    familiares — concatenando os meses de todos os anos selecionados em
    uma única linha do tempo contínua, facilitando visualizar tendências
    de longo prazo e sazonalidade.

    Args:
        df: DataFrame consolidado com as colunas categorias, JAN..DEZ e ANO.
        anos: Lista de anos a serem incluídos, em sequência, no eixo x.

    Returns:
        go.Figure: Figura Plotly com uma linha por tipo de atendimento.
    """
    fig = go.Figure()
    for nome, cat, cor in [
        ("Individual", "ATENDIMENTOS INDVIDUAL", "#4E9AF1"),
        ("Familiar", "ATEDIMENTO FAMILIAR", "#F4A261"),
    ]:
        x, y = [], []
        for a in sorted(anos):
            r = df[(df.ANO == a) & (df.categorias == cat)]
            for m in MONTHS:
                x.append(f"{m}/{a}")
                y.append(0 if r.empty else r[m].sum())
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                name=nome,
                mode="lines+markers",
                line=dict(color=cor, width=2),
                marker=dict(size=4),
                hovertemplate=f"{nome}: " + "%{y}<extra></extra>",
            )
        )
    return _apply_theme(
        fig,
        "Evolução Mensal dos Atendimentos Individuais e Familiares",
        hovermode="x unified",
        xaxis=dict(title="Mês/Ano", gridcolor=BORDER, tickangle=-45, tickfont=dict(size=8)),
        yaxis=dict(title="Quantidade de Atendimentos", gridcolor=BORDER),
    )


def fig_heat(df: pd.DataFrame, anos: list) -> go.Figure:
    """Mapa de calor com o volume mensal de atendimentos, por ano.

    Soma atendimentos individuais e familiares por mês e exibe a
    intensidade em uma matriz Ano x Mês — cores mais claras indicam meses
    com maior volume de atendimentos.

    Args:
        df: DataFrame consolidado com as colunas categorias, JAN..DEZ e ANO.
        anos: Lista de anos a serem incluídos nas linhas da matriz.

    Returns:
        go.Figure: Figura Plotly do tipo Heatmap.
    """
    cats = ["ATENDIMENTOS INDVIDUAL", "ATEDIMENTO FAMILIAR"]
    anos_ord = sorted(anos)
    z = []
    for a in anos_ord:
        r = df[(df.ANO == a) & (df.categorias.isin(cats))]
        z.append(r[MONTHS].sum().tolist())
    fig = go.Figure(
        go.Heatmap(
            z=z,
            x=MONTHS,
            y=anos_ord,
            colorscale="Viridis",
            colorbar=dict(title="Atendimentos"),
            hovertemplate="Mês: %{x}<br>Ano: %{y}<br>Atendimentos: %{z}<extra></extra>",
        )
    )
    return _apply_theme(
        fig,
        "Intensidade de Atendimentos por Mês e Ano",
        xaxis=dict(title="Mês", gridcolor=BORDER),
        yaxis=dict(title="Ano", gridcolor=BORDER, tickmode="array", tickvals=anos_ord),
    )


def fig_rank(df: pd.DataFrame, anos: list) -> go.Figure:
    """Ranking horizontal das 10 categorias com maior volume total.

    Args:
        df: DataFrame consolidado com as colunas categorias, TOTAL e ANO.
        anos: Lista de anos a serem somados antes de ranquear.

    Returns:
        go.Figure: Figura Plotly de barras horizontais, ordenadas do menor
        para o maior valor (a maior fica no topo do eixo y).
    """
    d = df[df.ANO.isin(anos)].groupby("categorias")["TOTAL"].sum().sort_values().tail(10)
    fig = go.Figure(
        go.Bar(
            x=d.values,
            y=d.index,
            orientation="h",
            marker=dict(color=d.values, colorscale="Blues"),
            hovertemplate="%{y}: %{x}<extra></extra>",
        )
    )
    return _apply_theme(
        fig,
        "Top 10 Categorias por Volume Total de Registros",
        xaxis=dict(title="Quantidade Total", gridcolor=BORDER),
        yaxis=dict(gridcolor=BORDER),
    )


def fig_edu(df: pd.DataFrame, anos: list) -> go.Figure:
    """Gráfico de Barras Agrupadas com o volume por modalidade de ensino.

    Para cada modalidade (Infantil, Regular, EJA, SCFV), soma matriculados
    e crianças/adolescentes aguardando vaga, comparando o total ano a ano.

    Args:
        df: DataFrame consolidado com as colunas categorias, TOTAL e ANO.
        anos: Lista de anos a serem comparados no eixo x.

    Returns:
        go.Figure: Figura Plotly de barras agrupadas por modalidade.
    """
    mods = {
        "Infantil": ("MATRICULADOS (ENSINO INFANTIL)", "AGUARDANDO VAGA (ENSINO INFANTIL)"),
        "Regular": ("MATRICULADOS (ENSINO REGULAR)", "AGUARDANDO VAGA (ENSINO REGULAR)"),
        "EJA": ("MATRICULADOS (ENSINO EJA)", "AGUARDANDO VAGA (ENSINO EJA)"),
        "SCFV": ("MATRICULADOS (SCFV)", "AGUARDANDO VAGA (SCFV)"),
    }
    anos_ord = sorted(anos)
    fig = go.Figure()
    for mod, (a, b) in mods.items():
        vals = []
        for ano in anos_ord:
            x = df[df.ANO == ano]
            vals.append(x.loc[x.categorias.isin([a, b]), "TOTAL"].sum())
        fig.add_trace(
            go.Bar(name=mod, x=anos_ord, y=vals, hovertemplate=f"{mod}: " + "%{y}<extra></extra>")
        )
    return _apply_theme(
        fig,
        "Educação: Matriculados e Aguardando Vaga por Modalidade e Ano",
        barmode="group",
        xaxis=dict(title="Ano", gridcolor=BORDER, tickmode="array", tickvals=anos_ord),
        yaxis=dict(title="Matriculados + Aguardando Vaga", gridcolor=BORDER),
    )


def fig_dinamica_populacional(df: pd.DataFrame, anos: list) -> go.Figure:
    """Gráfico de Linhas para Entradas, Saídas e Evasões.

    Compara, ano a ano, o total de novos ingressos, desligamentos, evasões
    e transferências, permitindo avaliar o saldo de movimentação da casa.

    Args:
        df: DataFrame consolidado com as colunas categorias, TOTAL e ANO.
        anos: Lista de anos a serem plotados no eixo x.

    Returns:
        go.Figure: Figura Plotly com uma linha por indicador de movimentação.
    """
    cats = ["NOVOS INGRESSOS", "DESLIGAMENTOS", "EVASAO", "TRANSFERENCIAS"]
    cores = {"NOVOS INGRESSOS": "#2A9D8F", "DESLIGAMENTOS": "#F4A261", "EVASAO": "#E76F51", "TRANSFERENCIAS": "#4E9AF1"}

    sub = df[df["ANO"].isin(anos)]
    anos_ord = sorted(anos)

    fig = go.Figure()
    for cat in cats:
        valores = [sub[(sub["ANO"] == a) & (sub["categorias"] == cat)]["TOTAL"].sum() for a in anos_ord]
        fig.add_trace(
            go.Scatter(
                x=anos_ord,
                y=valores,
                name=cat.title(),
                mode="lines+markers",
                line=dict(color=cores[cat], width=3),
                marker=dict(size=8),
                hovertemplate=f"{cat.title()}: " + "%{y}<extra></extra>",
            )
        )

    return _apply_theme(
        fig,
        "Dinâmica Populacional: Ingressos, Desligamentos, Evasões e Transferências",
        font=dict(color=TEXT, size=10),
        xaxis=dict(title="Ano", gridcolor=BORDER, tickmode="array", tickvals=anos_ord),
        yaxis=dict(title="Quantidade", gridcolor=BORDER),
        legend=dict(orientation="h", yanchor="bottom", y=-0.35, font=dict(size=8)),
    )


def fig_profissionalizacao(df: pd.DataFrame, anos: list) -> go.Figure:
    """Gráfico de Barras Agrupadas contrastando Encaminhados vs Inseridos.

    Compara, tanto para cursos profissionalizantes quanto para o mercado
    de trabalho, quantas pessoas foram encaminhadas versus quantas
    efetivamente foram inseridas, somando os anos selecionados.

    Args:
        df: DataFrame consolidado com as colunas categorias, TOTAL e ANO.
        anos: Lista de anos a serem somados antes da comparação.

    Returns:
        go.Figure: Figura Plotly de barras agrupadas (Cursos x Mercado).
    """
    cats = [
        "ENCAMINHADOS PARA CURSO PROFISSIONALIZANTE",
        "INSERIDOS EM CURSO PROFISSIONALIZANTE",
        "ENCAMINHADO PARA MERCADO DE TRABALHO",
        "INSERIDO NO MERCADO DE TRABALHO",
    ]

    sub = df[df["ANO"].isin(anos)]
    totais = {cat: sub[sub["categorias"] == cat]["TOTAL"].sum() for cat in cats}

    fig = go.Figure(
        data=[
            go.Bar(
                name="Cursos Prof.",
                x=["Encaminhados", "Inseridos"],
                y=[
                    totais["ENCAMINHADOS PARA CURSO PROFISSIONALIZANTE"],
                    totais["INSERIDOS EM CURSO PROFISSIONALIZANTE"],
                ],
                marker_color="#8338EC",
                hovertemplate="Cursos Prof. — %{x}: %{y}<extra></extra>",
            ),
            go.Bar(
                name="Mercado Trab.",
                x=["Encaminhados", "Inseridos"],
                y=[
                    totais["ENCAMINHADO PARA MERCADO DE TRABALHO"],
                    totais["INSERIDO NO MERCADO DE TRABALHO"],
                ],
                marker_color="#4E9AF1",
                hovertemplate="Mercado Trab. — %{x}: %{y}<extra></extra>",
            ),
        ]
    )

    return _apply_theme(
        fig,
        "Profissionalização: Encaminhamentos vs. Inserções",
        barmode="group",
        font=dict(color=TEXT, size=10),
        yaxis=dict(title="Quantidade Total", gridcolor=BORDER),
        legend=dict(orientation="h", yanchor="bottom", y=-0.35, font=dict(size=8)),
    )


def fig_radar_interfaces(df: pd.DataFrame, anos: list) -> go.Figure:
    """Gráfico de Radar mostrando o perfil das Interfaces de rede.

    Para cada ano selecionado, desenha um polígono com o volume de
    contatos registrados com quatro redes de interface — socioassistencial,
    judiciário, saúde e educação — facilitando comparar o "formato" da
    atuação de um ano para o outro.

    Args:
        df: DataFrame consolidado com as colunas categorias, TOTAL e ANO.
        anos: Lista de anos a serem desenhados (um polígono por ano).

    Returns:
        go.Figure: Figura Plotly do tipo Scatterpolar.
    """
    interfaces = [
        "INTERFACE COM REDE SOCIOASSISTENCIAL",
        "INTERFACE COM JUDICIARIO",
        "INTERFACE COM SAUDE",
        "INTERFACE COM EDUCACAO",
    ]
    labels = ["Rede Socioassistencial", "Judiciário", "Saúde", "Educação"]

    fig = go.Figure()
    for ano in sorted(anos):
        sub = df[df["ANO"] == ano]
        valores = [sub.loc[sub["categorias"] == i, "TOTAL"].sum() for i in interfaces]

        valores.append(valores[0])
        labels_plot = labels + [labels[0]]

        fig.add_trace(
            go.Scatterpolar(
                r=valores,
                theta=labels_plot,
                fill="toself",
                name=str(ano),
                line_color=YEAR_COLORS.get(ano),
                hovertemplate="%{theta}: %{r}<extra></extra>",
            )
        )

    return _apply_theme(
        fig,
        "Perfil das Interfaces com a Rede de Proteção, por Ano",
        polar=dict(
            radialaxis=dict(visible=True, gridcolor=BORDER),
            angularaxis=dict(gridcolor=BORDER),
            bgcolor="rgba(0,0,0,0)",
        ),
        font=dict(color=TEXT, size=10),
        margin=dict(t=40, b=10, l=30, r=30),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, font=dict(size=8)),
    )


def build_app(csv: str = "IPP_LEMs.csv") -> dash.Dash:
    """Monta e configura a aplicação Dash do Dashboard LEM.

    Carrega os dados consolidados, calcula os KPIs de topo, define o
    layout (filtro de anos, cartões de KPI e 8 visualizações) e registra
    o callback que recalcula todos os gráficos conforme os anos
    selecionados no filtro.

    Args:
        csv: Caminho para o CSV consolidado gerado pelo script de
            padronização (colunas categorias, JAN..DEZ, TOTAL, ANO).

    Returns:
        dash.Dash: Instância da aplicação Dash pronta para ser executada
        (via `.run()`).
    """
    df = load_data(csv)
    app = dash.Dash(__name__)
    a, i, d, m = kpis(df)

    def card(t, v, sub=None):
        """Monta um cartão de KPI com título, valor formatado (pt-BR) e subtítulo opcional."""
        children = [html.H4(t), html.H2(f"{v:,}".replace(",", "."))]
        if sub:
            children.append(html.P(sub, style={"color": MUTED, "fontSize": "12px", "margin": "0"}))
        return html.Div(
            children,
            style={
                "background": CARD_BG,
                "padding": "15px",
                "border": "1px solid " + BORDER,
                "borderRadius": "8px",
                "flex": "1",
            },
        )

    def graph_box(style_extra=None):
        """Gera o dicionário de estilo (cartão escuro) usado pelos contêineres de gráfico."""
        base = {
            "background": CARD_BG,
            "border": "1px solid " + BORDER,
            "borderRadius": "8px",
            "padding": "10px",
        }
        if style_extra:
            base.update(style_extra)
        return base

    app.layout = html.Div(
        style={"background": BG, "color": TEXT, "padding": "20px", "minHeight": "100vh"},
        children=[
            html.H2("Dashboard LEM"),
            dcc.Checklist(
                id="anos",
                options=[{"label": y, "value": y} for y in YEARS],
                value=YEARS,
                inline=True,
                style={"marginBottom": "15px"},
            ),
            html.Div(
                [
                    card("Atendimentos", a, sub="Individual + Familiar"),
                    card("Ingressos", i),
                    card("Desligamentos", d),
                    card("Matrículas", m),
                ],
                style={"display": "flex", "gap": "10px", "marginBottom": "20px"},
            ),
            # g1: NOVO — Saúde (barras empilhadas por ano, agrupadas por mês)
            html.Div(
                dcc.Graph(id="g1", style={"height": "400px"}),
                style=graph_box({"marginBottom": "15px"}),
            ),
            # g2: Atendimentos (linhas)
            html.Div(
                dcc.Graph(id="g2", style={"height": "400px"}),
                style=graph_box({"marginBottom": "15px"}),
            ),
            # g3: Heatmap de atendimentos
            html.Div(
                dcc.Graph(id="g3", style={"height": "400px"}),
                style=graph_box({"marginBottom": "15px"}),
            ),
            # g4: Ranking de categorias
            html.Div(
                dcc.Graph(id="g4", style={"height": "400px"}),
                style=graph_box({"marginBottom": "15px"}),
            ),
            # g5: Educação
            html.Div(
                dcc.Graph(id="g5", style={"height": "400px"}),
                style=graph_box({"marginBottom": "25px"}),
            ),
            # g6, g7, g8: Radar de interfaces / Dinâmica populacional / Profissionalização
            html.Div(
                [
                    html.Div(
                        dcc.Graph(id="g6", style={"height": "100%", "width": "100%"}),
                        style=graph_box({"aspectRatio": "1 / 1", "flex": "1", "minWidth": "0"}),
                    ),
                    html.Div(
                        dcc.Graph(id="g7", style={"height": "100%", "width": "100%"}),
                        style=graph_box({"aspectRatio": "1 / 1", "flex": "1", "minWidth": "0"}),
                    ),
                    html.Div(
                        dcc.Graph(id="g8", style={"height": "100%", "width": "100%"}),
                        style=graph_box({"aspectRatio": "1 / 1", "flex": "1", "minWidth": "0"}),
                    ),
                ],
                style={"display": "flex", "gap": "15px"},
            ),
        ],
    )

    @app.callback(
        Output("g1", "figure"),
        Output("g2", "figure"),
        Output("g3", "figure"),
        Output("g4", "figure"),
        Output("g5", "figure"),
        Output("g6", "figure"),
        Output("g7", "figure"),
        Output("g8", "figure"),
        Input("anos", "value"),
    )
    def upd(anos):
        """Recalcula as 8 figuras do dashboard sempre que o filtro de anos muda."""
        return (
            fig_saude_mensal(df, anos),
            fig_linhas(df, anos),
            fig_heat(df, anos),
            fig_rank(df, anos),
            fig_edu(df, anos),
            fig_radar_interfaces(df, anos),
            fig_dinamica_populacional(df, anos),
            fig_profissionalizacao(df, anos),
        )

    return app


if __name__ == "__main__":
    build_app().run(debug=True)
