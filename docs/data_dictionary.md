# Dicionário de dados

Colunas de cada tabela **após o tratamento**, com tipo-alvo e observações. As tabelas de fato e
dimensão são carregadas no banco relacional (`db/schema.sql`); as bases analíticas são derivadas
delas.

Convenção de tipos: `id` identificador, `texto`, `cat` categórica canônica, `int`/`float` numérico,
`data`/`datahora` temporal (ISO), `bool` booleano.

## Dimensões

### estudantes (812) - um aluno
| Coluna | Tipo | Observações |
|---|---|---|
| aluno_id | id (PK) | formato `A#####` |
| nome_aluno | texto | PII fictícia |
| cpf_ficticio | texto | normalizado para só dígitos |
| email_aluno / telefone | texto | PII fictícia |
| data_nascimento | data | 2003–2008 (fora do período do resto da base) |
| cidade | cat | 11 cidades canônicas |
| escola_origem | cat | Pública / Privada / Federal / Não informado |
| data_cadastro | data | |
| canal_captacao | cat | Instagram / Google / WhatsApp / Indicação / Feira escolar |

### professores (35) - um professor
| Coluna | Tipo | Observações |
|---|---|---|
| professor_id | id (PK) | formato `P###` |
| nome_professor | texto | |
| email_professor | texto | |
| materia_principal | cat | uma das 5 colunas de matéria |
| materias_ensina | texto | lista separada por `; ` |
| data_contratacao | data | anterior ao período do desafio |
| status_professor | cat | Ativo / Inativo |
| unidade_base | cat | Aldeota / Centro / Online / Sul |
| carga_horaria_semanal | int | |
| observacoes | texto | |

### ofertas_curso (220) - turma × matéria × ano
| Coluna | Tipo | Observações |
|---|---|---|
| oferta_id | id (PK) | formato `O########` |
| ano | int | |
| turma / turno / unidade / modalidade | cat | turno, unidade e modalidade canônicos |
| materia | cat | uma das 5 colunas de matéria |
| professor_id | id (FK → professores) | |
| professor_nome_informado | texto | nome redigitado; não usar como chave |
| carga_horaria_total | int | |
| preco_lista | float | |
| data_inicio / data_fim | data | |

### simulados (165) - um simulado
| Coluna | Tipo | Observações |
|---|---|---|
| simulado_id | id (PK) | formato `S########` |
| ano | int | |
| data_simulado | data | |
| materia | cat | uma das 5 colunas de matéria |
| professor_id | id (FK → professores) | |
| dificuldade | cat | Fácil / Média / Difícil |
| tipo_simulado | cat | ENEM / Por matéria / Redação / Revisão / Vestibular estadual |
| total_questoes / tempo_limite_min | int | |
| tema | texto | |

## Fatos

### aulas (2.418) - uma aula realizada
| Coluna | Tipo | Observações |
|---|---|---|
| aula_id | id (PK) | formato `L#######` |
| oferta_id | id (FK → ofertas_curso) | |
| ano | int | |
| data_aula | data | |
| materia | cat | uma das 5 colunas de matéria |
| professor_id | id (FK → professores) | |
| turma / tema_aula | texto | |
| duracao_min | int | 50–120 |
| modalidade_aula | cat | Presencial / Online / Híbrido / Não informado |

### matriculas (9.412 após dedup) - um aluno numa oferta
| Coluna | Tipo | Observações |
|---|---|---|
| matricula_id | id (PK) | formato `M#######` |
| aluno_id | id (FK → estudantes) | |
| oferta_id | id (FK → ofertas_curso) | |
| ano | int | ano da matrícula |
| materia_declarada | cat | a coluna de matéria mais suja na origem (28 grafias) |
| data_matricula | data | |
| bolsa_percentual | float | 0–50; vazio ≠ 0 |
| status_matricula | cat | Concluída / Ativa / Cancelada / Trancada / Não informado |
| nota_diagnostico | float | escala 0–100 (nota de entrada) |
| origem_captacao | cat | mesmo domínio de canal_captacao |

### presencas_aulas (74.877 após dedup) - presença de um aluno numa aula
| Coluna | Tipo | Observações |
|---|---|---|
| presenca_id | id (PK) | formato `PA#########` |
| aula_id | id (FK → aulas) | traz matéria/professor via join |
| aluno_id | id (FK → estudantes) | |
| status_presenca | cat | Presente / Ausente / Atrasado / Justificado / Não informado |
| atraso_min | float | 0–30; vazio ≈ não atrasou |
| justificativa | texto | vazio = sem justificativa (esperado) |
| presente_efetivo | bool (derivado) | status ∈ {Presente, Atrasado} |

### resultados_simulados (21.430 após dedup) - resultado de um aluno num simulado
| Coluna | Tipo | Observações |
|---|---|---|
| resultado_id | id (PK) | formato `R########` |
| simulado_id | id (FK → simulados) | traz a matéria via join |
| aluno_id | id (FK → estudantes) | |
| ano | int | |
| materia | cat (derivado) | matéria do simulado, para a escala e a Q3 |
| status_realizacao | cat | Finalizado / Ausente / Incompleto / Não informado |
| nota | float | escala depende da matéria (Redação 0–1000; demais 0–100) |
| nota_valida | float (derivado) | nota dentro da faixa da própria matéria; fora → ausente |
| nota_pct | float (derivado) | nota_valida ÷ escala_max × 100 (comparável entre matérias) |
| acertos | int | |
| tempo_finalizacao_min | float | |
| inicio_simulado | datahora | origem com ≥6 formatos, normalizada |
| dispositivo | cat | Celular / Desktop / Papel / Tablet / Não informado |
| tentativas | int | |
| unidade_aplicacao | cat | Aldeota / Centro / Online / Sul / Não informado |

### aprovacoes_vestibular (339 após dedup) - uma aprovação
| Coluna | Tipo | Observações |
|---|---|---|
| aprovacao_id | id (PK) | formato `V######` |
| ano_vestibular | int | dimensão-chave da Q1 |
| aluno_id | id (FK → estudantes) | 306 alunos distintos |
| universidade | cat | 10 universidades canônicas |
| curso_aprovado | texto | |
| modalidade_vaga | cat | Ampla concorrência / Cota escola pública / PCD / PPI / Não informado |
| chamada | texto | usado para detectar duplicidade de cadastro |
| bolsa_aprovacao | cat | Sim / Não / Parcial / Não informado |
| data_resultado | data | |
| nota_final_vestibular | float | escala ENEM ~475–948 (não confundir com nota de simulado) |
| campus | texto | |

## Bases analíticas (derivadas)

### base_analitica_aluno (812) - uma linha por aluno
| Coluna | Tipo | Observações |
|---|---|---|
| aluno_id | id | |
| cidade / escola_origem / canal_captacao | cat | perfil |
| n_matriculas | int | nº de matrículas do aluno |
| taxa_presenca | float | % de presença efetiva |
| nota_pct_media | float | média do nota_pct de simulados |
| nota_diagnostico_media | float | média da nota diagnóstica |
| aprovado | bool | 1 se o aluno aparece em aprovações |

### base_analitica_materia (11) - uma linha por matéria
| Coluna | Tipo | Observações |
|---|---|---|
| materia | cat | |
| nota_pct_media | float | nota média normalizada |
| n_resultados | int | nº de resultados de simulado |
| presenca_media | float | presença média nas aulas da matéria |
| taxa_conclusao | float | % de matrículas concluídas |
| taxa_aprovacao | float | % de alunos da matéria aprovados |
| n_alunos | int | nº de alunos distintos na matéria |
