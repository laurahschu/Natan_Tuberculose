# Predição de Abandono do Tratamento de Tuberculose — Front + API

Aplicação acadêmica de **apoio à decisão clínica** que estima o risco de um
paciente **abandonar** o tratamento de tuberculose. O usuário preenche os dados
do paciente no frontend, que envia para a API de Machine Learning; a API roda um
modelo de **rede neural** e devolve a **probabilidade de abandono** e uma
recomendação de conduta.

> ⚠️ Ferramenta acadêmica de apoio à decisão. **Não substitui avaliação clínica.**

## Arquitetura

```
┌──────────────────────────┐   POST /predict/neural (JSON)   ┌──────────────────────────────┐
│  tb-predict (frontend)   │  ─────────────────────────────▶  │  nano_tuberculose (API)      │
│  React + Vite + TS       │                                  │  Flask + CORS                │
│  http://localhost:5173   │  ◀─────────────────────────────  │  http://localhost:5001       │
└──────────────────────────┘    risco de abandono (rede        └──────────────────────────────┘
                                 neural)                          └─ Rede Neural (.keras / TensorFlow)
```

> **Por que a porta 5001?** No macOS a porta 5000 é ocupada pelo *AirPlay
> Receiver*, então a API roda na **5001** (configurável via env `PORT`).

## Estrutura do repositório

```
.
├── tb-predict/         # Frontend: React + Vite + TypeScript + TailwindCSS
└── nano_tuberculose/   # API: Flask + modelo de ML
    ├── app.py                 # endpoints /predict/neural, /health
    ├── model_service.py       # carrega e roda o modelo
    ├── baseline_pipeline_treino2.pkl              # pipeline de pré-processamento das variáveis
    ├── modelo_redeneural_tuberculose_vFinal_treino2.keras  # modelo da Rede Neural
    ├── test_api.py            # testes da API por linha de comando
    ├── Dockerfile / docker-compose.yml
    └── Trabalho_tuberculose_final.ipynb     # notebook de treino/análise
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
curl -s -X POST http://localhost:5001/predict/neural \
  -H "Content-Type: application/json" \
  -d '{
    "idade_anos": 35, "CS_SEXO": "M", "CS_GESTANT": "6", "CS_RACA": "1",
    "CS_ESCOL_N": "3", "SG_UF": "35", "TRATAMENTO": "1", "POP_LIBER": "2",
    "POP_RUA": "1", "POP_SAUDE": "2", "POP_IMIG": "2", "FORMA": "1",
    "AGRAVALCOO": "2", "AGRAVDIABE": "2", "AGRAVDOENC": "2", "AGRAVOUTRA": "2",
    "HIV": "1", "SG_UF_2": "35", "TRATSUP_AT": "1", "TRANSF": "2"
  }' | python3 -m json.tool
```

> Campos não informados podem ser enviados como string vazia (`""`); o modelo
> trata o valor como categoria desconhecida.

Resposta (resumida):

```json
{
  "prediction_label": "Abandono",
  "probability_abandono": 94.93,
  "recommendation": "Alerta de alto risco! Iniciar busca ativa ou suporte psicossocial."
}
```

## API

| Método | Rota              | Descrição                              |
|--------|-------------------|----------------------------------------|
| POST   | `/predict/neural` | Estima o risco de abandono (rede neural) |
| GET    | `/health`         | Status da API e do modelo carregado    |

Todos os campos do payload são enviados como **string**, exceto `idade_anos`
(número). Campos não informados vão como string vazia (`""`). Faixas de risco
usadas na recomendação: **<40%** baixo · **40–70%** moderado · **>70%** alto.

## Implantação no EasyPanel

Cada pasta é um **serviço** independente, com seu próprio `Dockerfile`. Crie
dois serviços do tipo **App** apontando para este mesmo repositório, mudando
apenas o *Build Context*:

### Serviço 1 — API (`nano_tuberculose`)

| Campo (EasyPanel)     | Valor                          |
|-----------------------|--------------------------------|
| Build Context / Path  | `nano_tuberculose`             |
| Dockerfile            | `Dockerfile`                   |
| Porta do domínio      | `5050`                         |

Os modelos `.pkl` e `.keras` já vão **embarcados na imagem** (sem necessidade de
volume). Variáveis de ambiente:

| Variável          | Padrão | Descrição                                  |
|-------------------|--------|--------------------------------------------|
| `PORT`            | `5050` | Porta em que o gunicorn escuta             |
| `WEB_CONCURRENCY` | `2`    | Nº de workers do gunicorn (memória ↑)      |

> O CORS já está liberado (`origins: *`), então o frontend pode chamar a API de
> outro domínio. Anote a **URL pública** desta API (ex.: `https://tb-api.seu-dominio.com`).

### Serviço 2 — Frontend (`tb-predict`)

| Campo (EasyPanel)     | Valor                          |
|-----------------------|--------------------------------|
| Build Context / Path  | `tb-predict`                   |
| Dockerfile            | `Dockerfile`                   |
| Porta do domínio      | `5051`                         |

Variáveis de ambiente:

| Variável       | Obrigatória | Exemplo / Padrão                          |
|----------------|-------------|-------------------------------------------|
| `VITE_API_URL` | sim         | `https://tb-api.seu-dominio.com/predict/neural` |
| `PORT`         | não         | `5051` (porta em que o nginx escuta)      |

`VITE_API_URL` é a URL **pública** da API (o navegador acessa a API diretamente,
então use o domínio público, **não** o nome interno do container). Ela é injetada
**em runtime** (via `config.js` gerado no boot), então basta alterar a env e
**reiniciar** o serviço — não precisa rebuildar.

> ⚠️ **Causa de "Not Found" / "502 Service is not reachable":** a porta do
> **domínio** de cada serviço no EasyPanel precisa ser **igual** à porta em que o
> container escuta (env `PORT`): **5050** para a API e **5051** para o front. Se
> não baterem, o proxy não alcança o container. Ambas as portas são controláveis
> pela env `PORT` — mude a env e a porta do domínio em conjunto.

## Stack

- **Frontend:** React 18, Vite 6, TypeScript, TailwindCSS 4 — servido por nginx
- **Backend:** Flask 3, flask-cors, scikit-learn, TensorFlow/Keras, pandas, joblib
- **Deploy:** Docker (multi-stage no front) / gunicorn / EasyPanel
