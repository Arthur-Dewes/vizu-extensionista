import pandas as pd

def read(path: str) -> pd.DataFrame:
    data: pd.DataFrame = pd.read_excel(path, header=None, skiprows=2, usecols=range(13), nrows=41)    
    data.set_index(0, inplace=True)
    data.index = data.index.astype(str).str.strip()
    data.columns = data.iloc[0, :].to_list()
    data = data.drop(
        labels=["DESDOBRAMENTOS TÉCNICOS", "PROFISSIONALIZAÇÃO", "SAÚDE", "EDUCAÇÃO", "Ensino infantil", "Ensino regular", "Ensino EJA", "SCFV"], 
        errors='ignore'
    )
    data.index.name = "index"
    data.fillna(0, inplace=True)
    return data

if __name__ == '__main__':
    df_2021: pd.DataFrame = read("data/LEM 2021.xlsx")
    df_2022: pd.DataFrame = read("data/LEM 2022 (1).xlsx")
    df_2023: pd.DataFrame = read("data/LEM 2023.xlsx")
    df_2024: pd.DataFrame = read("data/LEM 2024 (1).xlsx")
    df_2025: pd.DataFrame = read("data/LEM 2025 1.xlsx")

    for df in [df_2021, df_2022, df_2023, df_2024, df_2025]:
        print(df.shape)
    
    