# Predição de Abandono do Tratamento de Tuberculose — Front + API

Aplicação acadêmica de **apoio à decisão clínica** que estima o risco de um
paciente **abandonar** o tratamento de tuberculose. O usuário preenche os dados
do paciente no frontend, que envia para a API de Machine Learning; a API roda
**dois modelos** e devolve, para cada um, a probabilidade de abandono/cura e uma
recomendação de conduta.

> ⚠️ Ferramenta acadêmica de apoio à decisão. **Não substitui avaliação clínica.**

## Arquitetura

```
┌──────────────────────────┐        POST /predict (JSON)        ┌──────────────────────────────┐
│  tb-predict (frontend)   │  ───────────────────────────────▶  │  nano_tuberculose (API)      │
│  React + Vite + TS       │                                    │  Flask + CORS                │
│  http://localhost:5173   │  ◀───────────────────────────────  │  http://localhost:5001       │
└──────────────────────────┘     resposta dos 2 modelos         └──────────────────────────────┘
                                                                   ├─ Regressão Logística (.pkl / scikit-learn)
                                                                   └─ Rede Neural (.keras / TensorFlow)
```

> **Por que a porta 5001?** No macOS a porta 5000 é ocupada pelo *AirPlay
> Receiver*, então a API roda na **5001** (configurável via env `PORT`).

## Estrutura do repositório

```
.
├── tb-predict/         # Frontend: React + Vite + TypeScript + TailwindCSS
└── nano_tuberculose/   # API: Flask + modelos de ML
    ├── app.py                 # endpoints /predict, /predict/logistic, /predict/neural, /health
    ├── model_service.py       # carrega e roda os dois modelos
    ├── baseline_pipeline_v3.pkl              # pipeline da Regressão Logística
    ├── modelo_redeneural_tuberculose_v1.keras  # modelo da Rede Neural
    ├── test_api.py            # testes da API por linha de comando
    ├── Dockerfile / docker-compose.yml
    └── 00_Trabalho_tuberculose_v3.ipynb     # notebook de treino/análise
```

## Como rodar

São dois serviços. A forma mais simples é via **Docker** para a API; alternativa
sem Docker logo abaixo.

### 1. API (backend)

**Opção A — Docker (recomendada, já expõe na 5001):**

```bash
cd nano_tuberculose
docker compose up --build
```

**Opção B — local com Python 3.12 (TensorFlow ainda não suporta 3.13+):**

```bash
cd nano_tuberculose
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py            # sobe em http://localhost:5001
```

Verifique a saúde da API:

```bash
curl http://localhost:5001/health
```

### 2. Frontend

```bash
cd tb-predict
npm install
npm run dev              # abre em http://localhost:5173
```

Abra **http://localhost:5173**, preencha o formulário e clique em analisar.

## Exemplo de requisição

```bash
curl -s -X POST http://localhost:5001/predict \
  -H "Content-Type: application/json" \
  -d '{
    "idade_anos": 35, "CS_SEXO": "M", "CS_GESTANT": "6", "CS_RACA": "1",
    "CS_ESCOL_N": "3", "SG_UF": "35", "TRATAMENTO": "1", "POP_LIBER": "2",
    "POP_RUA": "1", "POP_SAUDE": "2", "POP_IMIG": "2", "FORMA": "1",
    "AGRAVALCOO": "2", "AGRAVDIABE": "2", "AGRAVDOENC": "2", "AGRAVOUTRA": "2",
    "HIV": "1", "SG_UF_2": "35", "TRATSUP_AT": "1", "TRANSF": "2"
  }' | python3 -m json.tool
```

Resposta (resumida):

```json
{
  "logistic_regression": { "prediction_label": "Abandono", "probability_abandono": 59.59, "recommendation": "Risco moderado..." },
  "neural_network":       { "prediction_label": "Abandono", "probability_abandono": 94.93, "recommendation": "Alerta de alto risco..." }
}
```

## API

| Método | Rota                | Descrição                              |
|--------|---------------------|----------------------------------------|
| POST   | `/predict`          | Roda os dois modelos                   |
| POST   | `/predict/logistic` | Apenas a Regressão Logística           |
| POST   | `/predict/neural`   | Apenas a Rede Neural                   |
| GET    | `/health`           | Status da API e dos modelos carregados |

Todos os campos do payload são enviados como **string**, exceto `idade_anos`
(número). Faixas de risco usadas na recomendação: **<40%** baixo · **40–70%**
moderado · **>70%** alto.

## Stack

- **Frontend:** React 18, Vite 6, TypeScript, TailwindCSS 4
- **Backend:** Flask 3, flask-cors, scikit-learn, TensorFlow/Keras, pandas, joblib
- **Deploy:** Docker / gunicorn
