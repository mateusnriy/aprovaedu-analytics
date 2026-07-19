"""Analises Q1-Q4: le do banco relacional, calcula os indicadores, gera as figuras e
consolida tudo em metricas.json (fonte unica dos numeros do relatorio).

Regra: nenhum numero do relatorio e digitado a mao - todo valor sai daqui.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # sem display, so salva PNG
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from src import config, db, etl

DIR_FIG = config.RAIZ / "reports" / "figures"
DIR_SQL = config.RAIZ / "sql"
CAMINHO_METRICAS = config.RAIZ / "reports" / "metricas.json"

# paleta categorica colorblind-safe (Okabe-Ito) - ordem fixa, nunca ciclada
COR = {"azul": "#0072B2", "laranja": "#E69F00", "verde": "#009E73", "vermelho": "#D55E00",
       "roxo": "#CC79A7", "ceu": "#56B4E9", "amarelo": "#F0E442", "cinza": "#7F7F7F"}
INDICADORES = ["nota_pct_media", "presenca_media", "taxa_conclusao", "taxa_aprovacao"]
ROTULO_IND = {"nota_pct_media": "Nota (%)", "presenca_media": "Presença",
              "taxa_conclusao": "Conclusão", "taxa_aprovacao": "Aprovação"}


def _estilo():
    plt.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": 130, "font.size": 10,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": "#E6E6E6", "grid.linewidth": 0.8,
        "axes.axisbelow": True, "axes.edgecolor": "#B0B0B0",
        "figure.facecolor": "white", "axes.facecolor": "white",
    })


def _salvar(fig, nome):
    DIR_FIG.mkdir(parents=True, exist_ok=True)
    caminho = DIR_FIG / nome
    fig.tight_layout()
    fig.savefig(caminho, bbox_inches="tight")
    plt.close(fig)
    return caminho


# ------------------------------------------------------------------ Q1

def q1():
    """taxa de aprovacao por ano = aprovados distintos / matriculados distintos."""
    df = db.consultar_arquivo(DIR_SQL / "q1_taxa_aprovacao.sql")

    # contagem bruta de eventos por ano (antes da dedup de cadastro) - mostra o impacto da limpeza
    raw = etl._ler_csv("aprovacoes_vestibular")
    brutos = (raw.groupby("ano_vestibular").size().rename("eventos_brutos")
                 .reset_index().rename(columns={"ano_vestibular": "ano"}))
    brutos["ano"] = brutos["ano"].astype(int)
    df = df.merge(brutos, on="ano", how="left")

    x = np.arange(len(df))  # mesma coordenada nos dois paineis (rotulos = anos), senao o sharex quebra
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 7), sharex=True,
                                   gridspec_kw={"height_ratios": [1, 1.1]})
    # painel 1: a taxa (uma serie, sem legenda - o titulo ja nomeia)
    ax1.plot(x, df["taxa_aprovacao_pct"], color=COR["azul"], lw=2, marker="o", ms=8)
    for xi, taxa in zip(x, df["taxa_aprovacao_pct"]):
        ax1.annotate(f"{taxa:.1f}%", (xi, taxa), textcoords="offset points", xytext=(0, 9),
                     ha="center", fontsize=9, color="#333333")
    ax1.set_ylim(0, max(df["taxa_aprovacao_pct"]) * 1.35)
    ax1.set_ylabel("Taxa de aprovação (%)")
    ax1.set_title("Q1 — Taxa de aprovação por ano (aprovados distintos ÷ matriculados distintos)",
                  fontsize=11, loc="left", weight="bold")

    # painel 2: matriculados (a) e aprovados distintos (c) - mesma unidade (pessoas), um eixo.
    # (b) e (c) coincidem por ano apos a dedup, entao mostro so (a) e (c) para nao repetir barra.
    w = 0.38
    ax2.bar(x - w / 2, df["matriculados_dist"], w, label="(a) matriculados distintos",
            color=COR["ceu"])
    ax2.bar(x + w / 2, df["aprovados_dist"], w, label="(c) aprovados distintos", color=COR["verde"])
    ax2.set_xticks(x)
    ax2.set_xticklabels(df["ano"])
    ax2.set_ylabel("Contagem de alunos")
    ax2.set_xlabel("Ano")
    ax2.legend(frameon=False, fontsize=9, loc="upper left")
    ax2.set_title("Matriculados vs. aprovados distintos por ano", fontsize=10, loc="left",
                  color="#333333")
    caminho = _salvar(fig, "q1_taxa_aprovacao_ano.png")

    return {
        "por_ano": df.to_dict("records"),
        "taxa_media_pct": round(float(df["taxa_aprovacao_pct"].mean()), 1),
        "taxa_min_pct": round(float(df["taxa_aprovacao_pct"].min()), 1),
        "taxa_max_pct": round(float(df["taxa_aprovacao_pct"].max()), 1),
        "aprovacoes_brutas_total": int(df["eventos_brutos"].sum()),
        "aprovacoes_pos_dedup_total": int(df["aprovados_dist"].sum()),
        "figura": caminho.name,
    }


# ------------------------------------------------------------------ Q2

def q2():
    """presenca x aprovacao: teste formal + visao por faixa. Reporta o resultado como sair."""
    aluno = db.consultar("SELECT taxa_presenca, aprovado FROM base_analitica_aluno "
                         "WHERE taxa_presenca IS NOT NULL")
    aprov = aluno.loc[aluno["aprovado"] == 1, "taxa_presenca"]
    nao = aluno.loc[aluno["aprovado"] == 0, "taxa_presenca"]

    # teste de diferenca de distribuicao (nao assume normalidade) + forca da associacao
    u, p_mw = stats.mannwhitneyu(aprov, nao, alternative="two-sided")
    r_pb, p_pb = stats.pointbiserialr(aluno["aprovado"], aluno["taxa_presenca"])

    faixas = db.consultar_arquivo(DIR_SQL / "q2_presenca_aprovacao.sql")

    fig, (axb, axf) = plt.subplots(1, 2, figsize=(11, 5), gridspec_kw={"width_ratios": [1, 1.2]})
    # boxplot por grupo
    bp = axb.boxplot([nao, aprov], labels=[f"Não aprovados\n(n={len(nao)})",
                                           f"Aprovados\n(n={len(aprov)})"],
                     patch_artist=True, widths=0.55, medianprops=dict(color="#222222", lw=1.5))
    for patch, cor in zip(bp["boxes"], [COR["cinza"], COR["verde"]]):
        patch.set_facecolor(cor)
        patch.set_alpha(0.75)
    axb.set_ylabel("Taxa de presença efetiva (%)")
    axb.set_title("Distribuição de presença por grupo", fontsize=11, loc="left", weight="bold")

    # barras: taxa de aprovacao por faixa de presenca
    axf.bar(faixas["faixa_presenca"], faixas["taxa_aprovacao_pct"], color=COR["azul"], width=0.6)
    for i, r in faixas.iterrows():
        axf.annotate(f"{r['taxa_aprovacao_pct']:.0f}%\n(n={r['n_alunos']})",
                     (i, r["taxa_aprovacao_pct"]), textcoords="offset points", xytext=(0, 5),
                     ha="center", fontsize=9, color="#333333")
    axf.set_ylim(0, max(faixas["taxa_aprovacao_pct"]) * 1.3)
    axf.set_ylabel("Taxa de aprovação (%)")
    axf.set_title("Taxa de aprovação por faixa de presença", fontsize=11, loc="left", weight="bold")
    axf.tick_params(axis="x", labelsize=9)
    caminho = _salvar(fig, "q2_presenca_aprovacao.png")

    return {
        "n_aprovados": int(len(aprov)), "n_nao_aprovados": int(len(nao)),
        "presenca_media_aprovados": round(float(aprov.mean()), 1),
        "presenca_media_nao_aprovados": round(float(nao.mean()), 1),
        "mannwhitney_u": round(float(u), 1), "mannwhitney_p": round(float(p_mw), 4),
        "pointbiserial_r": round(float(r_pb), 3), "pointbiserial_p": round(float(p_pb), 4),
        "faixas": faixas.to_dict("records"),
        "figura": caminho.name,
    }


# ------------------------------------------------------------------ Q3

def q3():
    """ranking de materias por indice composto (media de 4 z-scores), so nas 10 objetivas.
    Redacao fica a parte: e prova dissertativa em escala 0-1000, cujo nota_pct nao e
    estritamente comparavel - incluida no z-score, distorceria ranking e heatmap."""
    df = db.consultar_arquivo(DIR_SQL / "q3_desempenho_materia.sql")

    obj = df[df["materia"] != "Redação"].copy()
    for ind in INDICADORES:
        mu, sd = obj[ind].mean(), obj[ind].std(ddof=0)
        obj[ind + "_z"] = (obj[ind] - mu) / sd
    obj["indice_composto"] = obj[[i + "_z" for i in INDICADORES]].mean(axis=1)
    obj = obj.sort_values("indice_composto", ascending=False).reset_index(drop=True)

    redacao = df[df["materia"] == "Redação"].iloc[0]

    # --- figura 1: ranking das 10 objetivas; Redacao numa caixa a parte ---
    fig, ax = plt.subplots(figsize=(9, 5.6))
    ax.barh(obj["materia"], obj["indice_composto"], color=COR["azul"])
    ax.invert_yaxis()
    ax.axvline(0, color="#B0B0B0", lw=1)
    for i, r in obj.iterrows():
        off = 4 if r["indice_composto"] >= 0 else -4
        ha = "left" if r["indice_composto"] >= 0 else "right"
        ax.annotate(f"{r['indice_composto']:+.2f}", (r["indice_composto"], i),
                    textcoords="offset points", xytext=(off, 0), va="center", ha=ha,
                    fontsize=9, color="#333333")
    ax.set_xlabel("Índice composto (média de 4 z-scores das 10 matérias objetivas)")
    ax.set_title("Q3 — Desempenho por matéria (índice composto)", fontsize=11, loc="left",
                 weight="bold")
    ax.text(0.98, 0.04,
            f"Redação à parte: nota {redacao['nota_pct_media']:.0f}% (normalizada 0–1000),\n"
            f"prova dissertativa — não comparável às objetivas.",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=8.5, color=COR["vermelho"],
            bbox=dict(boxstyle="round", fc="#FFF3EA", ec=COR["vermelho"], alpha=0.95))
    caminho_rank = _salvar(fig, "q3_ranking.png")

    # --- figura 2: heatmap materia x indicador (z-scores, diverging RdBu), so as objetivas ---
    matz = obj.set_index("materia")[[i + "_z" for i in INDICADORES]]
    matz.columns = [ROTULO_IND[i] for i in INDICADORES]
    lim = float(np.nanmax(np.abs(matz.values)))
    fig, ax = plt.subplots(figsize=(7.5, 6))
    ax.grid(False)  # grid global atrapalha a leitura das celulas do heatmap
    im = ax.imshow(matz.values, cmap="RdBu_r", vmin=-lim, vmax=lim, aspect="auto")
    ax.set_xticks(range(len(matz.columns)))
    ax.set_xticklabels(matz.columns)
    ax.set_yticks(range(len(matz.index)))
    ax.set_yticklabels(matz.index)
    for i in range(matz.shape[0]):
        for j in range(matz.shape[1]):
            v = matz.values[i, j]
            ax.text(j, i, f"{v:+.1f}", ha="center", va="center", fontsize=8.5,
                    color="white" if abs(v) > lim * 0.55 else "#222222")
    ax.set_title("Q3 — Heatmap matéria × indicador (z-score, matérias objetivas)", fontsize=11,
                 loc="left", weight="bold")
    fig.colorbar(im, ax=ax, shrink=0.8, label="z-score")
    caminho_heat = _salvar(fig, "q3_heatmap.png")

    cols_saida = ["materia", "indice_composto"] + INDICADORES + ["n_resultados", "n_alunos"]
    return {
        "ranking_objetivas": obj[cols_saida].round(3).to_dict("records"),
        "redacao_a_parte": {k: (round(float(redacao[k]), 3) if k != "materia" else redacao[k])
                            for k in ["materia"] + INDICADORES + ["n_resultados", "n_alunos"]},
        "nota_ressalva": "Redação é prova dissertativa (escala 0–1000); mesmo normalizada em "
                         "nota_pct, não é estritamente comparável às objetivas, por isso fica "
                         "fora do ranking por z-score.",
        "figura_ranking": caminho_rank.name, "figura_heatmap": caminho_heat.name,
    }


# ------------------------------------------------------------------ complementares

def complementares():
    """analises adicionais (diferencial): aprovacao por universidade, canal e escola de origem."""
    uni = db.consultar("SELECT universidade, COUNT(*) n FROM aprovacoes_vestibular "
                       "GROUP BY universidade ORDER BY n DESC")
    canal = db.consultar(
        "SELECT canal_captacao, COUNT(*) n_alunos, SUM(aprovado) aprovados, "
        "ROUND(100.0*SUM(aprovado)/COUNT(*),1) taxa_aprovacao_pct "
        "FROM base_analitica_aluno GROUP BY canal_captacao ORDER BY taxa_aprovacao_pct DESC")
    escola = db.consultar(
        "SELECT escola_origem, COUNT(*) n_alunos, SUM(aprovado) aprovados, "
        "ROUND(100.0*SUM(aprovado)/COUNT(*),1) taxa_aprovacao_pct "
        "FROM base_analitica_aluno GROUP BY escola_origem ORDER BY taxa_aprovacao_pct DESC")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(uni["universidade"], uni["n"], color=COR["roxo"])
    for i, r in uni.iterrows():
        ax.annotate(str(r["n"]), (i, r["n"]), textcoords="offset points", xytext=(0, 4),
                    ha="center", fontsize=9, color="#333333")
    ax.set_ylabel("Aprovações")
    ax.set_title("Aprovações por universidade", fontsize=11, loc="left", weight="bold")
    ax.tick_params(axis="x", labelrotation=45, labelsize=9)
    caminho = _salvar(fig, "extra_aprovacoes_universidade.png")

    return {
        "aprovacoes_por_universidade": uni.to_dict("records"),
        "aprovacao_por_canal": canal.to_dict("records"),
        "aprovacao_por_escola_origem": escola.to_dict("records"),
        "figura_universidade": caminho.name,
    }


# ------------------------------------------------------------------ orquestracao

def _coerce(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if np.isnan(o) else float(o)
    raise TypeError(str(type(o)))


def main():
    _estilo()
    metricas = {
        "q1_taxa_aprovacao": q1(),
        "q2_presenca_aprovacao": q2(),
        "q3_desempenho_materia": q3(),
        "complementares": complementares(),
    }
    CAMINHO_METRICAS.parent.mkdir(parents=True, exist_ok=True)
    CAMINHO_METRICAS.write_text(
        json.dumps(metricas, ensure_ascii=False, indent=2, default=_coerce), encoding="utf-8")
    print("Analises concluidas. Figuras em reports/figures/, metricas em reports/metricas.json")
    return metricas


if __name__ == "__main__":
    main()
