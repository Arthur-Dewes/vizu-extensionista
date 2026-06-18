import pandas as pd
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output

YEARS       = [2021, 2022, 2023, 2024, 2025]
YEAR_COLORS = ["#4E9AF1", "#F4A261", "#2A9D8F", "#E76F51", "#8338EC"]
YEAR_COLOR  = dict(zip(YEARS, YEAR_COLORS))

BG          = "#0F1117"
CARD_BG     = "#1A1D27"
BORDER      = "#2A2D3E"
TEXT        = "#E8EAF6"
MUTED       = "#7B7F9E"
ACCENT      = "#4E9AF1"

MONTHS = ["JAN","FEV","MAR","ABR","MAI","JUN","JUL","AGO","SET","OUT","NOV","DEZ"]

FONT = dict(family="'IBM Plex Mono', 'Courier New', monospace", color=TEXT)

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=FONT,
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        font=dict(color=MUTED, size=11),
        orientation="h",
        yanchor="bottom", y=1.02,
        xanchor="left",   x=0,
    ),
    xaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER, tickfont=dict(color=MUTED)),
    yaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER, tickfont=dict(color=MUTED)),
)


def load_data(path: str = "IPP_LEMs.csv") -> pd.DataFrame:
    return pd.read_csv(path)


def atendimentos_mensais(df: pd.DataFrame, anos: list[int]) -> go.Figure:
    """Barras empilhadas: atendimentos totais por mês x ano."""
    cats = [
        "ATENDIMENTOS INDVIDUAL",
        "ATEDIMENTO FAMILIAR",
        "INTERFACE COM REDE SOCIOASSISTENCIAL",
        "INTERFACE COM JUDICIARIO",
        "INTERFACE COM SAUDE",
        "INTERFACE COM EDUCACAO",
        "SAUDE MENTAL",
        "SAUDE CLINICA",
        "INTERNACOES",
    ]
    sub = df[df["categorias"].isin(cats) & df["ANO"].isin(anos)]

    fig = go.Figure()
    for ano in sorted(anos):
        row = sub[sub["ANO"] == ano][MONTHS].sum()
        fig.add_trace(go.Bar(
            name=str(ano),
            x=MONTHS,
            y=row.values,
            marker_color=YEAR_COLOR[ano],
            marker_line_width=0,
            hovertemplate=f"<b>{ano}</b><br>%{{x}}: %{{y}}<extra></extra>",
        ))

    fig.update_layout(
        **PLOT_LAYOUT,
        barmode="stack",
        title=dict(text="Atendimentos mensais por ano", font=dict(color=TEXT, size=14)),
    )
    return fig


def demanda_educacional(df: pd.DataFrame, anos: list[int]) -> go.Figure:
    """Áreas empilhadas: demanda educacional (matriculados + aguardando)."""
    modalidades = {
        "Ensino Infantil": ("MATRICULADOS (ENSINO INFANTIL)", "AGUARDANDO VAGA (ENSINO INFANTIL)"),
        "Ensino Regular":  ("MATRICULADOS (ENSINO REGULAR)",  "AGUARDANDO VAGA (ENSINO REGULAR)"),
        "EJA":             ("MATRICULADOS (ENSINO EJA)",       "AGUARDANDO VAGA (ENSINO EJA)"),
        "SCFV":            ("MATRICULADOS (SCFV)",             "AGUARDANDO VAGA (SCFV)"),
    }
    MODAL_COLORS = ["#4E9AF1", "#2A9D8F", "#F4A261", "#8338EC"]

    sub = df[df["ANO"].isin(anos)]
    anos_ord = sorted(anos)

    fig = go.Figure()
    for (mod, (mat, agu)), color in zip(modalidades.items(), MODAL_COLORS):
        totais = []
        for ano in anos_ord:
            bloco = sub[sub["ANO"] == ano]
            val_mat = bloco.loc[bloco["categorias"] == mat, "TOTAL"].sum()
            val_agu = bloco.loc[bloco["categorias"] == agu, "TOTAL"].sum()
            totais.append(val_mat + val_agu)

        fig.add_trace(go.Scatter(
            name=mod,
            x=anos_ord,
            y=totais,
            stackgroup="one",
            mode="lines",
            line=dict(color=color, width=1.5),
            fillcolor=color.replace(")", ",0.45)").replace("rgb(", "rgba("),
            hovertemplate=f"<b>{mod}</b><br>%{{x}}: %{{y}}<extra></extra>",
        ))

    fig.update_layout(
        **{k: v for k, v in PLOT_LAYOUT.items() if k != "xaxis"},
        title=dict(text="Demanda educacional por modalidade (matriculados + fila)", font=dict(color=TEXT, size=14)),
        xaxis=dict(**PLOT_LAYOUT["xaxis"], tickmode="array", tickvals=anos_ord),
    )
    return fig


def individuais_vs_familiares(df: pd.DataFrame, anos: list[int]) -> go.Figure:
    """Linhas: atendimentos individuais x familiares mês a mês."""
    series = {
        "Individual": ("ATENDIMENTOS INDVIDUAL", ACCENT),
        "Familiar":   ("ATEDIMENTO FAMILIAR",    "#F4A261"),
    }

    sub = df[df["ANO"].isin(anos)]
    anos_ord = sorted(anos)

    fig = go.Figure()
    for label, (cat, color) in series.items():
        xs, ys = [], []
        for ano in anos_ord:
            bloco = sub[(sub["ANO"] == ano) & (sub["categorias"] == cat)]
            for mes in MONTHS:
                xs.append(f"{mes}/{ano}")
                ys.append(int(bloco[mes].sum()) if not bloco.empty else 0)

        fig.add_trace(go.Scatter(
            name=label,
            x=xs,
            y=ys,
            mode="lines+markers",
            line=dict(color=color, width=2),
            marker=dict(size=4, color=color),
            hovertemplate=f"<b>{label}</b><br>%{{x}}: %{{y}}<extra></extra>",
        ))

    fig.update_layout(
        **{k: v for k, v in PLOT_LAYOUT.items() if k != "xaxis"},
        title=dict(text="Atendimentos individuais vs. familiares", font=dict(color=TEXT, size=14)),
        xaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER, tickangle=-45, tickfont=dict(color=MUTED, size=9)),
    )
    return fig


def card(title: str, graph_id: str) -> html.Div:
    return html.Div([
        html.H3(title, style={
            "margin": "0 0 12px 0",
            "fontSize": "12px",
            "letterSpacing": "0.12em",
            "textTransform": "uppercase",
            "color": MUTED,
        }),
        dcc.Graph(id=graph_id, config={"displayModeBar": False},
                  style={"height": "340px"}),
    ], style={
        "background": CARD_BG,
        "border": f"1px solid {BORDER}",
        "borderRadius": "8px",
        "padding": "20px",
        "marginBottom": "20px",
    })


def build_app(csv_path: str = "IPP_LEMs.csv") -> dash.Dash:
    df = load_data(csv_path)

    app = dash.Dash(__name__, title="Fundação Pão dos Pobres — LEMs")

    app.layout = html.Div([
        # header
        html.Div([
            html.Div([
                html.Span("FPP", style={
                    "fontFamily": "'IBM Plex Mono', monospace",
                    "fontSize": "22px",
                    "fontWeight": "700",
                    "color": ACCENT,
                    "marginRight": "12px",
                }),
                html.Span("Fundação Pão dos Pobres · Análise de Dados LEMs", style={
                    "color": MUTED,
                    "fontSize": "13px",
                }),
            ], style={"display": "flex", "alignItems": "center"}),

            # year filter
            html.Div([
                html.Label("Filtrar anos:", style={"color": MUTED, "fontSize": "11px", "marginRight": "10px"}),
                dcc.Checklist(
                    id="year-filter",
                    options=[{"label": str(y), "value": y} for y in YEARS],
                    value=YEARS,
                    inline=True,
                    style={"color": TEXT, "fontSize": "12px", "gap": "12px"},
                    inputStyle={"marginRight": "4px", "accentColor": ACCENT},
                ),
            ], style={"display": "flex", "alignItems": "center"}),
        ], style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "padding": "16px 24px",
            "borderBottom": f"1px solid {BORDER}",
            "marginBottom": "24px",
        }),

        # charts
        html.Div([
            card("Atendimentos mensais por ano",                "chart-atendimentos"),
            card("Demanda educacional por modalidade",          "chart-educacao"),
            card("Atendimentos individuais vs. familiares",     "chart-individual-familiar"),
        ], style={"padding": "0 24px 24px"}),

    ], style={
        "background": BG,
        "minHeight": "100vh",
        "color": TEXT,
        "fontFamily": "'IBM Plex Mono', 'Courier New', monospace",
    })

    @app.callback(
        Output("chart-atendimentos",      "figure"),
        Output("chart-educacao",          "figure"),
        Output("chart-individual-familiar","figure"),
        Input("year-filter", "value"),
    )
    def update_charts(anos):
        anos = anos or YEARS
        return (
            atendimentos_mensais(df, anos),
            demanda_educacional(df, anos),
            individuais_vs_familiares(df, anos),
        )

    return app


if __name__ == "__main__":
    import sys
    csv = sys.argv[1] if len(sys.argv) > 1 else "IPP_LEMs.csv"
    build_app(csv).run(debug=True)