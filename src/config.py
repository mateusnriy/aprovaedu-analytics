"""Configuracao central: caminhos, escala de nota por materia e mapas canonicos.

Tudo que decide "o que e valido" mora aqui, nao espalhado pelo codigo. Assim os testes de
qualidade percorrem uma unica fonte de verdade e nenhuma coluna de materia fica esquecida.
"""
from pathlib import Path

# --- caminhos ---
RAIZ = Path(__file__).resolve().parents[1]
DIR_RAW = RAIZ / "data" / "raw"
DIR_PROCESSED = RAIZ / "data" / "processed"
DIR_DB = RAIZ / "db"
CAMINHO_DB = DIR_DB / "aprovaedu.db"
CAMINHO_SCHEMA = DIR_DB / "schema.sql"
DIR_DOCS = RAIZ / "docs"

# --- escala de nota de simulado (a correcao critica) ---
# Redacao segue a escala ENEM (0-1000); as demais materias vao de 0 a 100.
# Aplicar uma faixa 0-100 global descartaria toda a Redacao.
ESCALA_MAX = {"Redação": 1000.0}
ESCALA_PADRAO = 100.0

# --- as 5 colunas de materia da base (3 nomes de coluna diferentes) ---
# Qualquer tabela nova com materia entra aqui - e a lista que os testes percorrem.
COLUNAS_MATERIA = [
    ("simulados", "materia"),
    ("aulas", "materia"),
    ("ofertas_curso", "materia"),
    ("matriculas", "materia_declarada"),   # a mais suja: 28 grafias brutas
    ("professores", "materia_principal"),
]

MATERIAS_CANONICAS = {
    "Matemática", "Física", "Química", "Biologia", "História", "Geografia",
    "Sociologia", "Filosofia", "Português", "Inglês", "Redação",
}

ROTULO_AUSENTE = "Não informado"

# --- mapas canonicos: chave normalizada (sem acento/caixa) -> rotulo de exibicao ---
# Cada mapa cobre um dominio; varias colunas podem apontar para o mesmo dominio.
MAPAS_CANONICOS = {
    "materia": {
        "matematica": "Matemática", "mat.": "Matemática",  # 'mat.' so some com o mapa
        "fisica": "Física", "quimica": "Química", "biologia": "Biologia",
        "historia": "História", "geografia": "Geografia", "sociologia": "Sociologia",
        "filosofia": "Filosofia", "portugues": "Português", "ingles": "Inglês",
        "redacao": "Redação",
    },
    "cidade": {
        "aquiraz": "Aquiraz", "caucaia": "Caucaia", "crato": "Crato", "eusebio": "Eusébio",
        "fortaleza": "Fortaleza", "horizonte": "Horizonte", "itapipoca": "Itapipoca",
        "juazeiro do norte": "Juazeiro do Norte", "maracanau": "Maracanaú",
        "pacatuba": "Pacatuba", "sobral": "Sobral",
    },
    "escola_origem": {
        "publica": "Pública", "privada": "Privada", "federal": "Federal",
        "nao informado": ROTULO_AUSENTE,
    },
    "captacao": {
        "instagram": "Instagram", "google": "Google", "whatsapp": "WhatsApp",
        "indicacao": "Indicação", "feira escolar": "Feira escolar",
    },
    "status_professor": {"ativo": "Ativo", "inativo": "Inativo"},
    "unidade": {"aldeota": "Aldeota", "centro": "Centro", "online": "Online", "sul": "Sul"},
    "turno": {"integral": "Integral", "manha": "Manhã", "noite": "Noite", "tarde": "Tarde"},
    "modalidade": {"hibrido": "Híbrido", "online": "Online", "presencial": "Presencial"},
    "dificuldade": {"facil": "Fácil", "media": "Média", "dificil": "Difícil"},
    "tipo_simulado": {
        "enem": "ENEM", "por materia": "Por matéria", "redacao": "Redação",
        "revisao": "Revisão", "vestibular estadual": "Vestibular estadual",
    },
    "status_matricula": {
        "concluida": "Concluída", "ativa": "Ativa", "cancelada": "Cancelada",
        "trancada": "Trancada",
    },
    "status_presenca": {
        "presente": "Presente", "ausente": "Ausente", "atrasado": "Atrasado",
        "justificado": "Justificado",
    },
    "status_realizacao": {
        "finalizado": "Finalizado", "ausente": "Ausente", "incompleto": "Incompleto",
    },
    "dispositivo": {
        "celular": "Celular", "desktop": "Desktop", "papel": "Papel", "tablet": "Tablet",
    },
    "universidade": {
        "ifce": "IFCE", "uece": "UECE", "uern": "UERN", "ufc": "UFC", "ufca": "UFCA",
        "ufpe": "UFPE", "ufrn": "UFRN", "unifor": "UNIFOR", "unilab": "UNILAB", "uva": "UVA",
    },
    "modalidade_vaga": {
        "ampla concorrencia": "Ampla concorrência", "cota escola publica": "Cota escola pública",
        "pcd": "PCD", "ppi": "PPI",
    },
    "bolsa_aprovacao": {"sim": "Sim", "nao": "Não", "parcial": "Parcial"},
}

# (tabela, coluna) -> dominio no mapa acima. So colunas com dominio fechado entram aqui;
# vazio vira "Nao informado" e valor fora do mapa faz o ETL falhar alto.
COLUNA_DOMINIO = {
    ("estudantes", "cidade"): "cidade",
    ("estudantes", "escola_origem"): "escola_origem",
    ("estudantes", "canal_captacao"): "captacao",
    ("professores", "materia_principal"): "materia",
    ("professores", "status_professor"): "status_professor",
    ("professores", "unidade_base"): "unidade",
    ("ofertas_curso", "materia"): "materia",
    ("ofertas_curso", "turno"): "turno",
    ("ofertas_curso", "unidade"): "unidade",
    ("ofertas_curso", "modalidade"): "modalidade",
    ("simulados", "materia"): "materia",
    ("simulados", "dificuldade"): "dificuldade",
    ("simulados", "tipo_simulado"): "tipo_simulado",
    ("aulas", "materia"): "materia",
    ("aulas", "modalidade_aula"): "modalidade",
    ("matriculas", "materia_declarada"): "materia",
    ("matriculas", "status_matricula"): "status_matricula",
    ("matriculas", "origem_captacao"): "captacao",
    ("presencas_aulas", "status_presenca"): "status_presenca",
    ("resultados_simulados", "status_realizacao"): "status_realizacao",
    ("resultados_simulados", "dispositivo"): "dispositivo",
    ("resultados_simulados", "unidade_aplicacao"): "unidade",
    ("aprovacoes_vestibular", "universidade"): "universidade",
    ("aprovacoes_vestibular", "modalidade_vaga"): "modalidade_vaga",
    ("aprovacoes_vestibular", "bolsa_aprovacao"): "bolsa_aprovacao",
}

# status de matricula que contam como aluno efetivamente ativo (denominador da taxa de aprovacao)
STATUS_MATRICULA_ATIVA = {"Concluída", "Ativa", "Trancada"}

# presenca efetiva = esteve na aula
STATUS_PRESENCA_EFETIVA = {"Presente", "Atrasado"}

# ordem de prioridade na dedup de matriculas (mais avancado vence)
PRIORIDADE_STATUS_MATRICULA = {"Concluída": 4, "Ativa": 3, "Trancada": 2, "Cancelada": 1,
                               ROTULO_AUSENTE: 0}

# intervalo de anos das tabelas transacionais (para validar datas parseadas)
ANO_MIN, ANO_MAX = 2021, 2025
