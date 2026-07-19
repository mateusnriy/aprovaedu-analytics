# Log de tratamento

Gerado automaticamente pelo `src/etl.py`. Registra o que cada etapa do ETL fez e quantos registros foram afetados, na ordem em que rodou.

## estudantes
- 812 alunos, categoricas canonicalizadas (cidade, escola, canal).
## professores
- 35 professores, materia_principal e status canonicalizados.
## ofertas_curso
- 220 ofertas, materia/turno/unidade/modalidade canonicalizados.
## simulados
- 165 simulados, materia/dificuldade/tipo canonicalizados.
## aulas
- 2418 aulas, materia/modalidade canonicalizados (0 PKs duplicadas removidas).
## matriculas
- materia_declarada (28 grafias) e status canonicalizados.
- dedup (aluno, oferta): 40 linhas removidas, 9412 mantidas.
## presencas_aulas
- status canonicalizado; presente_efetivo derivado (Presente/Atrasado).
- dedup (aluno, aula): 120 removidas, 74877 mantidas.
## resultados_simulados
- escala por materia aplicada (Redacao 0-1000, demais 0-100); 365 notas fora da faixa viraram ausentes (nunca truncadas).
- dedup (aluno, simulado): 80 removidas, 21430 mantidas.
## aprovacoes_vestibular
- universidade e modalidade canonicalizadas.
- 15 duplicidades de cadastro removidas (chamada='Cadastro duplicado?' com par identico confirmado): de 354 para 339 aprovacoes.
