# AprovaEdu Analytics

Solução analítica para uma rede de cursinhos pré-vestibular (2021–2025): lê os dados brutos das 9
tabelas, trata e organiza num banco relacional, e responde às perguntas da coordenação pedagógica
sobre desempenho dos alunos, efetividade dos cursos e fatores associados à aprovação. Entrega as
conclusões num relatório, num dashboard interativo e num score de propensão.

## Contexto e objetivo

A rede acumulou, ao longo de cinco anos, dados de fontes internas diferentes (daí a heterogeneidade
de formato e qualidade). A coordenação quer decisão apoiada em dado. O projeto responde a quatro
perguntas obrigatórias:

1. **Q1** — Evolução da taxa de aprovação ao longo dos anos.
2. **Q2** — Relação entre presença nas aulas e aprovação.
3. **Q3** — Cursos/matérias com melhor desempenho.
4. **Q4** — Recomendações práticas para a coordenação.

## Principais achados

- **Taxa de aprovação estável em ~33%** (30–36%) ao longo dos cinco anos — o volume cresce, a
  proporção de aprovados se mantém.
- **Sem associação mensurável entre presença e aprovação** (teste estatístico formal; presença
  comprimida demais para discriminar os grupos).
- **Matérias com desempenho parecido entre si**; o maior achado de negócio é a **qualidade do dado
  na origem** (matéria escrita de até 28 formas, escala de nota inconsistente, duplicidade de
  cadastro).

## Instruções para rodar o projeto

**Pré-requisitos:** Python 3.11+ com `pip` e `git`. Docker é opcional (para o ambiente isolado).

### 1. Clonar e preparar o ambiente

```bash
git clone https://github.com/mateusnriy/aprovaedu-analytics.git
cd aprovaedu-analytics

# ambiente virtual (recomendado, para isolar as dependências)
python -m venv .venv
source .venv/bin/activate            # Windows (PowerShell): .venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### 2. Rodar o pipeline

```bash
python run_pipeline.py
```

Executa, de ponta a ponta e de forma **idempotente**, na ordem:

1. **ETL** - leitura, canonicalização, escala de nota por matéria, parser de datas e dedup;
2. **carga** no banco relacional `db/aprovaedu.db` + export dos dados tratados em `data/processed/*.csv`;
3. **bases analíticas** (`base_analitica_aluno`, `base_analitica_materia`);
4. **análises Q1–Q4** → figuras em `reports/figures/` + `reports/metricas.json`;
5. **score de propensão** → segmentos + figura.

Rodar duas vezes produz exatamente o mesmo resultado. Os 9 CSVs brutos já acompanham o repositório
(`data/raw/`), então não há passo manual — roda a partir de um clone limpo.

### 3. Rodar os testes

```bash
pytest        # esperado: 11 passed
```

### 4. Abrir o dashboard

```bash
streamlit run dashboard/app.py
```

Abre em `http://localhost:8501`: KPIs, respostas Q1–Q3, segmentação do score e filtros interativos
(canal de captação, escola de origem, cidade).

### (Opcional) Rodar com Docker

Ambiente isolado, sem instalar nada localmente além do Docker:

```bash
docker build -t aprovaedu .                                  # construir a imagem
docker run --rm aprovaedu                                     # rodar o pipeline
docker run --rm -p 8501:8501 aprovaedu \                      # servir o dashboard
  streamlit run dashboard/app.py --server.address=0.0.0.0
```

## Ferramentas utilizadas

| Camada | Ferramenta | Papel no projeto |
|---|---|---|
| Linguagem | **Python 3.11+** | base de todo o pipeline |
| Manipulação de dados | **pandas**, **numpy** | leitura, limpeza, agregações |
| Banco de dados | **SQLite** (`sqlite3`) | camada relacional oficial, com schema PK/FK |
| Estatística | **scipy** | testes formais da Q2 (Mann-Whitney, point-biserial) |
| Modelo preditivo | **scikit-learn** | regressão logística interpretável (score de propensão) |
| Visualização | **matplotlib**, **seaborn** | figuras do relatório |
| Dashboard | **Streamlit** | painel interativo com filtros |
| Testes | **pytest** | 11 testes de qualidade de dados |
| Reprodutibilidade | **Docker**, `requirements.txt` | ambiente limpo, um comando |

As versões estão fixadas em [`requirements.txt`](requirements.txt) (pisos mínimos com `>=`).

**Princípio: simplicidade defensável.** Nada de Spark/Airflow/data warehouse — seria
over-engineering para o volume (~110 mil linhas, cabe em memória com folga) e desviaria o foco do que
é avaliado (qualidade do tratamento, clareza das decisões, capacidade de inferência). A mesma stack
escala para PostgreSQL trocando só a camada de banco, se um dia o volume exigir.

## Estrutura do projeto

```
aprovaedu-analytics/
├── run_pipeline.py            # orquestra o pipeline de ponta a ponta (ponto de entrada)
├── requirements.txt           # dependências (versões mínimas)
├── Dockerfile / .dockerignore # ambiente reprodutível
│
├── data/
│   ├── raw/                   # 9 CSVs originais, imutáveis (fonte da verdade)
│   └── processed/             # dados tratados + bases analíticas + score (versionado)
│
├── db/
│   ├── schema.sql             # DDL do banco relacional (dimensões, fatos, PK/FK, índices)
│   └── aprovaedu.db           # banco SQLite gerado pelo pipeline (não versionado)
│
├── sql/                       # consultas analíticas versionadas
│   ├── q1_taxa_aprovacao.sql       # Q1 — taxa de aprovação por ano
│   ├── q2_presenca_aprovacao.sql   # Q2 — presença × aprovação por faixa
│   ├── q3_desempenho_materia.sql   # Q3 — indicadores por matéria
│   └── extra_*.sql                 # análises adicionais (evolução, unidade, universidade)
│
├── src/
│   ├── config.py             # caminhos, escala por matéria, mapas canônicos (fonte única)
│   ├── etl.py                # leitura → canonicalização → escala → datas → dedup
│   ├── db.py                 # cria o schema, carrega e valida a integridade referencial
│   ├── base_analitica.py     # monta as bases analíticas (aluno e matéria)
│   ├── analysis.py           # Q1–Q4 → figuras + metricas.json
│   └── score.py              # score de propensão à aprovação (scikit-learn)
│
├── tests/
│   └── test_qualidade.py     # 11 testes travando as decisões críticas
│
├── notebooks/
│   └── profiling.ipynb       # diagnóstico exploratório da base (executado)
│
├── dashboard/
│   └── app.py                # dashboard interativo (Streamlit)
│
├── reports/
│   ├── RELATORIO_FINAL.md    # relatório completo (+ .pdf)
│   ├── DECISOES.md           # decisões de tratamento (achado→decisão→justificativa→nº)
│   ├── metricas.json         # fonte única de todos os números do relatório
│   └── figures/              # PNGs do relatório e do dashboard
│
└── docs/
    ├── data_dictionary.md    # dicionário de dados (colunas, tipos, domínios)
    ├── log_tratamento.md     # log gerado automaticamente pelo ETL
    └── USO_DE_IA.md          # documento de uso de IA
```

**Fluxo:** `data/raw` → `src/etl.py` → `db/aprovaedu.db` (+ `data/processed`) → `src/analysis.py` e
`src/score.py` → `reports/` e `dashboard/`. Tudo disparado por `run_pipeline.py`.

## Decisões técnicas e analíticas relevantes

Detalhadas em [`reports/DECISOES.md`](reports/DECISOES.md) (achado → decisão → justificativa → nº de
registros afetados). As mais relevantes:

**Técnicas**

- **Banco relacional SQLite** como camada oficial (PK/FK, portável, versionável, dockerizável);
  migra para PostgreSQL sem reescrever se o volume crescer.
- **Leitura BOM-safe** (`utf-8-sig`, `dtype=str`, `keep_default_na=False`), com tipagem controlada.
- **Canonicalização com mapa explícito e falha alta:** valor fora do mapa interrompe o pipeline em
  vez de criar categoria fantasma (remover acento/caixa não basta — `"Mat."` ≠ `"Matemática"`).
- **Parser de datas em cascata** (barra/BR antes de traço/US) e **pipeline idempotente**, com todo
  número saindo de `reports/metricas.json` (nada digitado à mão).

**Analíticas**

- **Escala de nota por matéria** (Redação 0–1000; demais 0–100). Fora da faixa vira ausente, nunca
  truncado. Uma faixa global descartaria toda a Redação e mudaria a resposta da Q3.
- **Taxa de aprovação por pessoas** (aprovados distintos ÷ matriculados distintos), nunca por eventos.
- **Presença efetiva** = Presente + Atrasado, com **teste estatístico formal** na Q2, reportando o
  resultado como sai (inclusive nulo).
- **Índice composto por z-score** na Q3, com **Redação à parte** (prova dissertativa, não comparável).
- **Deduplicação** de negócio + remoção de 15 duplicidades de cadastro em aprovações (campo `chamada`).

## Onde encontrar

| O quê | Arquivo |
|---|---|
| Relatório final | [`reports/RELATORIO_FINAL.md`](reports/RELATORIO_FINAL.md) · [PDF](reports/RELATORIO_FINAL.pdf) |
| Decisões de tratamento | [`reports/DECISOES.md`](reports/DECISOES.md) |
| Dicionário de dados | [`docs/data_dictionary.md`](docs/data_dictionary.md) |
| Uso de IA | [`docs/USO_DE_IA.md`](docs/USO_DE_IA.md) |
| Números que sustentam o relatório | [`reports/metricas.json`](reports/metricas.json) |
