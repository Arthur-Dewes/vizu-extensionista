import sys
import unicodedata
import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go
from ydata_profiling import ProfileReport

def normalize_text(index: pd.Index) -> pd.Index:
    def _normalize(s: str) -> str:
        nfd = unicodedata.normalize('NFD', s)
        return ''.join(c for c in nfd if unicodedata.category(c) != 'Mn').upper()
    return index.map(_normalize)

def read(path: str) -> pd.DataFrame:
    data: pd.DataFrame = pd.read_excel(path, header=None, skiprows=2, usecols=range(13), nrows=41) # type: ignore
    data.set_index(0, inplace=True)
    data.index = data.index.astype(str).str.strip()
    data.columns = data.iloc[0, :].to_list()
    data = data.drop(
        labels=["DESDOBRAMENTOS TÉCNICOS", "PROFISSIONALIZAÇÃO", "SAÚDE", "EDUCAÇÃO", "Ensino infantil", "Ensino regular", "Ensino EJA", "SCFV"], 
        errors='ignore'
    )
    for idx, ed in enumerate([" (Ensino infantil)", " (Ensino regular)", " (Ensino EJA)", " (SCFV)"]):
        indexes = list(data.index)
        pos_matriculados = 24 + (idx * 2)
        pos_aguardando = 25 + (idx * 2)
        indexes[pos_matriculados] = f"{indexes[pos_matriculados]}{ed}"
        indexes[pos_aguardando] = f"{indexes[pos_aguardando]}{ed}"
        data.index = indexes    
    data.index = normalize_text(data.index)
    data.index.name = "index"
    # data.fillna(0, inplace=True)
    data['TOTAL'] = data.apply(pd.to_numeric, errors='coerce').sum(axis=1)
    return data

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Uso: script.py <ano_inicial> <tabela1> <tabela2>")
        sys.exit(1)
    
    starting_year: int = int(sys.argv[1])
    paths: list[str] = sys.argv[2:]
    dataframes: dict[int, pd.DataFrame] = {starting_year + i: read(path) for i, path in enumerate(paths)}
    
    ref = dataframes[starting_year].shape
    for year, df in dataframes.items():
        assert df.shape == ref, f"Erro na tabela do ano {year}: esperado {ref[0]} linhas e {ref[1]} colunas, mas obteve {df.shape[0]} linhas e {df.shape[1]} colunas"
    del ref

    for year, df in dataframes.items():
        df["ANO"] = year
    df_final = pd.concat([dataframes[i] for i in range(starting_year, starting_year+len(dataframes))])

    profile = ProfileReport(dataframes[2021], title="Relatório LEM") # type: ignore
    profile.to_file("relatorio.html") # type: ignore

    
    # df_ed = pd.DataFrame([
    #     {
    #         'ANO': year,
    #         'ENSINO INFANTIL': df.loc['MATRICULADOS (ENSINO INFANTIL)', 'TOTAL'] + df.loc['AGUARDANDO VAGA (ENSINO INFANTIL)', 'TOTAL'],
    #         'ENSINO REGULAR':  df.loc['MATRICULADOS (ENSINO REGULAR)',  'TOTAL'] + df.loc['AGUARDANDO VAGA (ENSINO REGULAR)',  'TOTAL'],
    #         'ENSINO EJA':      df.loc['MATRICULADOS (ENSINO EJA)',      'TOTAL'] + df.loc['AGUARDANDO VAGA (ENSINO EJA)',      'TOTAL'],
    #         'SCFV':            df.loc['MATRICULADOS (SCFV)',            'TOTAL'] + df.loc['AGUARDANDO VAGA (SCFV)',            'TOTAL'],
    #     }
    #     for year, df in dataframes.items()
    # ])
    # print(df_ed)

    # fig = go.Figure()
    # eds = [ed for ed in df_ed if ed != "ANO"]
    # for ed in eds:
    #     fig.add_trace(go.Violin(x=df_ed['ANO'][df_ed['ANO'] == ed],
    #                             y=df_ed['ANO'][df_ed['ANO'] == ed],
    #                             name=ed,
    #                             box_visible=True,
    #                             meanline_visible=True))

