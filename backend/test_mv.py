import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # Check market status first
        r = await client.get("https://api.cartola.globo.com/mercado/status")
        print(f"Status do Mercado: {r.json().get('status_mercado')}")
        
        response = await client.get("https://api.cartola.globo.com/atletas/mercado")
        data = response.json()
        atletas = data.get("atletas", [])
        print(f"Total atletas: {len(atletas)}")
        for atleta in atletas[:5]:
            preco = atleta.get("preco_num", 0.0)
            pontos = atleta.get("pontos_num", 0.0)
            jogos = atleta.get("jogos_num", 0)
            mv_calc = (preco * 0.45) + (pontos * 0.1)
            print(f"{atleta['apelido']} - Preço: {preco} | Última Pont: {pontos} | MV Calculado: {mv_calc:.2f} | Jogos: {jogos}")

if __name__ == "__main__":
    asyncio.run(main())
