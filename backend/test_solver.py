import requests
import json

url = "http://127.0.0.1:8000/api/v1/solver/optimize"

players = [
    {"id": 1, "nome": "Goleiro A", "pos": 1, "preco": 10.0, "pontos_esperados": 5.0, "clube_id": 1},
    {"id": 2, "nome": "Goleiro B", "pos": 1, "preco": 5.0, "pontos_esperados": 3.0, "clube_id": 2},
    {"id": 3, "nome": "Zagueiro A", "pos": 3, "preco": 8.0, "pontos_esperados": 4.0, "clube_id": 3},
    {"id": 4, "nome": "Zagueiro B", "pos": 3, "preco": 9.0, "pontos_esperados": 6.0, "clube_id": 1},
    {"id": 5, "nome": "Zagueiro C", "pos": 3, "preco": 4.0, "pontos_esperados": 2.0, "clube_id": 4},
    {"id": 6, "nome": "Lateral A", "pos": 2, "preco": 12.0, "pontos_esperados": 7.0, "clube_id": 2},
    {"id": 7, "nome": "Lateral B", "pos": 2, "preco": 11.0, "pontos_esperados": 6.5, "clube_id": 3},
    {"id": 8, "nome": "Lateral C", "pos": 2, "preco": 6.0, "pontos_esperados": 4.5, "clube_id": 5},
    {"id": 9, "nome": "Meia A", "pos": 4, "preco": 15.0, "pontos_esperados": 8.0, "clube_id": 1},
    {"id": 10, "nome": "Meia B", "pos": 4, "preco": 14.0, "pontos_esperados": 7.5, "clube_id": 4},
    {"id": 11, "nome": "Meia C", "pos": 4, "preco": 13.0, "pontos_esperados": 7.0, "clube_id": 5},
    {"id": 12, "nome": "Meia D", "pos": 4, "preco": 7.0, "pontos_esperados": 5.0, "clube_id": 6},
    {"id": 13, "nome": "Atacante A", "pos": 5, "preco": 20.0, "pontos_esperados": 12.0, "clube_id": 2},
    {"id": 14, "nome": "Atacante B", "pos": 5, "preco": 18.0, "pontos_esperados": 10.0, "clube_id": 3},
    {"id": 15, "nome": "Atacante C", "pos": 5, "preco": 19.0, "pontos_esperados": 11.0, "clube_id": 1},
    {"id": 16, "nome": "Atacante D", "pos": 5, "preco": 9.0, "pontos_esperados": 6.0, "clube_id": 6},
    {"id": 17, "nome": "Tecnico A", "pos": 6, "preco": 10.0, "pontos_esperados": 5.0, "clube_id": 1},
    {"id": 18, "nome": "Tecnico B", "pos": 6, "preco": 8.0, "pontos_esperados": 4.0, "clube_id": 2},
]

payload = {
    "budget": 120.0,
    "formation": "4-3-3",
    "players": players
}

response = requests.post(url, json=payload)
print("Status Code:", response.status_code)
try:
    print("Response:", json.dumps(response.json(), indent=2))
except Exception as e:
    print("Response text:", response.text)
