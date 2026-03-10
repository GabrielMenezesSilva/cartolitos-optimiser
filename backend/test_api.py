from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_optimize_endpoint():
    response = client.post(
        "/api/v1/solver/optimize",
        json={"budget": 120, "formation": "4-3-3", "objective": "mitagem", "players": [
            {"id": 1, "nome": "Player 1", "pos": 1, "preco": 10.0, "pontos_esperados": 5.0, "clube_id": 1},
            {"id": 2, "nome": "Player 2", "pos": 2, "preco": 8.0, "pontos_esperados": 3.0, "clube_id": 1},
            {"id": 3, "nome": "Player 3", "pos": 2, "preco": 8.0, "pontos_esperados": 3.0, "clube_id": 1},
            {"id": 4, "nome": "Player 4", "pos": 3, "preco": 9.0, "pontos_esperados": 4.0, "clube_id": 1},
            {"id": 5, "nome": "Player 5", "pos": 3, "preco": 9.0, "pontos_esperados": 4.0, "clube_id": 1},
            {"id": 6, "nome": "Player 6", "pos": 4, "preco": 11.0, "pontos_esperados": 6.0, "clube_id": 1},
            {"id": 7, "nome": "Player 7", "pos": 4, "preco": 11.0, "pontos_esperados": 6.0, "clube_id": 1},
            {"id": 8, "nome": "Player 8", "pos": 4, "preco": 11.0, "pontos_esperados": 6.0, "clube_id": 1},
            {"id": 9, "nome": "Player 9", "pos": 5, "preco": 14.0, "pontos_esperados": 8.0, "clube_id": 1},
            {"id": 10, "nome": "Player 10", "pos": 5, "preco": 14.0, "pontos_esperados": 8.0, "clube_id": 1},
            {"id": 11, "nome": "Player 11", "pos": 5, "preco": 14.0, "pontos_esperados": 8.0, "clube_id": 1},
            {"id": 12, "nome": "Coach", "pos": 6, "preco": 5.0, "pontos_esperados": 3.0, "clube_id": 1}
        ]}
    )
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Keys:", data.keys())
        if 'meta' in data:
            print("Meta:", data['meta'])
            print("Config:", data['config'])
            print(f"Players returned: {len(data['results']['lineup'])}")
        elif 'lineup' in data:
            print("WARNING: Old structure returned!")
    else:
        print("Error:", response.text)

if __name__ == "__main__":
    test_optimize_endpoint()
