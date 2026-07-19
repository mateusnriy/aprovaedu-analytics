"""ETL: le os 9 CSVs brutos, trata, e devolve as tabelas limpas prontas para o banco.
Ordem que importa: canonicalizar categoricas -> tipar numeros/datas -> escala de nota por
materia -> deduplicar. Tudo que for decisao de negocio esta em config.py.
"""
from __future__ import annotations

import unicodedata
import numpy as np
import pandas as pd

from src import config


# utilidades

def _normkey(valor: str) -> str:
    """chave de comparacao: sem acento, sem caixa, sem espaco nas pontas."""
    valor = str(valor).strip().lower()
    return unicodedata.normalize("NFKD", valor).encode("ascii", "ignore").decode("ascii")


def _ler_csv(nome: str) -> pd.DataFrame:
    # le tudo como texto pra tipar depois de forma controlada
    return pd.read_csv(config.DIR_RAW / f"{nome}.csv", encoding="utf-8-sig",
                       dtype=str, keep_default_na=False)


def _num(serie: pd.Series) -> pd.Series:
    """texto -> float; vazio e lixo viram NaN."""
    return pd.to_numeric(serie.replace("", np.nan), errors="coerce")


def _int(serie: pd.Series) -> pd.Series:
    """texto -> inteiro nullable (mantem NaN sem virar float feio no CSV)."""
    return _num(serie).astype("Int64")


# datas aparecem em varios formatos na mesma coluna; tento barra/BR antes de traco/US
# pra nao trocar dia por mes (os separadores diferentes tiram a ambiguidade)
_FORMATOS_DATA = [
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
    "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y",
    "%m-%d-%Y %H:%M:%S", "%m-%d-%Y %H:%M", "%m-%d-%Y",
    "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y/%m/%d",
]


def _parse_datas(serie: pd.Series, com_hora: bool = False) -> pd.Series:
    """parser em cascata; devolve string ISO (com hora se com_hora)."""
    s = serie.replace("", np.nan)
    resultado = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    pendente = s.notna()
    for fmt in _FORMATOS_DATA:
        if not pendente.any():
            break
        tentativa = pd.to_datetime(s.where(pendente), format=fmt, errors="coerce")
        ok = tentativa.notna()
        resultado = resultado.where(~ok, tentativa)
        pendente = pendente & ~ok
    fmt_saida = "%Y-%m-%d %H:%M:%S" if com_hora else "%Y-%m-%d"
    return resultado.dt.strftime(fmt_saida)


def _canonicalizar(serie: pd.Series, dominio: str, ref: str) -> pd.Series:
    """aplica o mapa canonico; vazio -> 'Nao informado'; valor fora do mapa -> erro.
    Falhar alto aqui e proposital: uma grafia nova nao pode virar categoria fantasma em
    silencio (foi assim que o bug de escala passou despercebido em outra avaliacao).
    """
    mapa = config.MAPAS_CANONICOS[dominio]

    def conv(v):
        v = str(v).strip()
        if v == "":
            return config.ROTULO_AUSENTE
        chave = _normkey(v)
        if chave in mapa:
            return mapa[chave]
        raise ValueError(
            f"{ref}: grafia fora do mapa canonico '{dominio}': {v!r} (normkey={chave!r}). "
            f"Investigar antes de seguir - nao criar categoria nova em silencio."
        )

    return serie.map(conv)


class _Log:
    """acumula as linhas do log de tratamento (achado -> acao -> registros)."""

    def __init__(self):
        self.linhas: list[str] = []

    def add(self, msg: str):
        self.linhas.append(msg)

    def escrever(self, caminho):
        cabecalho = (
            "# Log de tratamento\n\n"
            "Gerado automaticamente pelo `src/etl.py`. Registra o que cada etapa do ETL fez e "
            "quantos registros foram afetados, na ordem em que rodou.\n\n"
        )
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(cabecalho + "\n".join(self.linhas) + "\n", encoding="utf-8")


# limpeza por tabela

def _aplicar_categoricas(nome: str, df: pd.DataFrame) -> pd.DataFrame:
    for (tab, col), dominio in config.COLUNA_DOMINIO.items():
        if tab == nome:
            df[col] = _canonicalizar(df[col], dominio, f"{tab}.{col}")
    return df


def _limpar_estudantes(df, log):
    df = _aplicar_categoricas("estudantes", df)
    df["cpf_ficticio"] = df["cpf_ficticio"].str.replace(r"\D", "", regex=True)  # so digitos
    df["data_nascimento"] = _parse_datas(df["data_nascimento"])
    df["data_cadastro"] = _parse_datas(df["data_cadastro"])
    log.add("## estudantes\n- 812 alunos, categoricas canonicalizadas (cidade, escola, canal).")
    return df


def _limpar_professores(df, log):
    df = _aplicar_categoricas("professores", df)
    df["data_contratacao"] = _parse_datas(df["data_contratacao"])
    df["carga_horaria_semanal"] = _int(df["carga_horaria_semanal"])
    log.add("## professores\n- 35 professores, materia_principal e status canonicalizados.")
    return df


def _limpar_ofertas(df, log):
    df = _aplicar_categoricas("ofertas_curso", df)
    df["ano"] = _int(df["ano"])
    df["carga_horaria_total"] = _int(df["carga_horaria_total"])
    df["preco_lista"] = _num(df["preco_lista"])
    df["data_inicio"] = _parse_datas(df["data_inicio"])
    df["data_fim"] = _parse_datas(df["data_fim"])
    log.add("## ofertas_curso\n- 220 ofertas, materia/turno/unidade/modalidade canonicalizados.")
    return df


def _limpar_simulados(df, log):
    df = _aplicar_categoricas("simulados", df)
    df["ano"] = _int(df["ano"])
    df["data_simulado"] = _parse_datas(df["data_simulado"])
    df["total_questoes"] = _int(df["total_questoes"])
    df["tempo_limite_min"] = _int(df["tempo_limite_min"])
    log.add("## simulados\n- 165 simulados, materia/dificuldade/tipo canonicalizados.")
    return df


def _limpar_aulas(df, log):
    df = _aplicar_categoricas("aulas", df)
    df["ano"] = _int(df["ano"])
    df["data_aula"] = _parse_datas(df["data_aula"])
    df["duracao_min"] = _int(df["duracao_min"])
    n0 = len(df)
    df = df.drop_duplicates(subset=["aula_id"])
    log.add(f"## aulas\n- {len(df)} aulas, materia/modalidade canonicalizados "
            f"({n0 - len(df)} PKs duplicadas removidas).")
    return df


def _limpar_matriculas(df, log):
    df = _aplicar_categoricas("matriculas", df)
    df["ano"] = _int(df["ano"])
    df["data_matricula"] = _parse_datas(df["data_matricula"])
    df["bolsa_percentual"] = _num(df["bolsa_percentual"])
    df["nota_diagnostico"] = _num(df["nota_diagnostico"])
    # dedup de negocio: 1 linha por (aluno, oferta), status mais avancado e data mais recente
    n0 = len(df)
    df["_prio"] = df["status_matricula"].map(config.PRIORIDADE_STATUS_MATRICULA).fillna(0)
    df = (df.sort_values(["_prio", "data_matricula"], ascending=[False, False])
            .drop_duplicates(subset=["aluno_id", "oferta_id"], keep="first")
            .drop(columns="_prio")
            .sort_values("matricula_id"))
    log.add(f"## matriculas\n- materia_declarada (28 grafias) e status canonicalizados.\n"
            f"- dedup (aluno, oferta): {n0 - len(df)} linhas removidas, {len(df)} mantidas.")
    return df


def _limpar_presencas(df, log):
    df = _aplicar_categoricas("presencas_aulas", df)
    df["atraso_min"] = _num(df["atraso_min"])
    df["presente_efetivo"] = df["status_presenca"].isin(config.STATUS_PRESENCA_EFETIVA).astype(int)
    n0 = len(df)
    df = df.drop_duplicates(subset=["aluno_id", "aula_id"], keep="first")
    log.add(f"## presencas_aulas\n- status canonicalizado; presente_efetivo derivado "
            f"(Presente/Atrasado).\n- dedup (aluno, aula): {n0 - len(df)} removidas, {len(df)} mantidas.")
    return df


def _limpar_resultados(df, simulados, log):
    df = _aplicar_categoricas("resultados_simulados", df)
    df["ano"] = _int(df["ano"])
    df["nota"] = _num(df["nota"])
    df["acertos"] = _int(df["acertos"])
    df["tempo_finalizacao_min"] = _num(df["tempo_finalizacao_min"])
    df["tentativas"] = _int(df["tentativas"])
    df["inicio_simulado"] = _parse_datas(df["inicio_simulado"], com_hora=True)

    # traz a materia do simulado (ja canonica) - a escala depende dela
    materia_por_simulado = simulados.set_index("simulado_id")["materia"]
    df["materia"] = df["simulado_id"].map(materia_por_simulado)

    # escala POR MATERIA: Redacao 0-1000, demais 0-100
    escala = df["materia"].map(config.ESCALA_MAX).fillna(config.ESCALA_PADRAO)
    dentro = df["nota"].between(0, escala)
    df["nota_valida"] = df["nota"].where(dentro)          # fora da faixa -> NaN (nunca truncar)
    df["nota_pct"] = df["nota_valida"] / escala * 100      # normalizado p/ comparar materias

    fora = int((df["nota"].notna() & ~dentro).sum())
    # dedup: melhor nota_valida por (aluno, simulado)
    n0 = len(df)
    df = (df.sort_values("nota_valida", ascending=False, na_position="last")
            .drop_duplicates(subset=["aluno_id", "simulado_id"], keep="first")
            .sort_values("resultado_id"))
    log.add(f"## resultados_simulados\n- escala por materia aplicada (Redacao 0-1000, "
            f"demais 0-100); {fora} notas fora da faixa viraram ausentes (nunca truncadas).\n"
            f"- dedup (aluno, simulado): {n0 - len(df)} removidas, {len(df)} mantidas.")
    return df


def _limpar_aprovacoes(df, log):
    df = _aplicar_categoricas("aprovacoes_vestibular", df)
    df["ano_vestibular"] = _int(df["ano_vestibular"])
    df["nota_final_vestibular"] = _num(df["nota_final_vestibular"])
    df["data_resultado"] = _parse_datas(df["data_resultado"])

    # duplicidade de cadastro: remover linhas 'Cadastro duplicado?' que tenham par identico
    # (mesmo aluno, ano e nota). Confirmar o par, nao remover cego por chamada.
    chave = ["aluno_id", "ano_vestibular", "nota_final_vestibular"]
    tam_grupo = df.groupby(chave)[chave[0]].transform("size")
    marcada = df["chamada"].astype(str).str.strip() == "Cadastro duplicado?"
    remover = marcada & (tam_grupo >= 2)
    n_remover = int(remover.sum())
    df = df[~remover].copy()
    log.add(f"## aprovacoes_vestibular\n- universidade e modalidade canonicalizadas.\n"
            f"- {n_remover} duplicidades de cadastro removidas (chamada='Cadastro duplicado?' "
            f"com par identico confirmado): de 354 para {len(df)} aprovacoes.")
    return df


# orquestracao

def executar_etl(log: _Log | None = None) -> dict[str, pd.DataFrame]:
    """le e trata as 9 tabelas; devolve dicionario de DataFrames limpos."""
    log = log or _Log()

    est = _limpar_estudantes(_ler_csv("estudantes"), log)
    prof = _limpar_professores(_ler_csv("professores"), log)
    ofe = _limpar_ofertas(_ler_csv("ofertas_curso"), log)
    sim = _limpar_simulados(_ler_csv("simulados"), log)
    aul = _limpar_aulas(_ler_csv("aulas"), log)
    matr = _limpar_matriculas(_ler_csv("matriculas"), log)
    pres = _limpar_presencas(_ler_csv("presencas_aulas"), log)
    res = _limpar_resultados(_ler_csv("resultados_simulados"), sim, log)
    apr = _limpar_aprovacoes(_ler_csv("aprovacoes_vestibular"), log)

    return {
        "estudantes": est, "professores": prof, "ofertas_curso": ofe, "simulados": sim,
        "aulas": aul, "matriculas": matr, "presencas_aulas": pres,
        "resultados_simulados": res, "aprovacoes_vestibular": apr,
    }


# colunas exportadas por tabela (ordem = ordem do schema)
COLUNAS_SAIDA = {
    "estudantes": ["aluno_id", "nome_aluno", "cpf_ficticio", "email_aluno", "telefone",
                   "data_nascimento", "cidade", "escola_origem", "data_cadastro", "canal_captacao"],
    "professores": ["professor_id", "nome_professor", "email_professor", "materia_principal",
                    "materias_ensina", "data_contratacao", "status_professor", "unidade_base",
                    "carga_horaria_semanal", "observacoes"],
    "ofertas_curso": ["oferta_id", "ano", "turma", "turno", "unidade", "materia", "professor_id",
                      "professor_nome_informado", "modalidade", "carga_horaria_total",
                      "preco_lista", "data_inicio", "data_fim"],
    "simulados": ["simulado_id", "ano", "data_simulado", "materia", "professor_id",
                  "professor_nome_informado", "dificuldade", "tipo_simulado", "total_questoes",
                  "tempo_limite_min", "tema"],
    "aulas": ["aula_id", "oferta_id", "ano", "data_aula", "materia", "professor_id", "turma",
              "tema_aula", "duracao_min", "modalidade_aula"],
    "matriculas": ["matricula_id", "aluno_id", "oferta_id", "ano", "materia_declarada",
                   "data_matricula", "bolsa_percentual", "status_matricula", "nota_diagnostico",
                   "origem_captacao"],
    "presencas_aulas": ["presenca_id", "aula_id", "aluno_id", "status_presenca", "atraso_min",
                        "justificativa", "presente_efetivo"],
    "resultados_simulados": ["resultado_id", "simulado_id", "aluno_id", "ano", "materia",
                             "status_realizacao", "nota", "nota_valida", "nota_pct", "acertos",
                             "tempo_finalizacao_min", "inicio_simulado", "dispositivo",
                             "tentativas", "unidade_aplicacao"],
    "aprovacoes_vestibular": ["aprovacao_id", "ano_vestibular", "aluno_id", "universidade",
                              "curso_aprovado", "modalidade_vaga", "chamada", "bolsa_aprovacao",
                              "data_resultado", "nota_final_vestibular", "campus"],
}


def exportar_csv(dfs: dict[str, pd.DataFrame]):
    """exporta as tabelas tratadas para data/processed (copia legivel dos dados tratados)."""
    config.DIR_PROCESSED.mkdir(parents=True, exist_ok=True)
    for nome, cols in COLUNAS_SAIDA.items():
        dfs[nome][cols].to_csv(config.DIR_PROCESSED / f"{nome}.csv", index=False,
                               encoding="utf-8")


def main():
    """roda o ETL, carrega o banco relacional e exporta os CSVs tratados."""
    from src import db

    log = _Log()
    dfs = executar_etl(log)
    exportar_csv(dfs)
    db.construir_banco(dfs)
    log.escrever(config.DIR_DOCS / "log_tratamento.md")
    print("ETL concluido:")
    for nome, df in dfs.items():
        print(f"  {nome:24s} {len(df):6d} linhas")
    print(f"banco: {config.CAMINHO_DB}")


if __name__ == "__main__":
    main()
