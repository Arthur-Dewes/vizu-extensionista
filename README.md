### Rodar preprocessamento

```bash
# como executar
# main.py <ano_inicial> <arquivo1> [arquivo2 ...]
python3 main.py 2021 \
  "data/LEM 2021.xlsx" \
  "data/LEM 2022 (1).xlsx" \
  "data/LEM 2023.xlsx" \
  "data/LEM 2024 (1).xlsx" \
  "data/LEM 2025 1.xlsx"
```

> Os arquivos devem ser passados em **ordem cronológica**, a partir do `ano_inicial`.

### Rodar vizualizações

```bash
python3 viz.py IPP_LEMs.csv # abre em http://127.0.0.1:8050
```

### Requirements

python 3.12
requirements.txt
