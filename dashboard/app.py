import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
PROC = RAIZ / "data" / "processed"
FIG = RAIZ / "reports" / "figures"
METRICAS = RAIZ / "reports" / "metricas.json"

COR = {"azul": "#0072B2", "laranja": "#E69F00", "verde": "#009E73", "vermelho": "#D55E00",
       "roxo": "#CC79A7", "cinza": "#7F7F7F"}

st.set_page_config(page_title="AprovaEdu Analytics", page_icon="🎓", layout="wide")


@st.cache_data
def carregar():
    aluno = pd.read_csv(PROC / "base_analitica_aluno.csv")
    materia = pd.read_csv(PROC / "base_analitica_materia.csv")
    score = pd.read_csv(PROC / "base_analitica_aluno_score.csv")
    metricas = json.loads(METRICAS.read_text(encoding="utf-8"))
    return aluno, materia, score, metricas


def estilo_ax(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, color="#E6E6E6", lw=0.8, axis="both")
    ax.set_axisbelow(True)
    return ax


aluno, materia, score, metricas = carregar()

# ---------------- barra lateral: filtros do pool de alunos ----------------
st.sidebar.title("Filtros")
st.sidebar.caption("Afetam os indicadores por aluno (visão geral, presença e score).")

canais = sorted(aluno["canal_captacao"].dropna().unique())
escolas = sorted(aluno["escola_origem"].dropna().unique())
cidades = sorted(aluno["cidade"].dropna().unique())

sel_canal = st.sidebar.multiselect("Canal de captação", canais, default=canais)
sel_escola = st.sidebar.multiselect("Escola de origem", escolas, default=escolas)
sel_cidade = st.sidebar.multiselect("Cidade", cidades, default=cidades)

pool = aluno[aluno["canal_captacao"].isin(sel_canal)
             & aluno["escola_origem"].isin(sel_escola)
             & aluno["cidade"].isin(sel_cidade)].copy()

# ---------------- cabecalho ----------------
st.title("🎓 AprovaEdu Analytics")
st.caption("Rede de cursinhos pré-vestibular · 2021–2025 · dados gerados pelo pipeline do projeto")

if pool.empty:
    st.warning("Nenhum aluno na seleção atual. Ajuste os filtros na barra lateral.")
    st.stop()

# ---------------- KPIs ----------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Alunos (na seleção)", f"{len(pool):,}".replace(",", "."))
c2.metric("Aprovados (na seleção)", int(pool["aprovado"].sum()))
c3.metric("% aprovados (na seleção)", f"{pool['aprovado'].mean() * 100:.1f}%")
c4.metric("Presença média", f"{pool['taxa_presenca'].mean():.1f}%")

st.divider()

aba1, aba2, aba3, aba4 = st.tabs(
    ["Visão geral (Q1)", "Presença × aprovação (Q2)", "Desempenho por matéria (Q3)", "Score"])

# ---------------- aba 1: Q1 + aprovação por canal ----------------
with aba1:
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Taxa de aprovação por ano")
        st.caption("Base completa (aprovados distintos ÷ matriculados distintos).")
        q1 = pd.DataFrame(metricas["q1_taxa_aprovacao"]["por_ano"])
        fig, ax = plt.subplots(figsize=(6, 3.5))
        estilo_ax(ax)
        ax.plot(q1["ano"], q1["taxa_aprovacao_pct"], color=COR["azul"], marker="o", lw=2)
        for _, r in q1.iterrows():
            ax.annotate(f"{r['taxa_aprovacao_pct']:.1f}%", (r["ano"], r["taxa_aprovacao_pct"]),
                        textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)
        ax.set_ylim(0, q1["taxa_aprovacao_pct"].max() * 1.35)
        ax.set_xticks(q1["ano"])
        ax.set_ylabel("Taxa (%)")
        st.pyplot(fig)
    with col_b:
        st.subheader("Aprovação por canal de captação (na seleção)")
        canal = (pool.groupby("canal_captacao")["aprovado"].agg(["mean", "count"]) * [100, 1])
        canal = canal.rename(columns={"mean": "taxa", "count": "n"}).sort_values("taxa",
                                                                                 ascending=False)
        fig, ax = plt.subplots(figsize=(6, 3.5))
        estilo_ax(ax)
        ax.bar(canal.index, canal["taxa"], color=COR["azul"])
        for i, (_, r) in enumerate(canal.iterrows()):
            ax.annotate(f"{r['taxa']:.0f}%\n(n={int(r['n'])})", (i, r["taxa"]),
                        textcoords="offset points", xytext=(0, 4), ha="center", fontsize=8)
        ax.set_ylim(0, canal["taxa"].max() * 1.3)
        ax.set_ylabel("Taxa de aprovação (%)")
        ax.tick_params(axis="x", labelrotation=30)
        st.pyplot(fig)

# ---------------- aba 2: Q2 presenca ----------------
with aba2:
    st.subheader("Presença × aprovação (na seleção)")
    q2 = metricas["q2_presenca_aprovacao"]
    st.caption(f"Teste na base completa — Mann-Whitney p={q2['mannwhitney_p']}, "
               f"correlação point-biserial r={q2['pointbiserial_r']} "
               f"(sem associação relevante entre presença e aprovação).")
    col_a, col_b = st.columns(2)
    with col_a:
        aprov = pool.loc[pool["aprovado"] == 1, "taxa_presenca"].dropna()
        nao = pool.loc[pool["aprovado"] == 0, "taxa_presenca"].dropna()
        fig, ax = plt.subplots(figsize=(6, 4))
        estilo_ax(ax)
        bp = ax.boxplot([nao, aprov], labels=[f"Não aprov.\n(n={len(nao)})",
                                              f"Aprov.\n(n={len(aprov)})"], patch_artist=True,
                        widths=0.55, medianprops=dict(color="#222", lw=1.5))
        for patch, cor in zip(bp["boxes"], [COR["cinza"], COR["verde"]]):
            patch.set_facecolor(cor)
            patch.set_alpha(0.75)
        ax.set_ylabel("Taxa de presença (%)")
        st.pyplot(fig)
    with col_b:
        faixas = pd.cut(pool["taxa_presenca"], [0, 75, 85, 90, 100],
                        labels=["<75%", "75-85%", "85-90%", ">90%"])
        tab = pool.groupby(faixas, observed=True)["aprovado"].agg(["mean", "count"])
        tab["taxa"] = tab["mean"] * 100
        fig, ax = plt.subplots(figsize=(6, 4))
        estilo_ax(ax)
        ax.bar(tab.index.astype(str), tab["taxa"], color=COR["azul"])
        for i, (_, r) in enumerate(tab.iterrows()):
            ax.annotate(f"{r['taxa']:.0f}%\n(n={int(r['count'])})", (i, r["taxa"]),
                        textcoords="offset points", xytext=(0, 4), ha="center", fontsize=8)
        ax.set_ylim(0, max(tab["taxa"].max() * 1.3, 1))
        ax.set_ylabel("Taxa de aprovação (%)")
        st.pyplot(fig)

# ---------------- aba 3: Q3 materia ----------------
with aba3:
    st.subheader("Ranking de matérias por índice composto")
    st.caption("Base completa. Redação fica à parte (prova dissertativa, escala 0–1000).")
    rank = pd.DataFrame(metricas["q3_desempenho_materia"]["ranking_objetivas"])
    fig, ax = plt.subplots(figsize=(8, 4.5))
    estilo_ax(ax)
    ax.barh(rank["materia"], rank["indice_composto"], color=COR["azul"])
    ax.invert_yaxis()
    ax.axvline(0, color="#B0B0B0", lw=1)
    ax.set_xlabel("Índice composto (média de 4 z-scores)")
    st.pyplot(fig)
    st.image(str(FIG / "q3_heatmap.png"), caption="Heatmap matéria × indicador (z-score)")
    st.dataframe(materia.round(1), use_container_width=True)

# ---------------- aba 4: score ----------------
with aba4:
    sc = metricas.get("score_propensao", {})
    st.subheader("Score de propensão à aprovação")
    st.caption(f"Regressão logística, validação cruzada 5-fold · AUC = "
               f"{sc.get('cv_auc_media', '—')} ± {sc.get('cv_auc_desvio', '—')}. "
               f"Modelo interpretável (foco nos coeficientes, não em maximizar AUC).")
    pool_score = pool.merge(score[["aluno_id", "propensao", "segmento"]], on="aluno_id",
                            how="left")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Distribuição por segmento (na seleção)**")
        seg = pool_score["segmento"].value_counts().reindex(
            ["Baixa propensão", "Média propensão", "Alta propensão"]).fillna(0)
        fig, ax = plt.subplots(figsize=(6, 4))
        estilo_ax(ax)
        ax.bar(seg.index, seg.values, color=[COR["vermelho"], COR["laranja"], COR["verde"]])
        for i, v in enumerate(seg.values):
            ax.annotate(int(v), (i, v), textcoords="offset points", xytext=(0, 4), ha="center")
        ax.set_ylabel("Alunos")
        ax.tick_params(axis="x", labelrotation=15)
        st.pyplot(fig)
    with col_b:
        st.markdown("**Peso de cada fator**")
        st.image(str(FIG / "score_coeficientes.png"))

st.divider()
st.caption("Fonte: pipeline do projeto (`python run_pipeline.py`). Todos os números derivam dos "
           "dados tratados e de `reports/metricas.json`.")
