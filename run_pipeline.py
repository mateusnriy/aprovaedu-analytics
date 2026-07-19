"""Pipeline de ponta a ponta: dados brutos -> banco relacional -> bases analiticas.

Um comando recria tudo do zero, de forma idempotente:

    python run_pipeline.py
"""
from src import etl, db, base_analitica, config


def main():
    log = etl._Log()

    # 1. tratamento das 9 tabelas
    dfs = etl.executar_etl(log)

    # 2. export dos dados tratados (copia legivel) + carga no banco relacional
    etl.exportar_csv(dfs)
    db.construir_banco(dfs)

    # 3. bases analiticas (aluno e materia) -> banco + CSV
    df_aluno, df_materia = base_analitica.montar_bases(dfs)
    base_analitica.persistir(df_aluno, df_materia)

    # 4. log do tratamento
    log.escrever(config.DIR_DOCS / "log_tratamento.md")

    print("Pipeline concluido.")
    for nome, df in dfs.items():
        print(f"  {nome:24s} {len(df):6d} linhas")
    print(f"  base_analitica_aluno     {len(df_aluno):6d} linhas")
    print(f"  base_analitica_materia   {len(df_materia):6d} linhas")
    print(f"banco: {config.CAMINHO_DB}")


if __name__ == "__main__":
    main()
