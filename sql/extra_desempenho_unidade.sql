-- Extra: nota media de simulado (normalizada) por unidade de aplicacao.
SELECT unidade_aplicacao,
       ROUND(AVG(nota_pct), 1) AS nota_pct_media,
       COUNT(nota_valida)      AS n_resultados
FROM resultados_simulados
WHERE nota_valida IS NOT NULL
  AND unidade_aplicacao <> 'Não informado'
GROUP BY unidade_aplicacao
ORDER BY nota_pct_media DESC;
