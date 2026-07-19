# Decisões de tratamento de dados

Registro das decisões de limpeza e modelagem, cada uma no formato **achado → decisão →
justificativa → registros afetados**. Os números vêm do profiling da base bruta
(`notebooks/00_profiling.ipynb`) e da execução do pipeline de ETL.

A base bruta são 9 CSVs de fontes internas diferentes, com heterogeneidade de formato e
qualidade. Integridade estrutural está intacta (PKs 100% únicas, nenhuma FK sozinha).

---

## 1. Leitura dos arquivos com BOM UTF-8

**Achado.** Os 9 CSVs têm BOM UTF-8. Lidos de forma ingênua, a primeira coluna de cada arquivo
vem com um caractere invisível no cabeçalho e valores vazios são convertidos em `NaN`.

**Decisão.** Ler tudo com `encoding="utf-8-sig"`, `dtype=str` e `keep_default_na=False`. A
tipagem numérica/temporal é feita depois, de forma controlada, coluna a coluna.

**Justificativa.** Ler como texto e converter explicitamente evita conversões silenciosas do
pandas e mantém a distinção entre "vazio" e "ausente" sob controle do pipeline.

**Registros afetados.** As 9 tabelas, na leitura.

---

## 2. Escala de nota de simulado é por matéria

**Achado.** A mediana da nota de simulado por matéria mostra **Redação em torno de 720** e as
demais dez matérias em torno de **60**. Redação está na escala ENEM (0–1000); as outras, em
0–100. Aplicar uma faixa válida "0–100" global descartaria **toda** a Redação como fora de
escala.

**Decisão.** Faixa válida **por matéria**: `Redação` usa 0–1000, as demais 0–100. Notas fora da
faixa da própria matéria viram ausentes (`NaN`), **nunca truncadas**. Além disso, calculo
`nota_pct = nota_valida / escala_max(materia) * 100` para permitir comparação entre matérias.

**Justificativa.** Truncar (ex.: 1005 → 100) infla a média de forma sistemática, um erro pior
do que descartar o registro. A normalização `nota_pct` permite comparar matérias de escalas
diferentes, mas Redação (prova dissertativa avaliada em banca) não é estritamente comparável às
objetivas mesmo normalizada, isso é sinalizado como ressalva na análise de desempenho.

**Registros afetados.** 365 notas fora da faixa da própria matéria → ausentes. 1.686 notas
vazias por ausência estrutural (aluno não fez a prova) já eram ausentes na origem.

---

## 3. Canonicalização das categóricas com mapa explícito

**Achado.** A informação de matéria aparece em 5 tabelas, sob 3 nomes de coluna
(`materia`, `materia_declarada`, `materia_principal`), cada uma com grafias inconsistentes.
`matriculas.materia_declarada` é a mais suja: 28 grafias brutas. Remover acento e caixa reduz,
mas não resolve, a abreviação `Mat.` continua diferente de `Matemática`. O mesmo padrão afeta
outras categóricas (cidade, universidade, status, escola de origem, canal de captação, etc.).

**Decisão.** Toda coluna categórica passa por um mapa canônico explícito
(chave normalizada → rótulo de exibição), centralizado na configuração do projeto. Um valor
fora de todos os mapas conhecidos faz o pipeline **falhar alto** (erro), em vez de criar uma
categoria fantasma em silêncio. Vazio numa categórica vira `"Não informado"` (exceto ausência
estrutural, como justificativa de presença vazia).

**Justificativa.** Falhar alto num valor desconhecido é o que teria evitado que uma grafia nova
passasse despercebida e distorcesse uma agregação. Centralizar o mapa evita esquecer uma das 5
colunas de matéria (a mais fácil de esquecer é `materia_declarada`, cujo nome não segue o padrão
das outras).

**Registros afetados.** As 5 colunas de matéria (28/19/19/16/15 grafias brutas) mais as demais
categóricas das 9 tabelas.

---

## 4. Deduplicação de cadastro em aprovações

**Achado.** São 354 linhas de aprovação para 306 alunos distintos; 46 alunos têm mais de uma
aprovação. Parte é erro de cadastro: o campo `chamada` traz o literal `"Cadastro duplicado?"` em
15 linhas, e cada uma dessas 15 tem um par idêntico (mesmo aluno, mesmo ano, mesma nota final)
em outra linha.

**Decisão.** Remover apenas as 15 linhas marcadas como `"Cadastro duplicado?"` que têm par
idêntico confirmado. Não remover por múltiplas aprovações de forma cega.

**Justificativa.** Os outros 31 alunos com múltiplas aprovações são casos legítimos (aprovados
em universidades ou anos diferentes) e devem ser mantidos. Remover por "mais de uma
aprovação" apagaria informação verdadeira.

**Registros afetados.** 15 linhas removidas → de 354 para 339 aprovações; 306 alunos distintos
aprovados, dos quais 31 com múltiplas aprovações legítimas.

---

## 5. Deduplicação de negócio nas tabelas de fato

**Achado.** Há duplicatas lógicas: mesma matrícula `(aluno, oferta)`, mesma presença
`(aluno, aula)` e mesmo resultado `(aluno, simulado)` repetidos.

**Decisão.**
- Matrículas: uma linha por `(aluno_id, oferta_id)`, priorizando o status mais avançado
  (Concluída > Ativa > Trancada > Cancelada) e a data mais recente.
- Presenças: uma linha por `(aluno_id, aula_id)`, presença dupla na mesma aula é impossível.
- Resultados: uma linha por `(aluno_id, simulado_id)`, mantendo a melhor nota válida (retentativas).

**Justificativa.** Cada grão descrito corresponde a um evento único de negócio; manter duplicatas
inflaria contagens e médias.

**Registros afetados.** 40 duplicatas em matrículas, 120 em presenças, 80 em resultados.

---

## 6. Presença efetiva

**Achado.** `status_presenca` tem quatro categorias válidas: Presente, Ausente, Atrasado,
Justificado. A taxa de presença por aluno é muito comprimida, mediana ~84%, quase todos entre
81% e 87%, mínimo 70% e máximo 97%.

**Decisão.** Presença efetiva = `Presente` ou `Atrasado`. `Justificado` e `Ausente` não contam
como presença efetiva.

**Justificativa.** O aluno atrasado esteve na aula; o justificado, não. A compressão da variável
é registrada aqui porque condiciona a análise de presença × aprovação: uma diferença de poucos
pontos entre grupos, sem teste formal, não é evidência de associação.

**Registros afetados.** As 74.997 presenças; taxa calculada para 800 alunos com aulas elegíveis.

---

## 7. Definição da taxa de aprovação

**Achado.** A base não traz a taxa pronta e há três contagens facilmente confundíveis por ano:
matriculados distintos, volume de eventos de aprovação, e alunos distintos aprovados.

**Decisão.** Taxa de aprovação = **alunos distintos aprovados ÷ matriculados distintos**, por
ano. No denominador entram matrículas com status Concluída, Ativa ou Trancada (aluno esteve
efetivamente ativo); Cancelada é excluída.

**Justificativa.** Dividir volume de eventos de aprovação por matriculados mistura contagem de
eventos com contagem de pessoas e pode gerar taxas acima de 100%. Usar pessoas no numerador e no
denominador mantém a taxa interpretável e entre 0 e 100.

**Registros afetados.** Matriculados distintos por ano (2021–2025): 138 / 170 / 218 / 263 / 233.
Aprovados distintos por ano: 50 / 53 / 77 / 79 / 80.

---

## 8. Datas em múltiplos formatos

**Achado.** `resultados_simulados.inicio_simulado` mistura vários formatos na mesma coluna (ISO,
BR com barra, US com traço, com e sem hora).

**Decisão.** Parser em cascata, tentando os formatos com barra (padrão BR) antes dos com traço
(padrão US), e validando o ano resultante contra o intervalo do período (2021–2025).
`data_nascimento` e `data_contratacao` ficam fora dessa validação de ano por serem anteriores ao
período.

**Justificativa.** Como os separadores diferem entre BR e US, fixar a ordem de tentativa elimina
a ambiguidade dia↔mês sem precisar adivinhar.

**Registros afetados.** As datas de `resultados_simulados` e demais colunas temporais das tabelas
transacionais.

---

## 9. Valores ausentes: estrutural vs. faltante

**Achado.** Vazios têm significados diferentes: nota vazia porque o aluno faltou ao simulado
(ausência estrutural, correto) é diferente de uma categórica vazia por falha de cadastro (dado
faltante).

**Decisão.** Distinguir os dois casos e nunca imputar em silêncio. Ausência estrutural é mantida
como ausente; categórica faltante vira `"Não informado"`. A política é registrada por coluna.

**Justificativa.** Imputar um valor a uma ausência estrutural inventaria informação; tratar toda
ausência como "Não informado" apagaria a distinção entre "não fez a prova" e "não cadastrado".

**Registros afetados.** Principais colunas com vazios: nota/tempo de simulado (~1.686, ausência
estrutural), dispositivo e unidade de aplicação (~3.600 cada), origem de captação (~1.590),
canal de captação e escola de origem (~90–130).
