from typing import List, Dict, Any, Optional
import pulp  # type: ignore
import copy


class MathEngine:
    def __init__(self, budget: float = 100.0, formation: str = "4-3-3", objective: str = "mitagem") -> None:
        self.budget: float = budget
        self.formation: str = formation
        self.objective: str = objective
        self.formations_map: Dict[str, Dict[str, int]] = {
            "3-4-3": {"gol": 1, "zag": 3, "lat": 0, "mei": 4, "ata": 3, "tec": 1},
            "3-5-2": {"gol": 1, "zag": 3, "lat": 0, "mei": 5, "ata": 2, "tec": 1},
            "4-3-3": {"gol": 1, "zag": 2, "lat": 2, "mei": 3, "ata": 3, "tec": 1},
            "4-4-2": {"gol": 1, "zag": 2, "lat": 2, "mei": 4, "ata": 2, "tec": 1},
            "4-5-1": {"gol": 1, "zag": 2, "lat": 2, "mei": 5, "ata": 1, "tec": 1},
            "5-3-2": {"gol": 1, "zag": 3, "lat": 2, "mei": 3, "ata": 2, "tec": 1},
            "5-4-1": {"gol": 1, "zag": 3, "lat": 2, "mei": 4, "ata": 1, "tec": 1},
        }
        self.pos_id_map = {"gol": 1, "lat": 2, "zag": 3, "mei": 4, "ata": 5, "tec": 6}
        self.pos_names = {1: "Goleiro", 2: "Lateral", 3: "Zagueiro", 4: "Meia", 5: "Atacante", 6: "Técnico"}

    def _build_and_solve(self, players: List[Dict[str, Any]], forbidden_sets: List[List[int]]) -> Optional[Dict[str, Any]]:
        """
        Builds and solves the ILP problem. Accepts a list of forbidden titular sets
        (as player ID lists) to force different solutions via no-good cuts.
        Returns None if no feasible solution exists.
        """
        req_positions = self.formations_map.get(self.formation)
        if not req_positions:
            raise ValueError(f"Formação inválida: {self.formation}")

        prob = pulp.LpProblem("Cartolitos_Optimiser", pulp.LpMaximize)

        x_vars = pulp.LpVariable.dicts("Tit", [p['id'] for p in players], cat="Binary")
        y_vars = pulp.LpVariable.dicts("Res", [p['id'] for p in players], cat="Binary")

        # Objective
        prob += pulp.lpSum([
            (float(p.get('solver_score', 0)) - (p.get('preco', 0) * 0.0001)) * x_vars[p['id']] +
            ((float(p.get('solver_score', 0)) * 0.1) - (p.get('preco', 0) * 0.0001)) * y_vars[p['id']]
            for p in players
        ]), "Objetivo_Maximizacao"

        # Budget
        prob += pulp.lpSum([
            p['preco'] * x_vars[p['id']] + p['preco'] * y_vars[p['id']]
            for p in players
        ]) <= self.budget, "Custo_Total"

        # Exclusivity
        for p in players:
            prob += x_vars[p['id']] + y_vars[p['id']] <= 1, f"Exclusividade_{p['id']}"

        # Formation constraints
        for pos_name, count in req_positions.items():
            pos_id = self.pos_id_map[pos_name]
            prob += pulp.lpSum([x_vars[p['id']] for p in players if p['pos'] == pos_id]) == count, f"Titulares_{pos_name}"
            res_count = 1 if (count > 0 and pos_id != 6) else 0
            prob += pulp.lpSum([y_vars[p['id']] for p in players if p['pos'] == pos_id]) == res_count, f"Reservas_{pos_name}"

        # Luxury bench constraint
        M = 200
        for pos_name, count in req_positions.items():
            pos_id = self.pos_id_map[pos_name]
            if count > 0 and pos_id != 6:
                pos_players = [p for p in players if p['pos'] == pos_id]
                for j in pos_players:
                    for i in pos_players:
                        if i['id'] != j['id']:
                            prob += j['preco'] * y_vars[j['id']] <= i['preco'] + M * (1 - x_vars[i['id']]), f"BancLuxo_{j['id']}_vs_{i['id']}"

        # No-good cuts: force at least 1 different titular from each previous solution
        for k, prev_set in enumerate(forbidden_sets):
            prev_vars = [x_vars[pid] for pid in prev_set if pid in x_vars]
            if prev_vars:
                n = len(prev_vars)
                # Make at least 1 player different (at least 1 previous player NOT selected)
                # => sum of previous titulars' x_vars <= n - 1
                prob += pulp.lpSum(prev_vars) <= n - 1, f"NoGoodCut_{k}"

        prob.solve(pulp.PULP_CBC_CMD(msg=0))

        if prob.status != 1:  # Not optimal
            return None

        # Compile result
        lineup = []
        cost = 0.0
        expected_points = 0.0

        titulares_info = [p for p in players if pulp.value(x_vars[p['id']]) == 1]
        field_players = [p for p in titulares_info if p['pos'] != 6]
        captain = max(field_players, key=lambda x: x.get('pontos_esperados', 0)) if field_players else None
        titular_ids = [p['id'] for p in titulares_info]

        for p in players:
            is_titular = pulp.value(x_vars[p['id']]) == 1
            is_reserva = pulp.value(y_vars[p['id']]) == 1
            is_captain = captain and captain['id'] == p['id'] and is_titular

            if is_titular or is_reserva:
                cost += p['preco']
                pts_esp = p.get('pontos_esperados', 0.0)

                if is_titular:
                    expected_points += pts_esp * 2 if is_captain else pts_esp

                meta_exp = p.get('metadata_explicativa', {}).copy()
                if is_captain:
                    meta_exp["capitao_motivo"] = "Escolhida pela inteligência como a opção com maior teto de pontos, ideal para dobrar a pontuação."
                if is_reserva:
                    meta_exp["reserva_motivo"] = "Reserva de luxo: opção mais barata que todos os titulares da posição, mas com alto Custo-Benefício."

                lineup.append({
                    "id": p['id'],
                    "nome": p['nome'],
                    "pos_id": p['pos'],
                    "pos_nome": self.pos_names.get(p['pos'], "Desconhecido"),
                    "preco": p['preco'],
                    "pontos_esperados": pts_esp,
                    "pontos_valorizacao": p.get('pontos_valorizacao', 0.0),
                    "status_id": p.get('status_id'),
                    "foto": p.get('foto'),
                    "clube_id": p.get('clube_id'),
                    "clube_slug": p.get('clube_slug', '??'),
                    "is_titular": is_titular,
                    "is_capitao": bool(is_captain),
                    "reason": p.get('reason', 'N/A'),
                    "perfil": p.get('perfil', 'Desconhecido'),
                    "consistencia": p.get('consistencia', 0.5),
                    "metadata_explicativa": meta_exp,
                })

        lineup_titulares = sorted([x for x in lineup if x['is_titular']], key=lambda x: x['pos_id'])
        lineup_reservas = sorted([x for x in lineup if not x['is_titular']], key=lambda x: x['pos_id'])
        final_lineup = lineup_titulares + lineup_reservas

        return {
            "meta": {
                "status": pulp.LpStatus[prob.status],
                "total_cost": round(cost, 2),
                "total_expected_points": round(expected_points, 2),
                "players_selected": len(final_lineup),
            },
            "config": {
                "budget": self.budget,
                "formation": self.formation,
                "objective": self.objective,
            },
            "results": {
                "lineup": final_lineup,
            },
            "_titular_ids": titular_ids,  # internal, removed before response
        }

    def optimize_team(self, players: List[Dict[str, Any]], num_lineups: int = 1) -> Dict[str, Any]:
        """
        Returns the single best lineup. Kept for backward compatibility.
        """
        result = self._build_and_solve(players, forbidden_sets=[])
        if result is None:
            raise ValueError("Não foi possível gerar uma escalação com os dados fornecidos.")
        result.pop("_titular_ids", None)
        return result

    def optimize_multiple(self, players: List[Dict[str, Any]], num_lineups: int = 3) -> List[Dict[str, Any]]:
        """
        Returns up to `num_lineups` distinct optimized lineups using no-good cuts.
        Each subsequent lineup must differ by at least 1 titular player.
        """
        lineups = []
        forbidden_sets: List[List[int]] = []

        for _ in range(num_lineups):
            result = self._build_and_solve(players, forbidden_sets=forbidden_sets)
            if result is None:
                break
            titular_ids = result.pop("_titular_ids", [])
            lineups.append(result)
            forbidden_sets.append(titular_ids)

        return lineups
