-- Extra: evolucao da nota media de simulado (normalizada) ao longo dos anos.
SELECT ano,
       ROUND(AVG(nota_pct), 1) AS nota_pct_media,
       COUNT(nota_valida)      AS n_resultados
FROM resultados_simulados
WHERE nota_valida IS NOT NULL
GROUP BY ano
ORDER BY ano;
