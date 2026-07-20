"""
Modelo simples e interpretavel (regressao logistica). 
"""
from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src import config, db, analysis

SEED = 42
NUM = ["nota_diagnostico_media", "taxa_presenca", "nota_pct_media", "n_matriculas"]
CAT = ["escola_origem", "canal_captacao"]
ROTULO = {
    "nota_diagnostico_media": "Nota diagnóstica",
    "taxa_presenca": "Taxa de presença",
    "nota_pct_media": "Nota de simulado (%)",
    "n_matriculas": "Nº de matrículas",
}


def _pipeline():
    pre = ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median")),
                          ("sc", StandardScaler())]), NUM),
        ("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), CAT),
    ])
    modelo = LogisticRegression(max_iter=1000, random_state=SEED)
    return Pipeline([("pre", pre), ("modelo", modelo)])


def treinar_e_pontuar():
    base = db.consultar("SELECT * FROM base_analitica_aluno")
    X = base[NUM + CAT]
    y = base["aprovado"].astype(int)

    pipe = _pipeline()

    # validacao cruzada (5-fold estratificado) em vez de um unico split
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    aucs = cross_val_score(pipe, X, y, cv=cv, scoring="roc_auc")

    # ajuste final em toda a base para ler os coeficientes / odds ratios
    pipe.fit(X, y)
    nomes = NUM + list(pipe.named_steps["pre"].named_transformers_["cat"]
                       .get_feature_names_out(CAT))
    coefs = pipe.named_steps["modelo"].coef_[0]
    odds = np.exp(coefs)
    tabela = (pd.DataFrame({"feature": nomes, "coef": coefs, "odds_ratio": odds})
              .sort_values("coef", ascending=False))

    # propensao por aluno + segmentacao em tercis
    base["propensao"] = pipe.predict_proba(X)[:, 1]
    base["segmento"] = pd.qcut(base["propensao"], 3,
                               labels=["Baixa propensão", "Média propensão", "Alta propensão"])

    return base, aucs, tabela


def _figura_odds(tabela):
    # so os preditores numericos, que sao os interpretaveis e comparaveis (ja padronizados)
    num = tabela[tabela["feature"].isin(NUM)].copy()
    num["rotulo"] = num["feature"].map(ROTULO)
    num = num.sort_values("coef")
    cores = [analysis.COR["verde"] if c >= 0 else analysis.COR["vermelho"] for c in num["coef"]]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(num["rotulo"], num["coef"], color=cores)
    ax.axvline(0, color="#B0B0B0", lw=1)
    for i, (_, r) in enumerate(num.iterrows()):
        # positivo: rotulo a direita da ponta; negativo: a direita do zero (espaco vazio da linha)
        xpos = r["coef"] if r["coef"] >= 0 else 0
        ax.annotate(f"OR={r['odds_ratio']:.2f}", (xpos, i), textcoords="offset points",
                    xytext=(6, 0), ha="left", va="center", fontsize=9, color="#333333")
    ax.set_xlabel("Coeficiente (features padronizadas) — >0 aumenta a propensão")
    ax.set_title("Score — peso de cada fator na propensão à aprovação", fontsize=11, loc="left",
                 weight="bold")
    return analysis._salvar(fig, "score_coeficientes.png")


def main():
    analysis._estilo()
    base, aucs, tabela = treinar_e_pontuar()

    # persiste a base pontuada (CSV + banco)
    saida = base[["aluno_id", "propensao", "segmento", "aprovado"]]
    saida.to_csv(config.DIR_PROCESSED / "base_analitica_aluno_score.csv", index=False,
                 encoding="utf-8")
    conn = db.conectar()
    try:
        saida.to_sql("base_analitica_aluno_score", conn, if_exists="replace", index=False)
        conn.commit()
    finally:
        conn.close()

    caminho_fig = _figura_odds(tabela)

    resultado = {
        "cv_auc_media": round(float(aucs.mean()), 3),
        "cv_auc_desvio": round(float(aucs.std()), 3),
        "coeficientes": tabela.round(3).to_dict("records"),
        "distribuicao_segmentos": base["segmento"].value_counts().to_dict(),
        "figura": caminho_fig.name,
    }

    # anexa o score ao metricas.json ja existente
    metricas = json.loads(analysis.CAMINHO_METRICAS.read_text(encoding="utf-8"))
    metricas["score_propensao"] = resultado
    analysis.CAMINHO_METRICAS.write_text(
        json.dumps(metricas, ensure_ascii=False, indent=2, default=analysis._coerce),
        encoding="utf-8")

    print(f"Score concluido. AUC (5-fold) = {aucs.mean():.3f} +/- {aucs.std():.3f}")
    return resultado


if __name__ == "__main__":
    main()
