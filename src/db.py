"""Banco relacional SQLite: cria o schema, carrega as tabelas tratadas e ajuda a consultar."""
from __future__ import annotations

import sqlite3
import pandas as pd

from src import config
from src.etl import COLUNAS_SAIDA


def conectar(caminho=None) -> sqlite3.Connection:
    conn = sqlite3.connect(caminho or config.CAMINHO_DB)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def construir_banco(dfs: dict[str, pd.DataFrame], caminho=None):
    """recria o banco do zero a partir dos DataFrames tratados e valida as FKs."""
    caminho = caminho or config.CAMINHO_DB
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if caminho.exists():
        caminho.unlink()  # recria do zero -> pipeline idempotente

    schema = config.CAMINHO_SCHEMA.read_text(encoding="utf-8")
    conn = conectar(caminho)
    try:
        conn.executescript(schema)
        # carrega respeitando a ordem (dimensoes antes dos fatos) e so as colunas do schema
        ordem = ["estudantes", "professores", "ofertas_curso", "simulados", "aulas",
                 "matriculas", "presencas_aulas", "resultados_simulados", "aprovacoes_vestibular"]
        for nome in ordem:
            cols = COLUNAS_SAIDA[nome]
            dfs[nome][cols].to_sql(nome, conn, if_exists="append", index=False)

        problemas = conn.execute("PRAGMA foreign_key_check").fetchall()
        if problemas:
            raise RuntimeError(f"integridade referencial violada no banco: {problemas[:5]}")
        conn.commit()
    finally:
        conn.close()


def consultar(sql: str, caminho=None) -> pd.DataFrame:
    """roda um SELECT e devolve DataFrame. Usado pelas analises e pelo dashboard."""
    conn = conectar(caminho)
    try:
        return pd.read_sql_query(sql, conn)
    finally:
        conn.close()


def consultar_arquivo(caminho_sql, caminho_db=None) -> pd.DataFrame:
    """roda uma query versionada de sql/ contra o banco."""
    from pathlib import Path
    sql = Path(caminho_sql).read_text(encoding="utf-8")
    return consultar(sql, caminho_db)
