"""Bases analiticas derivadas: 1 linha por aluno e 1 linha por materia.

Quase toda analise sai da base de aluno (grao central). A base de materia (11 linhas) alimenta
o ranking de desempenho da Q3.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src import config, db


def _base_aluno(dfs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    est = dfs["estudantes"]
    matr = dfs["matriculas"]
    pres = dfs["presencas_aulas"]
    res = dfs["resultados_simulados"]
    apr = dfs["aprovacoes_vestibular"]

    # taxa de presenca efetiva por aluno (sobre todas as suas presencas)
    taxa_presenca = pres.groupby("aluno_id")["presente_efetivo"].mean() * 100
    # nota_pct media de simulado por aluno
    nota_pct = res.groupby("aluno_id")["nota_pct"].mean()
    # nota diagnostica media (das matriculas)
    nota_diag = matr.groupby("aluno_id")["nota_diagnostico"].mean()
    # nº de matriculas
    n_matriculas = matr.groupby("aluno_id").size()
    # alvo: aprovado (aparece em aprovacoes)
    aprovados = set(apr["aluno_id"].unique())

    base = est[["aluno_id", "cidade", "escola_origem", "canal_captacao"]].copy()
    base["n_matriculas"] = base["aluno_id"].map(n_matriculas).fillna(0).astype(int)
    base["taxa_presenca"] = base["aluno_id"].map(taxa_presenca)
    base["nota_pct_media"] = base["aluno_id"].map(nota_pct)
    base["nota_diagnostico_media"] = base["aluno_id"].map(nota_diag)
    base["aprovado"] = base["aluno_id"].isin(aprovados).astype(int)
    return base


def _base_materia(dfs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    matr = dfs["matriculas"]
    pres = dfs["presencas_aulas"]
    aul = dfs["aulas"]
    res = dfs["resultados_simulados"]
    apr = dfs["aprovacoes_vestibular"]
    aprovados = set(apr["aluno_id"].unique())

    # nota_pct media e n por materia (dos resultados de simulado)
    nota_pct = res.groupby("materia")["nota_pct"].mean()
    n_result = res.groupby("materia")["nota_valida"].count()

    # presenca media por materia (presencas via aula -> materia da aula)
    pres_mat = pres.merge(aul[["aula_id", "materia"]], on="aula_id", how="left")
    presenca = pres_mat.groupby("materia")["presente_efetivo"].mean() * 100

    # taxa de conclusao por materia (matricula concluida / total, por materia_declarada)
    conclusao = (matr.assign(concl=(matr["status_matricula"] == "Concluída").astype(int))
                     .groupby("materia_declarada")["concl"].mean() * 100)

    # taxa de aprovacao dos alunos associados a materia (via matricula declarada)
    def taxa_aprov(sub):
        alunos = sub["aluno_id"].unique()
        return np.mean([a in aprovados for a in alunos]) * 100 if len(alunos) else np.nan
    aprov = matr.groupby("materia_declarada").apply(taxa_aprov, include_groups=False)
    n_alunos = matr.groupby("materia_declarada")["aluno_id"].nunique()

    materias = sorted(config.MATERIAS_CANONICAS)
    base = pd.DataFrame({"materia": materias})
    base["nota_pct_media"] = base["materia"].map(nota_pct)
    base["n_resultados"] = base["materia"].map(n_result).fillna(0).astype(int)
    base["presenca_media"] = base["materia"].map(presenca)
    base["taxa_conclusao"] = base["materia"].map(conclusao)
    base["taxa_aprovacao"] = base["materia"].map(aprov)
    base["n_alunos"] = base["materia"].map(n_alunos).fillna(0).astype(int)
    return base


def montar_bases(dfs: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    return _base_aluno(dfs), _base_materia(dfs)


def persistir(df_aluno: pd.DataFrame, df_materia: pd.DataFrame, caminho_db=None):
    """grava as bases como tabelas no banco e como CSV em data/processed."""
    config.DIR_PROCESSED.mkdir(parents=True, exist_ok=True)
    df_aluno.to_csv(config.DIR_PROCESSED / "base_analitica_aluno.csv", index=False, encoding="utf-8")
    df_materia.to_csv(config.DIR_PROCESSED / "base_analitica_materia.csv", index=False, encoding="utf-8")

    conn = db.conectar(caminho_db)
    try:
        df_aluno.to_sql("base_analitica_aluno", conn, if_exists="replace", index=False)
        df_materia.to_sql("base_analitica_materia", conn, if_exists="replace", index=False)
        conn.commit()
    finally:
        conn.close()
