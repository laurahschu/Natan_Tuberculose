# Relatório do Trabalho — Predição de Abandono do Tratamento de Tuberculose

**Disciplina:** MACHINE LEARNING E INTELIGÊNCIA ARTIFICIAL   
**Alunos(as):** Diego M. Sanchez, Iasmin Souto, Laura Schu, Nicolli Gomes, Ricardo Zanandrea e Wagner Schmitt   
**Data:** 21/06/2026

---

## 1. Resumo do projeto

Sistema acadêmico de **apoio à decisão clínica** que estima o risco de um paciente
**abandonar** o tratamento de tuberculose. A partir dos dados clínicos e
sociodemográficos do paciente, a aplicação devolve uma **probabilidade de
abandono** e uma **recomendação de conduta** (busca ativa, monitoramento, fluxo
normal).

O projeto integra três peças que se comunicam por HTTP:

1. **Modelos de Machine Learning** treinados sobre dados notificados de
   tuberculose (base SINAN);
2. uma **API REST** (Flask) que carrega esses modelos e responde a requisições de
   predição;
3. um **frontend web** (React) onde o profissional preenche um formulário e
   visualiza o resultado.

> ⚠️ Ferramenta acadêmica de apoio à decisão. **Não substitui a avaliação
> clínica de um profissional de saúde.**

---

## 2. Contexto e motivação

A tuberculose tem tratamento longo (geralmente 6 meses). O **abandono** do
tratamento é um problema de saúde pública grave: interrompe a cura, favorece a
transmissão e seleciona bactérias resistentes. Se for possível **identificar
precocemente** quais pacientes têm maior risco de abandonar, a equipe de saúde
pode priorizar ações de acompanhamento (ex.: Tratamento Diretamente Observado,
suporte psicossocial, busca ativa).

O objetivo do trabalho é justamente **prever esse risco** com base em
características já registradas na notificação do caso.

---

## 3. Arquitetura geral

```
┌──────────────────────────┐      POST /predict (JSON)       ┌──────────────────────────────┐
│  tb-predict (frontend)   │ ─────────────────────────────▶  │  nano_tuberculose (API)       │
│  React + Vite + TS       │                                 │  Flask + CORS                 │
│  navegador do usuário    │ ◀─────────────────────────────  │                               │
└──────────────────────────┘    resposta dos 2 modelos       └──────────────────────────────┘
                                                                 ├─ Regressão Logística (.pkl / scikit-learn)
                                                                 └─ Rede Neural (.keras / TensorFlow)
```

A aplicação roda **dois modelos diferentes** sobre os mesmos dados e devolve as
duas previsões. O frontend então **consolida** as duas em um único veredito (faz
a média das probabilidades e mostra se os modelos concordam).

### Estrutura do repositório

```
.
├── tb-predict/         # Frontend: React + Vite + TypeScript + TailwindCSS
└── nano_tuberculose/   # API + modelos de ML
    ├── app.py                                              # endpoints HTTP (Flask)
    ├── model_service.py                                    # carrega e executa os 2 modelos
    ├── baseline_pipeline_treino2.pkl                       # pipeline da Regressão Logística
    ├── modelo_redeneural_tuberculose_vFinal_treino2.keras  # modelo da Rede Neural
    ├── test_api.py                                         # testes automatizados da API
    ├── Trabalho_tuberculose_final.ipynb                    # notebook de treino/análise
    ├── requirements.txt
    └── Dockerfile / docker-compose.yml
```

---

## 4. Os dados e as variáveis (features)

Os modelos foram treinados a partir de um conjunto de dados de notificações de
tuberculose (`treino.csv`, derivado da base **SINAN** do Ministério da Saúde). O
**alvo** (variável a ser prevista) é binário:

| Valor | Significado |
|-------|-------------|
| `0`   | Não abandono |
| `1`   | Abandono do tratamento |

A predição usa **20 variáveis preditoras**. Quase todas são códigos categóricos
(enviados como texto); apenas `idade_anos` é numérica:

| Grupo | Campo | Descrição |
|-------|-------|-----------|
| **Demográfico** | `idade_anos` | Idade em anos |
| | `CS_SEXO` | Sexo (M/F) |
| | `CS_GESTANT` | Gestação (trimestre / não se aplica) |
| | `CS_RACA` | Raça / cor |
| | `CS_ESCOL_N` | Escolaridade |
| **Localização** | `SG_UF` | UF de notificação (código IBGE) |
| | `SG_UF_2` | UF de residência |
| **Clínico** | `TRATAMENTO` | Tipo de entrada (caso novo, recidiva, reingresso…) |
| | `FORMA` | Forma clínica (pulmonar / extrapulmonar) |
| | `HIV` | Resultado do exame de HIV |
| **Populações especiais** | `POP_LIBER` | Privado de liberdade |
| | `POP_RUA` | Situação de rua |
| | `POP_SAUDE` | Profissional de saúde |
| | `POP_IMIG` | Imigrante |
| **Agravos / comorbidades** | `AGRAVALCOO` | Alcoolismo |
| | `AGRAVDIABE` | Diabetes |
| | `AGRAVDOENC` | Doença mental |
| | `AGRAVOUTRA` | Outro agravo |
| **Acompanhamento** | `TRATSUP_AT` | Tratamento Diretamente Observado (TDO) |
| | `TRANSF` | Caso de transferência |

Variáveis como **situação de rua, alcoolismo, escolaridade baixa e ausência de
TDO** estão entre os fatores classicamente associados ao abandono — o que dá
sentido clínico ao modelo.

---

## 5. Os modelos de Machine Learning

Foram treinados **dois modelos** que compartilham o **mesmo pré-processamento**
(codificação das variáveis categóricas). Esse pré-processamento (`preprocessor`)
fica embutido dentro do pipeline da regressão logística e é **reaproveitado**
pela rede neural — garantindo que ambos vejam os dados no mesmo formato.

### 5.1 Regressão Logística (modelo baseline)

- Implementada com **scikit-learn**, salva como `baseline_pipeline_treino2.pkl`.
- Pipeline completo: `pré-processamento → regressão logística`.
- Serve de **linha de base** (baseline) simples e interpretável.

**Desempenho (relatório de classificação, conjunto de teste — 631 casos):**

| Classe | Precisão | Recall | F1 |
|--------|----------|--------|-----|
| 0 — Não abandono | 0,69 | 0,91 | 0,78 |
| 1 — Abandono | 0,80 | 0,48 | 0,60 |
| **Acurácia global** | | | **0,72** |

**Leitura clínica:** o modelo é muito bom em identificar quem **vai se manter no tratamento**
(recall 0,91). Para **abandono**, quando ele aponta risco ele costuma acertar
(precisão 0,80), mas ainda **deixa escapar** parte dos casos reais de abandono
(recall 0,48). Esse é o ponto que motivou treinar também a rede neural.

### 5.2 Rede Neural (Keras / TensorFlow)

Salva como `modelo_redeneural_tuberculose_vFinal_treino2.keras`. Arquitetura sequencial
densa, com regularização para evitar _overfitting_:

```
Entrada (nº de features após pré-processamento)
 → Dense(256) + BatchNorm + ReLU + Dropout(0.3)
 → Dense(128) + BatchNorm + ReLU + Dropout(0.2)
 → Dense(64)  + BatchNorm + ReLU + Dropout(0.1)
 → Dense(32)  + BatchNorm + ReLU
 → Dense(1, sigmoid)        # saída: probabilidade de abandono (0 a 1)
```

- **Otimizador:** Adam (learning rate 0,01)
- **Função de perda:** `binary_crossentropy`
- **Métrica de treino:** AUC
- **Regularização:** L2 nas camadas densas, `Dropout` e `BatchNormalization`
- **Balanceamento:** uso de `class_weight` para compensar que há mais casos de
  não abandono do que de abandono na base.

| Classe | Precisão | Recall | F1 |
|--------|----------|--------|-----|
| 0 — Não abandono | 0,72 | 0,56 | 0,63 |
| 1 — Abandono | 0,82 | 0,90 | 0,86 |
| **Acurácia global** | | | **0,80** |  

A saída `sigmoid` produz um número entre 0 e 1 interpretado como
**probabilidade de abandono**; aplica-se o limiar de **0,5** para decidir a
classe (`> 0,5` → Abandono).

---

## 6. A API (backend Flask)

A API é o coração do sistema. Ela carrega os modelos **uma única vez** (lazy
loading com cache em memória) e expõe quatro rotas HTTP.

### 6.1 Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/predict` | Roda **os dois modelos** e devolve as duas previsões |
| `POST` | `/predict/logistic` | Apenas a Regressão Logística |
| `POST` | `/predict/neural` | Apenas a Rede Neural |
| `GET`  | `/health` | Status da API e se os modelos foram carregados |

### 6.2 Fluxo de uma requisição `/predict`

1. **Validação do corpo** — verifica se é JSON e se é um objeto.
2. **Validação dos campos** — confere se as 20 variáveis preditoras estão
   presentes; se faltar alguma, devolve **HTTP 400** listando os campos ausentes.
3. **Predição** — monta um `DataFrame` de uma linha e roda os modelos:
   - regressão logística → `predict_proba`
   - rede neural → `preprocessor.transform` + `model.predict`
4. **Recomendação** — converte a probabilidade em uma conduta por faixa de risco.
5. Devolve o JSON com as duas previsões.

### 6.3 Faixas de risco e recomendação

| Probabilidade de abandono | Risco | Recomendação |
|---------------------------|-------|--------------|
| `< 40%` | Baixo | Seguir o fluxo normal de acompanhamento |
| `40% – 70%` | Moderado | Monitoramento mais frequente, reforço da adesão |
| `> 70%` | Alto | Busca ativa e suporte psicossocial, acompanhamento próximo |

### 6.4 Exemplo de requisição e resposta

**Requisição:**

```bash
curl -s -X POST http://localhost:5001/predict \
  -H "Content-Type: application/json" \
  -d '{
    "idade_anos": 35, "CS_SEXO": "M", "CS_GESTANT": "6", "CS_RACA": "1",
    "CS_ESCOL_N": "3", "SG_UF": "35", "TRATAMENTO": "1", "POP_LIBER": "2",
    "POP_RUA": "1", "POP_SAUDE": "2", "POP_IMIG": "2", "FORMA": "1",
    "AGRAVALCOO": "2", "AGRAVDIABE": "2", "AGRAVDOENC": "2", "AGRAVOUTRA": "2",
    "HIV": "1", "SG_UF_2": "35", "TRATSUP_AT": "1", "TRANSF": "2"
  }'
```

**Resposta (resumida):**

```json
{
  "logistic_regression": {
    "prediction_label": "Abandono",
    "probability_abandono": 59.59,
    "probability_cura": 40.41,
    "recommendation": "Risco moderado. Monitoramento mais frequente recomendado."
  },
  "neural_network": {
    "prediction_label": "Abandono",
    "probability_abandono": 94.93,
    "probability_cura": 5.07,
    "recommendation": "Alerta de alto risco! Iniciar busca ativa ou suporte psicossocial."
  }
}
```

---

## 7. O frontend (interface web)

Aplicação **React + TypeScript + Vite + TailwindCSS**. Principais
responsabilidades:

- **Formulário guiado** (`formConfig.ts`): apresenta as 20 variáveis organizadas
  em seções (demográficos, localização, clínico, populações especiais, agravos,
  acompanhamento), com rótulos legíveis e listas suspensas — o usuário não
  precisa conhecer os códigos numéricos da base.
- **Envio para a API** (`api.ts`): faz o `POST /predict` com os dados do
  formulário.
- **Consolidação do resultado** (`risk.ts`): como há duas previsões, o front
  calcula a **média das probabilidades**, define a faixa de risco (mesmas faixas
  da API) e indica se os dois modelos **concordam** no desfecho.
- **Exibição** (`ResultCard`, `GaugeBar`, `ClinicalVerdict`): mostra o veredito
  clínico em linguagem comum, sem jargão de ML, com indicador visual de risco.

---

## 8. Testes

O arquivo `test_api.py` executa uma bateria de **5 testes** contra a API em
execução:

1. `GET /health` — API no ar e modelos carregados;
2. `POST /predict/logistic` — predição da regressão logística;
3. `POST /predict/neural` — predição da rede neural;
4. `POST /predict` — os dois modelos juntos;
5. `POST /predict` com campos faltando — deve retornar **HTTP 400**.

Cada teste valida o código de status, a presença das chaves esperadas e a
consistência (ex.: as probabilidades de não abandono e abandono somam ~100%).

```bash
python test_api.py                       # testa localhost:5001
python test_api.py --url http://host:porta
```

---

## 9. Como executar

São dois serviços. A API pode subir via Docker (mais simples) ou localmente.

### API (backend)

```bash
cd nano_tuberculose
# Opção A — Docker
docker compose up --build
# Opção B — local (requer Python 3.12; TensorFlow ainda não suporta 3.13+)
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py            # http://localhost:5001
```

Verificação: `curl http://localhost:5001/health`

> **Por que a porta 5001?** No macOS a porta 5000 é ocupada pelo *AirPlay
> Receiver*, então a API roda na 5001 (configurável via variável `PORT`).

### Frontend

```bash
cd tb-predict
npm install
npm run dev              # http://localhost:5173
```

---

## 10. Stack tecnológica

| Camada | Tecnologias |
|--------|-------------|
| **Frontend** | React 18, Vite 6, TypeScript, TailwindCSS 4 (servido por nginx em produção) |
| **Backend** | Flask 3, flask-cors, gunicorn |
| **Machine Learning** | scikit-learn 1.6, TensorFlow/Keras 2.20, pandas, numpy, joblib |
| **Deploy** | Docker / docker-compose / EasyPanel |

---

## 11. Limitações e trabalhos futuros

- **Recall de abandono** ainda é o ponto fraco (a regressão logística detecta
  ~48% dos abandonos reais). Caminhos: ajustar o limiar de decisão, técnicas de
  balanceamento (ex.: SMOTE), ou ajuste fino de hiperparâmetros.
- **Qualidade dos dados:** muitos campos da base aceitam "Ignorado", o que reduz
  o sinal disponível.
- **Validação externa:** o modelo foi avaliado em um split de teste; idealmente
  deveria ser validado em dados de outra fonte/período.
- **Não é dispositivo clínico:** trata-se de um exercício acadêmico de apoio à
  decisão — não substitui a avaliação profissional.

---

## 12. Roteiro sugerido para a apresentação

1. **Problema** — abandono do tratamento de TB e por que prevê-lo importa (slide
   de contexto, seção 2).
2. **Dados** — de onde vêm e quais variáveis usamos (seção 4).
3. **Modelos** — baseline (regressão logística) × rede neural; por que dois
   (seção 5).
4. **Resultados** — tabela de métricas e leitura clínica (seção 5.1).
5. **Demonstração ao vivo** — subir a API, abrir o frontend, preencher um caso
   de alto risco e mostrar o veredito.
6. **Arquitetura** — frontend → API → modelos (seção 3).
7. **Limitações e próximos passos** (seção 11).
```
