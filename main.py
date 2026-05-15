import pandas as pd
import plotly.express as px

def read(path: str) -> pd.DataFrame:
    data: pd.DataFrame = pd.read_excel(path, header=None, skiprows=2, usecols=range(13), nrows=41)    
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
    data.index.name = "index"
    data.fillna(0, inplace=True)
    return data

if __name__ == '__main__':
    data = {
        2021: read("data/LEM 2021.xlsx"),
        2022: read("data/LEM 2022 (1).xlsx"),
        2023: read("data/LEM 2023.xlsx"),
        2024: read("data/LEM 2024 (1).xlsx"),
        2025: read("data/LEM 2025 1.xlsx")
    }
    
    sum_per_column = {}
    for df in data.values():
        print(df.shape)

    print(data[2021])
