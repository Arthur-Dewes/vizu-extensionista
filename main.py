import sys
import unicodedata
import pandas as pd
from data_profiling import ProfileReport

def normalize_text(series: pd.Series) -> pd.Series:
    def _normalize(s: str) -> str:
        nfd = unicodedata.normalize('NFD', s)
        return ''.join(c for c in nfd if unicodedata.category(c) != 'Mn').upper()
    return series.map(_normalize)

def read(path: str) -> pd.DataFrame:
    data: pd.DataFrame = pd.read_excel(path, header=None, skiprows=2, usecols=range(13), nrows=41) # type: ignore
    
    data.rename(columns={0: "categorias"}, inplace=True)
    data["categorias"] = data["categorias"].astype(str).str.strip()

    header = data.iloc[0, 1:].to_list()
    data.columns = ["categorias"] + header

    data = data.drop(
        labels=data[data["categorias"].isin([
            "DESDOBRAMENTOS TÉCNICOS", "PROFISSIONALIZAÇÃO", "SAÚDE", "EDUCAÇÃO",
            "Ensino infantil", "Ensino regular", "Ensino EJA", "SCFV"
        ])].index,
        errors='ignore'
    )

    for idx, ed in enumerate([" (Ensino infantil)", " (Ensino regular)", " (Ensino EJA)", " (SCFV)"]):
            pos_matriculados = 24 + (idx * 2)
            pos_aguardando   = 25 + (idx * 2)
            idx_matriculados = data.index[pos_matriculados]
            idx_aguardando   = data.index[pos_aguardando]
            data.at[idx_matriculados, "categorias"] = str(data.at[idx_matriculados, "categorias"]) + ed
            data.at[idx_aguardando,   "categorias"] = str(data.at[idx_aguardando,   "categorias"]) + ed

    data["categorias"] = normalize_text(data["categorias"])

    numeric_cols = [c for c in data.columns if c != "categorias"]
    data[numeric_cols] = data[numeric_cols].apply(pd.to_numeric, errors='coerce').astype("Int64")
    data['TOTAL'] = data[numeric_cols].sum(axis=1)
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
        df["ANO"] = pd.array([year] * len(df), dtype="Int64")
    df_final = pd.concat([dataframes[i] for i in range(starting_year, starting_year + len(dataframes))])

    profile = ProfileReport(df_final, title="Relatório LEM", correlations={"auto": {"calculate": False}}) # type: ignore
    profile.to_file("relatorio.html") # type: ignore

    df_final.fillna(0, inplace=True)
    df_final.to_csv("IPP_LEMs.csv", index=False)


