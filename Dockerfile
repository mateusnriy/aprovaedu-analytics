# Ambiente reprodutivel do AprovaEdu Analytics.
# Build:  docker build -t aprovaedu .
# Pipeline: docker run --rm aprovaedu
# Dashboard: docker run --rm -p 8501:8501 aprovaedu streamlit run dashboard/app.py \
#            --server.address=0.0.0.0
FROM python:3.11-slim

WORKDIR /app

# instala as dependencias primeiro (aproveita o cache de camadas do Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copia o restante do projeto
COPY . .

# por padrao, roda o pipeline de ponta a ponta (recria banco, dados tratados, figuras, metricas)
CMD ["python", "run_pipeline.py"]
