import pandas as pd

df_2021 = pd.read_excel("data/LEM 2021.xlsx", header=None, skiprows=2, usecols=range(14), nrows=42)
df_2021_map = {
    df_2021.iloc[0][0].strip(): int(df_2021.iloc[18][13]),
    df_2021.iloc[18][0].strip(): int(df_2021.iloc[23][13]),
    df_2021.iloc[23][0].strip(): int(df_2021.iloc[27][13]),
    df_2021.iloc[27][0].strip(): int(df_2021.iloc[41][13])
}
df_2021_desd_tec = df_2021.iloc[:18].copy()
df_2021_profissi = df_2021.iloc[18:23].copy()
df_2021_saude = df_2021.iloc[23:27].copy()
df_2021_educacao = df_2021.iloc[27:].copy()


print()
# print(df_2021)
print(df_2021_map)


print(df_2021_educacao)