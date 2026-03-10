import sys
import os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from app.api.cartola import optimize_real
import traceback

async def run():
    try:
        res = await optimize_real(budget=150.0, formation="4-3-3", ousadia=0, modo="mitagem")
        print("expected_points:", res["meta"]["total_expected_points"])
        for p in res["results"]["lineup"]:
            print(p["nome"], p["pos_nome"], p["pontos_esperados"], p["reason"])
    except Exception as e:
        traceback.print_exc()

asyncio.run(run())
