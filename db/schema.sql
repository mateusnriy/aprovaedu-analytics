-- Schema relacional do AprovaEdu Analytics (SQLite).
-- Modelagem em estrela enxuta: dimensoes (estudantes, professores, ofertas_curso, simulados)
-- e fatos (matriculas, aulas, presencas_aulas, resultados_simulados, aprovacoes_vestibular).
-- Datas ficam como TEXT em ISO (YYYY-MM-DD); booleanos como INTEGER 0/1.

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS resultados_simulados;
DROP TABLE IF EXISTS presencas_aulas;
DROP TABLE IF EXISTS aprovacoes_vestibular;
DROP TABLE IF EXISTS matriculas;
DROP TABLE IF EXISTS aulas;
DROP TABLE IF EXISTS simulados;
DROP TABLE IF EXISTS ofertas_curso;
DROP TABLE IF EXISTS professores;
DROP TABLE IF EXISTS estudantes;

-- ============================ DIMENSOES ============================

CREATE TABLE estudantes (
    aluno_id        TEXT PRIMARY KEY,
    nome_aluno      TEXT,
    cpf_ficticio    TEXT,
    email_aluno     TEXT,
    telefone        TEXT,
    data_nascimento TEXT,
    cidade          TEXT,
    escola_origem   TEXT,
    data_cadastro   TEXT,
    canal_captacao  TEXT
);

CREATE TABLE professores (
    professor_id           TEXT PRIMARY KEY,
    nome_professor         TEXT,
    email_professor        TEXT,
    materia_principal      TEXT,
    materias_ensina        TEXT,
    data_contratacao       TEXT,
    status_professor       TEXT,
    unidade_base           TEXT,
    carga_horaria_semanal  INTEGER,
    observacoes            TEXT
);

CREATE TABLE ofertas_curso (
    oferta_id                 TEXT PRIMARY KEY,
    ano                       INTEGER,
    turma                     TEXT,
    turno                     TEXT,
    unidade                   TEXT,
    materia                   TEXT,
    professor_id              TEXT,
    professor_nome_informado  TEXT,
    modalidade                TEXT,
    carga_horaria_total       INTEGER,
    preco_lista               REAL,
    data_inicio               TEXT,
    data_fim                  TEXT,
    FOREIGN KEY (professor_id) REFERENCES professores(professor_id)
);

CREATE TABLE simulados (
    simulado_id               TEXT PRIMARY KEY,
    ano                       INTEGER,
    data_simulado             TEXT,
    materia                   TEXT,
    professor_id              TEXT,
    professor_nome_informado  TEXT,
    dificuldade               TEXT,
    tipo_simulado             TEXT,
    total_questoes            INTEGER,
    tempo_limite_min          INTEGER,
    tema                      TEXT,
    FOREIGN KEY (professor_id) REFERENCES professores(professor_id)
);

-- ============================ FATOS ============================

CREATE TABLE aulas (
    aula_id         TEXT PRIMARY KEY,
    oferta_id       TEXT,
    ano             INTEGER,
    data_aula       TEXT,
    materia         TEXT,
    professor_id    TEXT,
    turma           TEXT,
    tema_aula       TEXT,
    duracao_min     INTEGER,
    modalidade_aula TEXT,
    FOREIGN KEY (oferta_id) REFERENCES ofertas_curso(oferta_id),
    FOREIGN KEY (professor_id) REFERENCES professores(professor_id)
);

CREATE TABLE matriculas (
    matricula_id      TEXT PRIMARY KEY,
    aluno_id          TEXT,
    oferta_id         TEXT,
    ano               INTEGER,
    materia_declarada TEXT,
    data_matricula    TEXT,
    bolsa_percentual  REAL,
    status_matricula  TEXT,
    nota_diagnostico  REAL,
    origem_captacao   TEXT,
    FOREIGN KEY (aluno_id) REFERENCES estudantes(aluno_id),
    FOREIGN KEY (oferta_id) REFERENCES ofertas_curso(oferta_id)
);

CREATE TABLE presencas_aulas (
    presenca_id      TEXT PRIMARY KEY,
    aula_id          TEXT,
    aluno_id         TEXT,
    status_presenca  TEXT,
    atraso_min       REAL,
    justificativa    TEXT,
    presente_efetivo INTEGER,
    FOREIGN KEY (aula_id) REFERENCES aulas(aula_id),
    FOREIGN KEY (aluno_id) REFERENCES estudantes(aluno_id)
);

CREATE TABLE resultados_simulados (
    resultado_id          TEXT PRIMARY KEY,
    simulado_id           TEXT,
    aluno_id              TEXT,
    ano                   INTEGER,
    materia               TEXT,
    status_realizacao     TEXT,
    nota                  REAL,
    nota_valida           REAL,
    nota_pct              REAL,
    acertos               INTEGER,
    tempo_finalizacao_min REAL,
    inicio_simulado       TEXT,
    dispositivo           TEXT,
    tentativas            INTEGER,
    unidade_aplicacao     TEXT,
    FOREIGN KEY (simulado_id) REFERENCES simulados(simulado_id),
    FOREIGN KEY (aluno_id) REFERENCES estudantes(aluno_id)
);

CREATE TABLE aprovacoes_vestibular (
    aprovacao_id          TEXT PRIMARY KEY,
    ano_vestibular        INTEGER,
    aluno_id              TEXT,
    universidade          TEXT,
    curso_aprovado        TEXT,
    modalidade_vaga       TEXT,
    chamada               TEXT,
    bolsa_aprovacao       TEXT,
    data_resultado        TEXT,
    nota_final_vestibular REAL,
    campus                TEXT,
    FOREIGN KEY (aluno_id) REFERENCES estudantes(aluno_id)
);

-- indices para os joins e filtros mais usados nas analises
CREATE INDEX idx_matriculas_aluno   ON matriculas(aluno_id);
CREATE INDEX idx_matriculas_oferta  ON matriculas(oferta_id);
CREATE INDEX idx_presencas_aluno    ON presencas_aulas(aluno_id);
CREATE INDEX idx_presencas_aula     ON presencas_aulas(aula_id);
CREATE INDEX idx_resultados_aluno   ON resultados_simulados(aluno_id);
CREATE INDEX idx_resultados_simulado ON resultados_simulados(simulado_id);
CREATE INDEX idx_aprovacoes_aluno   ON aprovacoes_vestibular(aluno_id);
