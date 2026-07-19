"""Fixtures dos testes de qualidade: roda o ETL uma vez e disponibiliza as tabelas tratadas,
as bases analiticas e as tabelas brutas (para o teste de nao-truncamento)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # deixa 'src' importavel

from src import etl, base_analitica, config


@pytest.fixture(scope="session")
def dfs():
    """9 tabelas ja tratadas (saida do ETL)."""
    return etl.executar_etl()


@pytest.fixture(scope="session")
def bases(dfs):
    """(base_analitica_aluno, base_analitica_materia)."""
    return base_analitica.montar_bases(dfs)


@pytest.fixture(scope="session")
def resultados_brutos():
    """resultados de simulado crus, com a escala esperada por materia, para o teste de
    nao-truncamento (compara nº de validos antes x depois)."""
    res = etl._ler_csv("resultados_simulados")
    sim = etl._ler_csv("simulados")
    res = res.merge(sim[["simulado_id", "materia"]], on="simulado_id", how="left")
    res["materia_norm"] = res["materia"].map(etl._normkey)
    res["nota_num"] = pd.to_numeric(res["nota"].replace("", np.nan), errors="coerce")
    res["escala_max"] = np.where(res["materia_norm"] == "redacao", 1000.0, 100.0)
    return res
