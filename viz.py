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


def load_data(path: str = "IPP_LEMs.csv") -> pd.DataFrame:
    return pd.read_csv(path)


def get_macro_area(categoria: str) -> str:
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


def kpis(df):
    def total(cat):
        return int(df.loc[df.categorias == cat, "TOTAL"].sum())

    atend = total("ATENDIMENTOS INDVIDUAL") + total("ATEDIMENTO FAMILIAR")
    ingr = total("NOVOS INGRESSOS")
    desl = total("DESLIGAMENTOS")
    mats = df[df.categorias.str.contains("MATRICULADOS", na=False)]["TOTAL"].sum()
    return atend, ingr, desl, int(mats)


def fig_linhas(df, anos):
    fig = go.Figure()
    for nome, cat, col in [
        ("Individual", "ATENDIMENTOS INDVIDUAL", "#4E9AF1"),
        ("Familiar", "ATEDIMENTO FAMILIAR", "#F4A261"),
    ]:
        x, y = [], []
        for a in anos:
            r = df[(df.ANO == a) & (df.categorias == cat)]
            for m in MONTHS:
                x.append(f"{m}/{a}")
                y.append(0 if r.empty else r[m].sum())
        fig.add_trace(go.Scatter(x=x, y=y, name=nome, mode="lines", line=dict(color=col)))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT),
        title="Atendimentos",
        margin=dict(t=50, l=10, r=10, b=10),
    )
    return fig


def fig_heat(df, anos):
    cats = ["ATENDIMENTOS INDVIDUAL", "ATEDIMENTO FAMILIAR"]
    z = []
    for a in anos:
        r = df[(df.ANO == a) & (df.categorias.isin(cats))]
        z.append(r[MONTHS].sum().tolist())
    fig = go.Figure(go.Heatmap(z=z, x=MONTHS, y=anos, colorscale="Viridis"))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT),
        title="Heatmap",
        margin=dict(t=50, l=10, r=10, b=10),
    )
    return fig


def fig_rank(df, anos):
    d = df[df.ANO.isin(anos)].groupby("categorias")["TOTAL"].sum().sort_values().tail(10)
    fig = go.Figure(go.Bar(x=d.values, y=d.index, orientation="h", marker_color="#4E9AF1"))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT),
        title="Top categorias",
        margin=dict(t=50, l=10, r=10, b=10),
    )
    return fig


def fig_edu(df, anos):
    mods = {
        "Infantil": ("MATRICULADOS (ENSINO INFANTIL)", "AGUARDANDO VAGA (ENSINO INFANTIL)"),
        "Regular": ("MATRICULADOS (ENSINO REGULAR)", "AGUARDANDO VAGA (ENSINO REGULAR)"),
        "EJA": ("MATRICULADOS (ENSINO EJA)", "AGUARDANDO VAGA (ENSINO EJA)"),
        "SCFV": ("MATRICULADOS (SCFV)", "AGUARDANDO VAGA (SCFV)"),
    }
    fig = go.Figure()
    for mod, (a, b) in mods.items():
        vals = []
        for ano in anos:
            x = df[df.ANO == ano]
            vals.append(x.loc[x.categorias.isin([a, b]), "TOTAL"].sum())
        fig.add_trace(go.Bar(name=mod, x=anos, y=vals))
    fig.update_layout(
        barmode="group",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT),
        title="Educação",
        margin=dict(t=50, l=10, r=10, b=10),
    )
    return fig


def fig_dinamica_populacional(df: pd.DataFrame, anos: list) -> go.Figure:
    """Gráfico de Linhas para Entradas, Saídas e Evasões."""
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
            )
        )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT, size=10),
        title="Dinâmica Populacional",
        xaxis=dict(gridcolor=BORDER, tickmode="array", tickvals=anos_ord),
        yaxis=dict(gridcolor=BORDER),
        margin=dict(t=40, l=10, r=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.35, font=dict(size=8)),
    )
    return fig


def fig_profissionalizacao(df: pd.DataFrame, anos: list) -> go.Figure:
    """Gráfico de Barras Agrupadas contrastando Encaminhados vs Inseridos."""
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
            ),
            go.Bar(
                name="Mercado Trab.",
                x=["Encaminhados", "Inseridos"],
                y=[
                    totais["ENCAMINHADO PARA MERCADO DE TRABALHO"],
                    totais["INSERIDO NO MERCADO DE TRABALHO"],
                ],
                marker_color="#4E9AF1",
            ),
        ]
    )

    fig.update_layout(
        barmode="group",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT, size=10),
        title="Encaminhamentos vs Inserções",
        yaxis=dict(gridcolor=BORDER),
        margin=dict(t=40, l=10, r=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.35, font=dict(size=8)),
    )
    return fig


def fig_radar_interfaces(df: pd.DataFrame, anos: list) -> go.Figure:
    """Gráfico de Radar mostrando o perfil das Interfaces."""
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
            )
        )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, gridcolor=BORDER),
            angularaxis=dict(gridcolor=BORDER),
            bgcolor="rgba(0,0,0,0)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT, size=10),
        title="Perfil de Interfaces de Rede",
        margin=dict(t=40, b=10, l=30, r=30),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, font=dict(size=8)),
    )
    return fig


def build_app(csv="IPP_LEMs.csv"):
    df = load_data(csv)
    app = dash.Dash(__name__)
    a, i, d, m = kpis(df)

    def card(t, v, sub=None):
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
            html.Div(
                dcc.Graph(id="g1", style={"height": "400px"}),
                style=graph_box({"marginBottom": "15px"}),
            ),
            html.Div(
                dcc.Graph(id="g2", style={"height": "400px"}),
                style=graph_box({"marginBottom": "15px"}),
            ),
            html.Div(
                dcc.Graph(id="g3", style={"height": "400px"}),
                style=graph_box({"marginBottom": "15px"}),
            ),
            html.Div(
                dcc.Graph(id="g4", style={"height": "400px"}),
                style=graph_box({"marginBottom": "25px"}),
            ),
            html.Div(
                [
                    html.Div(
                        dcc.Graph(id="g5", style={"height": "100%", "width": "100%"}),
                        style=graph_box({"aspectRatio": "1 / 1", "flex": "1", "minWidth": "0"}),
                    ),
                    html.Div(
                        dcc.Graph(id="g6", style={"height": "100%", "width": "100%"}),
                        style=graph_box({"aspectRatio": "1 / 1", "flex": "1", "minWidth": "0"}),
                    ),
                    html.Div(
                        dcc.Graph(id="g7", style={"height": "100%", "width": "100%"}),
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
        Input("anos", "value"),
    )
    def upd(anos):
        return (
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