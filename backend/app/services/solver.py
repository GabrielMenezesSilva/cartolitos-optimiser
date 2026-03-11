from typing import List, Dict, Any, Optional
import pulp # type: ignore

class MathEngine:
    def __init__(self, budget: float = 100.0, formation: str = "4-3-3", objective: str = "mitagem") -> None:
        self.budget: float = budget
        self.formation: str = formation
        self.objective: str = objective
        self.formations_map: Dict[str, Dict[str, int]] = {
            "4-3-3": {"gol": 1, "zag": 2, "lat": 2, "mei": 3, "ata": 3, "tec": 1},
            "4-4-2": {"gol": 1, "zag": 2, "lat": 2, "mei": 4, "ata": 2, "tec": 1},
            "3-5-2": {"gol": 1, "zag": 3, "lat": 0, "mei": 5, "ata": 2, "tec": 1},
        }
        self.pos_id_map = {"gol": 1, "lat": 2, "zag": 3, "mei": 4, "ata": 5, "tec": 6}
        self.pos_names = {1: "Goleiro", 2: "Lateral", 3: "Zagueiro", 4: "Meia", 5: "Atacante", 6: "Técnico"}

    def optimize_team(self, players: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Gera a escalação ideal (Titulares + Reservas) baseada em ILP.
        Retorna json formatado com meta, config, e results.
        """
        req_positions = self.formations_map.get(self.formation)
        if not req_positions:
            raise ValueError(f"Formação inválida: {self.formation}")

        prob = pulp.LpProblem("Cartolitos_Optimiser", pulp.LpMaximize)

        x_vars = pulp.LpVariable.dicts("Tit", [p['id'] for p in players], cat="Binary")
        y_vars = pulp.LpVariable.dicts("Res", [p['id'] for p in players], cat="Binary")

        # Função Objetivo: Max Z = Soma(Pontos_Esperados_i * x_i) 
        # Critério de Desempate: Priorizar menor preço subtraindo (0.0001 * Preco)
        prob += pulp.lpSum([
            (float(p.get('solver_score', 0)) - (p.get('preco', 0) * 0.0001)) * x_vars[p['id']] + 
            ((float(p.get('solver_score', 0)) * 0.1) - (p.get('preco', 0) * 0.0001)) * y_vars[p['id']]
            for p in players
        ]), "Objetivo_Maximizacao"

        # Restrição de Orçamento (Titulares + Banco)
        prob += pulp.lpSum([
            p['preco'] * x_vars[p['id']] + p['preco'] * y_vars[p['id']] 
            for p in players
        ]) <= self.budget, "Custo_Total"

        # Exclusividade
        for p in players:
            prob += x_vars[p['id']] + y_vars[p['id']] <= 1, f"Exclusividade_{p['id']}"

        # Formação: Limites para Titulares e Reservas
        for pos_name, count in req_positions.items():
            pos_id = self.pos_id_map[pos_name]
            
            prob += pulp.lpSum([x_vars[p['id']] for p in players if p['pos'] == pos_id]) == count, f"Titulares_{pos_name}"
            
            res_count = 1 if (count > 0 and pos_id != 6) else 0
            prob += pulp.lpSum([y_vars[p['id']] for p in players if p['pos'] == pos_id]) == res_count, f"Reservas_{pos_name}"

        # Restrição "Reserva de Luxo" (Big-M Method): Preço Reserva <= Preço Titular mais barato da mesma posição
        M = 200  
        for pos_name, count in req_positions.items():
            pos_id = self.pos_id_map[pos_name]
            if count > 0 and pos_id != 6:
                pos_players = [p for p in players if p['pos'] == pos_id]
                for j in pos_players:
                    for i in pos_players:
                        if i['id'] != j['id']:
                            prob += j['preco'] * y_vars[j['id']] <= i['preco'] + M * (1 - x_vars[i['id']]), f"BancLuxo_{j['id']}_vs_{i['id']}"

        prob.solve(pulp.PULP_CBC_CMD(msg=0))

        # Compilar resultado
        lineup = []
        cost = 0.0
        expected_points = 0.0

        # Separar capitão
        titulares_info = [p for p in players if pulp.value(x_vars[p['id']]) == 1]
        field_players = [p for p in titulares_info if p['pos'] != 6]
        captain = max(field_players, key=lambda x: x.get('pontos_esperados', 0)) if field_players else None

        for p in players:
            is_titular = pulp.value(x_vars[p['id']]) == 1
            is_reserva = pulp.value(y_vars[p['id']]) == 1
            is_captain = captain and captain['id'] == p['id'] and is_titular

            if is_titular or is_reserva:
                cost += p['preco']
                pts_esp = p.get('pontos_esperados', 0.0)
                
                if is_titular:
                    expected_points += pts_esp * 2 if is_captain else pts_esp

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
                })

        # Sort lineup for better presentation: Goalkeeper, Defenders, Midfielders, Attackers, Coach, Subs
        lineup_titulares = sorted([x for x in lineup if x['is_titular']], key=lambda x: x['pos_id'])
        lineup_reservas = sorted([x for x in lineup if not x['is_titular']], key=lambda x: x['pos_id'])
        
        final_lineup = lineup_titulares + lineup_reservas

        # Construir JSON Estruturado
        response = {
            "meta": {
                "status": pulp.LpStatus[prob.status],
                "total_cost": round(cost, 2),
                "total_expected_points": round(expected_points, 2),
                "players_selected": len(final_lineup)
            },
            "config": {
                "budget": self.budget,
                "formation": self.formation,
                "objective": self.objective
            },
            "results": {
                "lineup": final_lineup
            }
        }
        return response
