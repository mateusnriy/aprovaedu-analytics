# AprovaEdu Analytics

Solução analítica para uma rede de cursinhos pré-vestibular que, entre 2021 e 2025, acumulou
dados de alunos, professores, matérias, cursos, simulados, presença em aulas e aprovações no
vestibular vindos de fontes internas diferentes. O objetivo é apoiar a coordenação pedagógica
com indicadores e recomendações baseadas em dado sobre desempenho dos alunos, efetividade dos
cursos e fatores associados à aprovação.

## Stack

- **Python 3.11+**, pandas e numpy para tratamento de dados
- **SQLite** como banco de dados relacional (schema com chaves primárias e estrangeiras)
- **matplotlib** e **seaborn** para as visualizações do relatório
- **pytest** para os testes automatizados de qualidade de dados
- **Streamlit** para o dashboard interativo

## Estrutura do repositório

```
data/raw/         dados originais
data/processed/   dados tratados, prontos para análise
db/               schema do banco relacional e o banco SQLite
sql/              consultas analíticas
src/              código do pipeline (configuração, ETL, banco, análises)
tests/            testes automatizados de qualidade de dados
notebooks/        profiling exploratório da base
dashboard/        dashboard interativo em Streamlit
reports/          relatório final, decisões de tratamento e figuras
docs/             dicionário de dados e demais documentação
```
