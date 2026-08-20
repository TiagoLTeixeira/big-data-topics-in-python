# Participação feminina em TI

Análise da participação feminina em cursos de Tecnologia da Informação, a partir
dos microdados do **ENADE 2021** (INEP) e dos formandos da **Estácio** (2023–2025).
O pipeline gera os dados tratados e os gráficos com um único comando.

## Estrutura de pastas

```
.
├── data/
│   ├── raw/                  # dados brutos
│   │   ├── inep/             # microdados + dicionário oficiais do INEP
│   │   └── estacio/          # planilha de formandos da Estácio
│   └── processed/            # dados tratados gerados pelo pipeline — não versionados
│       ├── enade-2021/       # mulheres em TI no ENADE 2021 (.csv/.xlsx)
│       └── estacio/          # mulheres formandas na Estácio (.csv/.xlsx)
├── notebooks/                # tratamento dos dados, passo a passo (exploração)
├── scripts/                  # pipeline: gera os dados tratados + os gráficos
├── charts/                   # imagens finais (.png) — não versionadas
├── Dockerfile                # imagem enxuta do pipeline
├── docker-compose.yml        # sobe o pipeline com um comando
├── requirements.txt          # dependências (uso local / notebooks)
└── requirements-docker.txt   # dependências enxutas da imagem
```

## Tecnologias e bibliotecas

- **Python 3.12**
- **pandas** — leitura e tratamento dos dados
- **matplotlib** — geração dos gráficos
- **openpyxl** — leitura/escrita de arquivos `.xlsx`
- **JupyterLab** + **ipykernel** — execução dos notebooks (uso local)
- **Docker** + **Docker Compose** — execução reproduzível do pipeline

## Como rodar com Docker

O pipeline é uma tarefa de uma rodada só: o container sobe, gera os **dados tratados**
em `data/processed/` e as **imagens** em `charts/`, e encerra sozinho. Use `run --rm`
para que o container seja **removido automaticamente** ao terminar:

```bash
docker compose run --build --rm analysis
```

- `--build` reconstrói a imagem quando o código ou as dependências mudam.
- `--rm` apaga o container assim que o script termina — não deixa container parado
  acumulando (e evita o conflito de nome em execuções seguintes).

> Os arquivos gerados aparecem direto nas pastas `data/processed/` e `charts/` da sua
> máquina (montadas como volume).

## Como rodar localmente (sem Docker)

```bash
pip install -r requirements.txt
python "scripts/it_female_participation_analysis.py"   # gera dados + gráficos
jupyter lab                                            # abre os notebooks
```

## Fonte dos dados

- **ENADE 2021** — microdados oficiais do INEP:
  https://download.inep.gov.br/microdados/microdados_enade_2021.zip
- **Estácio** — planilha de formandos dos cursos de TI (2023–2025), obtida via
  requerimento interno junto à instituição, de uso restrito a este trabalho acadêmico.
