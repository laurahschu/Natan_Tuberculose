# Exemplo

```
~ 死 curl -s -X POST http://localhost:5001/predict \
  -H "Content-Type: application/json" \
  -d '{
    "idade_anos": 35,
    "CS_SEXO": "M",
    "CS_GESTANT": "6",
    "CS_RACA": "1",
    "CS_ESCOL_N": "3",
    "SG_UF": "35",
    "TRATAMENTO": "1",
    "POP_LIBER": "2",
    "POP_RUA": "1",
    "POP_SAUDE": "2",
    "POP_IMIG": "2",
    "FORMA": "1",
    "AGRAVALCOO": "2",
    "AGRAVDIABE": "2",
    "AGRAVDOENC": "2",
    "AGRAVOUTRA": "2",
    "HIV": "1",
    "SG_UF_2": "35",
    "TRATSUP_AT": "1",
    "TRANSF": "2"
  }' | python3 -m json.tool
{
    "logistic_regression": {
        "model": "logistic_regression",
        "prediction": 1,
        "prediction_label": "Abandono",
        "probability_abandono": 59.59,
        "probability_nao_abandono": 40.41,
        "recommendation": "Risco moderado. Monitoramento mais frequente recomendado."
    },
    "neural_network": {
        "model": "neural_network",
        "prediction": 1,
        "prediction_label": "Abandono",
        "probability_abandono": 94.93,
        "probability_nao_abandono": 5.07,
        "recommendation": "Alerta de alto risco! Iniciar busca ativa ou suporte psicossocial."
    }
}

```
