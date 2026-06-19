FROM python:3.12-slim

WORKDIR /app

# Dependências de sistema para scikit-learn / TensorFlow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Dependências Python (camada cacheável)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código da aplicação
COPY app.py model_service.py ./

# Modelos embarcados na imagem (no EasyPanel não há volume com os arquivos).
# O model_service procura, nesta ordem de fallback:
#   baseline_pipeline_neural_v3.pkl -> modelo_tuberculose_v2.pkl -> baseline_pipeline_v3.pkl
#   modelo_redeneural_tuberculose_v1.keras
COPY baseline_pipeline_v3.pkl modelo_redeneural_tuberculose_v1.keras ./

# Porta e nº de workers configuráveis por variável de ambiente no EasyPanel.
ENV PORT=5000 \
    WEB_CONCURRENCY=2

EXPOSE 5000

# Healthcheck usa o endpoint /health (não exige curl na imagem).
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import os,urllib.request,sys; url='http://127.0.0.1:'+os.environ.get('PORT','5000')+'/health'; sys.exit(0 if urllib.request.urlopen(url, timeout=5).status==200 else 1)" || exit 1

# Forma shell para expandir ${PORT} e ${WEB_CONCURRENCY} em runtime.
CMD gunicorn --bind 0.0.0.0:${PORT} --workers ${WEB_CONCURRENCY} --timeout 120 app:app
