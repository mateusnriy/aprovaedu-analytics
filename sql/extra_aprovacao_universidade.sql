-- Extra: aprovacoes por universidade (volume e alunos distintos).
SELECT universidade,
       COUNT(*)                 AS aprovacoes,
       COUNT(DISTINCT aluno_id) AS alunos_distintos
FROM aprovacoes_vestibular
GROUP BY universidade
ORDER BY aprovacoes DESC;
