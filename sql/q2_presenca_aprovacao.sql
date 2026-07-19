-- Q2 - Presenca x aprovacao, visao por faixa de presenca.
-- Complementa o teste estatistico formal (feito em Python) com uma leitura intuitiva:
-- taxa de aprovacao dentro de cada faixa de presenca efetiva.
WITH faixas AS (
    SELECT aluno_id,
           aprovado,
           CASE
               WHEN taxa_presenca < 75 THEN '1) <75%'
               WHEN taxa_presenca < 85 THEN '2) 75-85%'
               WHEN taxa_presenca < 90 THEN '3) 85-90%'
               ELSE '4) >90%'
           END AS faixa_presenca
    FROM base_analitica_aluno
    WHERE taxa_presenca IS NOT NULL
)
SELECT faixa_presenca,
       COUNT(*)                               AS n_alunos,
       SUM(aprovado)                          AS aprovados,
       ROUND(100.0 * SUM(aprovado) / COUNT(*), 1) AS taxa_aprovacao_pct
FROM faixas
GROUP BY faixa_presenca
ORDER BY faixa_presenca;
