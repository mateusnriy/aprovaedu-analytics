-- Q1 - Evolucao da taxa de aprovacao por ano.
-- Mostra as tres metricas que nao podem ser confundidas e a taxa correta = (c) / (a):
--   (a) matriculados distintos no ano (status ativo/concluida/trancada)
--   (b) eventos de aprovacao no ano (linhas de aprovacoes_vestibular, ja sem as duplicidades de cadastro)
--   (c) alunos distintos aprovados no ano
WITH matric AS (
    SELECT ano AS ano, COUNT(DISTINCT aluno_id) AS matriculados_dist
    FROM matriculas
    WHERE status_matricula IN ('Concluída', 'Ativa', 'Trancada')
    GROUP BY ano
),
aprov AS (
    SELECT ano_vestibular AS ano,
           COUNT(*)                 AS eventos_aprovacao,
           COUNT(DISTINCT aluno_id) AS aprovados_dist
    FROM aprovacoes_vestibular
    GROUP BY ano_vestibular
)
SELECT m.ano,
       m.matriculados_dist,
       a.eventos_aprovacao,
       a.aprovados_dist,
       ROUND(100.0 * a.aprovados_dist / m.matriculados_dist, 1) AS taxa_aprovacao_pct
FROM matric m
LEFT JOIN aprov a ON m.ano = a.ano
ORDER BY m.ano;
