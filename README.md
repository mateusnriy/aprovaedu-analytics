# AprovaEdu Analytics

Solução analítica para uma rede de cursinhos pré-vestibular que, entre 2021 e 2025, acumulou dados
de alunos, professores, matérias, cursos, simulados, presença em aulas e aprovações no vestibular
vindos de fontes internas diferentes. O objetivo é apoiar a coordenação pedagógica com indicadores e
recomendações baseadas em dado sobre desempenho dos alunos, efetividade dos cursos e fatores
associados à aprovação.

O relatório completo, com as respostas das perguntas obrigatórias e as recomendações, está em
[`reports/RELATORIO_FINAL.md`](reports/RELATORIO_FINAL.md).

## Principais achados

- Taxa de aprovação **estável em ~33%** (30–36%) ao longo dos cinco anos.
- **Sem associação** mensurável entre presença nas aulas e aprovação (teste estatístico formal).
- Matérias com desempenho **parecido entre si**; diferenças modestas no índice composto.
- O maior achado de negócio é a **qualidade do dado na origem** (matéria escrita de 28 formas, escala
  de nota inconsistente, duplicidade de cadastro).

## Stack

- **Python 3.11+**, pandas e numpy para tratamento de dados
- **SQLite** como banco de dados relacional (schema com chaves primárias e estrangeiras)
- **scipy** para os testes estatísticos; **matplotlib**/**seaborn** para as figuras
- **pytest** para os testes automatizados de qualidade de dados

## Como rodar

```bash
# 1. instalar dependências
pip install -r requirements.txt

# 2. rodar o pipeline de ponta a ponta (idempotente)
python run_pipeline.py

# 3. rodar os testes de qualidade
pytest
```

O `run_pipeline.py` faz, de uma vez: tratamento das 9 tabelas → carga no banco relacional → bases
analíticas → figuras e `reports/metricas.json`. Rodar duas vezes produz exatamente o mesmo
resultado.

## Estrutura do repositório

```
data/raw/         9 CSVs originais (imutáveis)
data/processed/   dados tratados, saída do pipeline (inclui as bases analíticas)
db/               schema.sql (modelo relacional) e o banco SQLite gerado
sql/              consultas analíticas versionadas (Q1–Q3)
src/              config.py, etl.py, db.py, base_analitica.py, analysis.py
tests/            testes de qualidade de dados
notebooks/        profiling exploratório da base
reports/          RELATORIO_FINAL.md, DECISOES.md, metricas.json, figures/
docs/             data_dictionary.md, log_tratamento.md, USO_DE_IA.md
```

## Banco de dados

A camada oficial dos dados tratados é um banco relacional **SQLite** (`db/aprovaedu.db`), com dimensões
(`estudantes`, `professores`, `ofertas_curso`, `simulados`) e fatos (`matriculas`, `aulas`,
`presencas_aulas`, `resultados_simulados`, `aprovacoes_vestibular`), chaves primárias e estrangeiras
declaradas em [`db/schema.sql`](db/schema.sql), e as duas bases analíticas materializadas. O banco é
**gerado pelo pipeline** e não é versionado; `python run_pipeline.py` o recria do zero. Os dados
tratados também são exportados em `data/processed/*.csv` (cópia legível e versionada).

SQLite foi escolhido por ser relacional de verdade, sem servidor, portável (um arquivo), reprodutível
e dockerizável. Para o volume desta base (~110 mil linhas) é a escolha adequada; o mesmo schema e as
mesmas consultas migram para PostgreSQL com esforço mínimo se o volume crescer.

## Decisões técnicas e analíticas

As decisões de tratamento estão detalhadas em [`reports/DECISOES.md`](reports/DECISOES.md). As de
maior efeito no resultado:

- **Escala de nota por matéria** (Redação 0–1000; demais 0–100). Notas fora da faixa da própria
  matéria viram ausentes, nunca truncadas. Uma faixa 0–100 global descartaria toda a Redação.
- **Canonicalização com falha alta:** toda categórica passa por um mapa canônico explícito; valor
  desconhecido interrompe o pipeline em vez de virar categoria fantasma.
- **Taxa de aprovação por pessoas** (aprovados distintos ÷ matriculados distintos), nunca por eventos.
- **Presença efetiva** = Presente + Atrasado.
- **Deduplicação** de negócio nas tabelas de fato e remoção de 15 duplicidades de cadastro em
  aprovações.

## Qualidade e reprodutibilidade

- Os testes (`tests/test_qualidade.py`) travam as decisões críticas contra regressões — em especial
  a escala por matéria, as taxas em [0,100], a deduplicação e a integridade referencial do banco.
- Todo número do relatório sai de `reports/metricas.json`, gerado pelo código — nenhum valor é
  digitado à mão.

## Uso de IA

O uso de ferramentas de IA no desenvolvimento está documentado, com honestidade, em
[`docs/USO_DE_IA.md`](docs/USO_DE_IA.md). Todas as decisões técnicas e analíticas foram tomadas pelo
autor; a IA foi apoio ao desenvolvimento.

## Licença

MIT — ver [`LICENSE`](LICENSE).
