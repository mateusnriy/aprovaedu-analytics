-- Q3 - Desempenho por materia.
-- Devolve os 4 indicadores por materia; o indice composto (media dos z-scores) e calculado
-- em Python a partir daqui. n_resultados e n_alunos acompanham para dar contexto de amostra.
SELECT materia,
       nota_pct_media,
       presenca_media,
       taxa_conclusao,
       taxa_aprovacao,
       n_resultados,
       n_alunos
FROM base_analitica_materia
ORDER BY nota_pct_media DESC;
