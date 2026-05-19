## Como executar

```bash
main.py <ano_inicial> <arquivo1> [arquivo2 ...]
```

### Exemplo com uv

```bash
uv run main.py 2021 \
  "data/LEM 2021.xlsx" \
  "data/LEM 2022 (1).xlsx" \
  "data/LEM 2023.xlsx" \
  "data/LEM 2024 (1).xlsx" \
  "data/LEM 2025 1.xlsx"
```

> Os arquivos devem ser passados em **ordem cronológica**, a partir do `ano_inicial`.