# Dashboard LEM

Pipeline de padronização de dados + dashboard interativo para os indicadores
mensais do LEM (planilhas anuais em Excel → CSV consolidado → visualizações
Plotly/Dash).

```
data/LEM 2021.xlsx     ─┐
data/LEM 2022 (1).xlsx ─┤
data/LEM 2023.xlsx     ─┼──▶  main.py  ──▶  IPP_LEMs.csv  ──▶  dashboard_lem.py  ──▶  http://127.0.0.1:8050
data/LEM 2024 (1).xlsx ─┤                └─▶ relatorio.html (ydata-profiling)
data/LEM 2025 1.xlsx   ─┘
```

## Sumário

- [Dashboard LEM](#dashboard-lem)
  - [Sumário](#sumário)
  - [Requisitos](#requisitos)
  - [Formato esperado das planilhas de entrada](#formato-esperado-das-planilhas-de-entrada)
  - [1. Rodar o pré-processamento](#1-rodar-o-pré-processamento)
  - [2. Rodar o dashboard](#2-rodar-o-dashboard)
  - [Arquivos gerados](#arquivos-gerados)
  - [Dicionário de dados](#dicionário-de-dados)
  - [Limitações conhecidas](#limitações-conhecidas)
  - [Solução de problemas](#solução-de-problemas)

## Requisitos

- Python **3.12**
- Dependências em `requirements.txt` (principais: `pandas`, `openpyxl`,
  `ydata-profiling`, `dash`, `plotly`)

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Formato esperado das planilhas de entrada

`main.py` assume que cada arquivo `.xlsx` segue **sempre o mesmo layout**:

- As **2 primeiras linhas** são cabeçalho/título e são ignoradas (`skiprows=2`).
- A **linha seguinte** contém os rótulos dos meses (JAN..DEZ) e é usada como
  cabeçalho das colunas.
- São lidas exatamente **41 linhas** de dados e **13 colunas** (1 coluna de
  categoria + 12 meses).
- Linhas que são apenas títulos de seção (`DESDOBRAMENTOS TÉCNICOS`,
  `PROFISSIONALIZAÇÃO`, `SAÚDE`, `EDUCAÇÃO`, `Ensino infantil`,
  `Ensino regular`, `Ensino EJA`, `SCFV`) são descartadas — servem só de
  agrupamento visual na planilha original.
- As linhas de posição **24 a 31** (0-indexadas, após a remoção acima)
  correspondem aos pares *Matriculados / Aguardando vaga* das 4 modalidades
  de ensino (Infantil, Regular, EJA, SCFV) e recebem um sufixo no nome da
  categoria para diferenciá-las (ex.: `MATRICULADOS (ENSINO INFANTIL)`).

⚠️ Se a estrutura de alguma planilha anual mudar (linhas adicionadas/removidas,
seções reordenadas), esse mapeamento posicional quebra silenciosamente — veja
[Limitações conhecidas](#limitações-conhecidas).

Todos os nomes de categoria são normalizados (maiúsculas, sem acentos) para
garantir que a mesma categoria seja comparável entre anos, mesmo que a
grafia varie de uma planilha para outra.

## 1. Rodar o pré-processamento

```bash
# uso: main.py <ano_inicial> <arquivo1> [arquivo2 ...]
python3 main.py 2021 \
  "data/LEM 2021.xlsx" \
  "data/LEM 2022 (1).xlsx" \
  "data/LEM 2023.xlsx" \
  "data/LEM 2024 (1).xlsx" \
  "data/LEM 2025 1.xlsx"
```

**Importante:**
- Os arquivos devem ser passados em **ordem cronológica**, começando pelo
  `ano_inicial` informado (ex.: acima, o 1º arquivo é 2021, o 2º é 2022 etc.
  — o ano é inferido pela posição do argumento, não pelo nome do arquivo).
- Todas as planilhas precisam resultar no **mesmo número de linhas e
  colunas** após a leitura; caso contrário o script para com um erro
  indicando em qual ano a divergência foi encontrada.

O script:
1. Lê e padroniza cada planilha (`read()`).
2. Valida que todos os anos têm o mesmo formato.
3. Concatena tudo em um único DataFrame, adicionando a coluna `ANO`.
4. Gera um relatório exploratório (`relatorio.html`) com `ydata-profiling`.
5. Preenche valores ausentes com `0` e exporta `IPP_LEMs.csv`.

## 2. Rodar o dashboard

```bash
python3 dashboard_lem.py IPP_LEMs.csv
# abre em http://127.0.0.1:8050
```

O dashboard traz um filtro de anos (checklist) e recalcula em tempo real:

| Gráfico | Conteúdo |
|---|---|
| Cartões de KPI | Atendimentos, Ingressos, Desligamentos, Matrículas (soma do período) |
| Saúde por mês | Barras empilhadas (ano) e agrupadas (Internações / Saúde Clínica / Saúde Mental) |
| Atendimentos | Linha do tempo de atendimentos individuais vs. familiares |
| Mapa de calor | Intensidade de atendimentos por mês x ano |
| Ranking | Top 10 categorias por volume total |
| Educação | Matriculados + aguardando vaga por modalidade e ano |
| Radar de interfaces | Perfil de contato com redes (socioassistencial, judiciário, saúde, educação) |
| Dinâmica populacional | Ingressos, desligamentos, evasões e transferências por ano |
| Profissionalização | Encaminhados vs. inseridos (cursos e mercado de trabalho) |

## Arquivos gerados

| Arquivo | Descrição |
|---|---|
| `IPP_LEMs.csv` | Dados consolidados de todos os anos, prontos para o dashboard |
| `relatorio.html` | Relatório exploratório automático (ydata-profiling): distribuições, valores ausentes, tipos de dados |

## Dicionário de dados

Colunas de `IPP_LEMs.csv`:

- `categorias`: nome normalizado da categoria (maiúsculo, sem acento)
- `JAN` … `DEZ`: valor mensal da categoria
- `TOTAL`: soma dos 12 meses
- `ANO`: ano de referência da linha

As categorias são agrupadas em macroáreas para leitura/agregação (ver
`get_macro_area()` em `dashboard_lem.py`): **Saúde**, **Atendimentos e
Relatórios**, **Educação**, **Profissionalização**, **Dinâmica Populacional**,
**Interfaces de Rede** e **Outros / Gestão**.

## Limitações conhecidas

- **Layout fixo por posição**: `nrows=41`, `usecols=range(13)` e os índices
  `24`–`31` para os pares de educação assumem que todas as planilhas anuais
  têm exatamente a mesma disposição de linhas. Qualquer alteração no template
  do Excel (linha extra, seção removida) exige revisar `read()`.
- **Ano inferido pela ordem dos argumentos**, não pelo conteúdo/nome do
  arquivo — passar os arquivos fora de ordem gera dados com o ano errado
  silenciosamente.
- **Categorias de saúde/atendimento assumidas como fixas** nas funções de
  gráfico (`fig_saude_mensal`, `fig_linhas` etc. em `dashboard_lem.py`); se o
  texto de uma categoria mudar no Excel de origem, o gráfico correspondente
  passa a somar zero para ela.
- Nomes de categoria com erro de digitação na planilha original são
  preservados propositalmente (ex.: `ATENDIMENTOS INDVIDUAL`,
  `ATEDIMENTO FAMILIAR`) — os gráficos referenciam essas strings exatas.

## Solução de problemas

- **`AssertionError: Erro na tabela do ano ...`**: uma das planilhas tem
  número de linhas/colunas diferente do primeiro ano. Confira se o arquivo
  não tem linhas extras, mescladas ou fora do padrão de 41 linhas / 13
  colunas.
- **Gráfico aparece vazio para uma categoria**: verifique se o nome da
  categoria na planilha bate exatamente (após normalização) com a string
  esperada no código (`dashboard_lem.py`, listas `HEALTH_CATEGORIES`,
  `mods`, `interfaces`, `cats`).
- **Dashboard não abre**: confirme que o `IPP_LEMs.csv` foi gerado por
  `main.py` antes de rodar `dashboard_lem.py`, e que a porta `8050` está
  livre.