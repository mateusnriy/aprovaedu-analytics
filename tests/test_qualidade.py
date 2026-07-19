"""Testes de qualidade de dados.

Cada teste trava um erro concreto e ja cometido nesta base numa avaliacao anterior. A lista e
curta de proposito: o que importa e proteger cada decisao fragil, nao inflar a contagem.
"""
import sqlite3
import tempfile
from pathlib import Path

import pandas as pd

from src import config, db


MATERIAS_ESPERADAS = config.MATERIAS_CANONICAS


def test_dominio_materia_canonico(dfs):
    """Trava grafia nao canonica sobrevivendo em alguma das 5 colunas de materia
    (ex.: 'Fisica'/'Física' ou 'Mat.'/'Matemática' como categorias distintas)."""
    for tabela, coluna in config.COLUNAS_MATERIA:
        obtido = set(dfs[tabela][coluna].unique()) - {config.ROTULO_AUSENTE}
        extra = obtido - MATERIAS_ESPERADAS
        assert not extra, f"{tabela}.{coluna} tem grafia nao canonica: {extra}"


def test_escala_por_materia_plausivel(dfs):
    """O teste mais importante: trava a escala de nota tratada como global em vez de por
    materia. Se a mediana de uma materia fugir da escala declarada, e sinal de escala errada."""
    res = dfs["resultados_simulados"]
    medianas = res.groupby("materia")["nota_valida"].median()
    for materia, mediana in medianas.items():
        limite = config.ESCALA_MAX.get(materia, config.ESCALA_PADRAO)
        assert 0.20 * limite <= mediana <= 0.90 * limite, (
            f"{materia}: mediana {mediana:.1f} incompativel com escala 0-{limite:.0f}"
        )


def test_nenhuma_materia_perde_tudo(dfs):
    """Trava a consequencia do bug de escala: uma materia inteira virando NaN em silencio
    porque a faixa errada descartou quase todos os seus registros."""
    res = dfs["resultados_simulados"]
    cobertura = res.groupby("materia")["nota_valida"].apply(lambda s: s.notna().mean())
    perdidas = cobertura[cobertura < 0.50]
    assert perdidas.empty, f"materias com >50% de notas descartadas: {list(perdidas.index)}"


def test_taxa_entre_0_e_100(bases):
    """Trava taxas absurdas (ex.: uma 'taxa' de 555% por dividir eventos por matriculados).
    Toda coluna de taxa da base de materia tem que ficar em [0, 100]."""
    _, materia = bases
    for col in [c for c in materia.columns if c.startswith("taxa_")]:
        fora = materia[(materia[col] < 0) | (materia[col] > 100)]
        assert fora.empty, f"{col} fora de [0,100]:\n{fora[['materia', col]]}"


def test_integridade_referencial(dfs):
    """Confirma que o ETL nao introduziu FK orfa (a base bruta ja era 100% integra)."""
    assert dfs["matriculas"]["oferta_id"].isin(dfs["ofertas_curso"]["oferta_id"]).all()
    assert dfs["presencas_aulas"]["aula_id"].isin(dfs["aulas"]["aula_id"]).all()
    assert dfs["resultados_simulados"]["simulado_id"].isin(dfs["simulados"]["simulado_id"]).all()
    for tabela in ["matriculas", "presencas_aulas", "resultados_simulados", "aprovacoes_vestibular"]:
        assert dfs[tabela]["aluno_id"].isin(dfs["estudantes"]["aluno_id"]).all(), tabela


def test_pk_unica(dfs):
    """A deduplicacao nao pode deixar (nem introduzir) PK duplicada."""
    chaves = [
        ("estudantes", "aluno_id"), ("professores", "professor_id"),
        ("ofertas_curso", "oferta_id"), ("simulados", "simulado_id"),
        ("aulas", "aula_id"), ("matriculas", "matricula_id"),
        ("presencas_aulas", "presenca_id"), ("resultados_simulados", "resultado_id"),
        ("aprovacoes_vestibular", "aprovacao_id"),
    ]
    for tabela, pk in chaves:
        assert not dfs[tabela][pk].duplicated().any(), f"PK duplicada em {tabela}"


def test_dedup_negocio_aplicada(dfs):
    """Duplicidade de negocio nao deve sobreviver: (aluno,oferta), (aluno,aula), (aluno,simulado)."""
    assert not dfs["matriculas"].duplicated(subset=["aluno_id", "oferta_id"]).any()
    assert not dfs["presencas_aulas"].duplicated(subset=["aluno_id", "aula_id"]).any()
    assert not dfs["resultados_simulados"].duplicated(subset=["aluno_id", "simulado_id"]).any()


def test_aprovacoes_duplicidade_cadastro_removida(dfs):
    """Nenhuma linha 'Cadastro duplicado?' deve sobreviver, e o total cai de 354 para ~339."""
    ap = dfs["aprovacoes_vestibular"]
    assert (ap["chamada"].astype(str).str.strip() != "Cadastro duplicado?").all()
    assert len(ap) <= 340, f"esperado <=340 aprovacoes, obtido {len(ap)}"


def test_nao_truncar_outliers(dfs, resultados_brutos):
    """Trava o erro de 'capar' outliers (1005 -> 100), que infla a media. O nº de notas
    validas depois nao pode ser maior que o nº de notas ja dentro da faixa antes."""
    validos_antes = resultados_brutos["nota_num"].between(
        0, resultados_brutos["escala_max"]).sum()
    validos_depois = dfs["resultados_simulados"]["nota_valida"].notna().sum()
    assert validos_depois <= validos_antes + 5  # tolerancia p/ diferencas de parsing


def test_base_analitica_aluno_grao_correto(dfs, bases):
    """base_analitica_aluno tem exatamente 1 linha por aluno (grao central das analises)."""
    df_aluno, _ = bases
    assert df_aluno["aluno_id"].is_unique
    assert len(df_aluno) == len(dfs["estudantes"])


def test_integridade_banco(dfs):
    """Constroi o banco relacional num arquivo temporario e confirma que o SQLite nao acusa
    nenhuma violacao de FK (PRAGMA foreign_key_check)."""
    with tempfile.TemporaryDirectory() as tmp:
        caminho = Path(tmp) / "teste.db"
        db.construir_banco(dfs, caminho=caminho)  # ja levanta se houver FK orfa
        conn = sqlite3.connect(caminho)
        try:
            problemas = conn.execute("PRAGMA foreign_key_check").fetchall()
        finally:
            conn.close()
        assert not problemas, f"FKs violadas no banco: {problemas}"
