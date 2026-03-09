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

    def optimize_team(self, players: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Gera a escalação ideal (Titulares + Reservas) baseada em ILP.
        Restrição Banco: Preço Reserva <= Menor Preço Titular da mesma posição.
        """
        prob = pulp.LpProblem("Cartolitos_Optimiser", pulp.LpMaximize)

        # Variáveis de decisão
        # X: Titulares, Y: Reservas
        x_vars = pulp.LpVariable.dicts("Tit", [p['id'] for p in players], cat="Binary")
        y_vars = pulp.LpVariable.dicts("Res", [p['id'] for p in players], cat="Binary")

        # 1. Função Objetivo: Maximizar valor específico (Pode ser E[P] ou E[Val])
        prob += pulp.lpSum([
            float(p.get('solver_score', p.get('pontos_esperados', 0.0)) or 0.0) * x_vars[p['id']] + 
            (float(p.get('solver_score', p.get('pontos_esperados', 0.0)) or 0.0) * 0.1) * y_vars[p['id']] 
            for p in players
        ]), "Objetivo_Maximizacao"

        # 2. Restrição de Orçamento (Titulares + Banco)
        prob += pulp.lpSum([
            p['preco'] * x_vars[p['id']] + p['preco'] * y_vars[p['id']] 
            for p in players
        ]) <= self.budget, "Custo_Total"

        # 3. Exclusividade: Um jogador não pode ser titular e reserva ao mesmo tempo
        for p in players:
            prob += x_vars[p['id']] + y_vars[p['id']] <= 1, f"Exclusividade_{p['id']}"

        # 4. Formação: Limites para Titulares e Reservas
        req_positions = self.formations_map.get(self.formation)
        if not req_positions:
            raise ValueError(f"Formação inválida: {self.formation}")

        pos_id_map = {"gol": 1, "lat": 2, "zag": 3, "mei": 4, "ata": 5, "tec": 6}

        for pos_name, count in req_positions.items():
            pos_id = pos_id_map[pos_name]
            
            # Limite de Titulares
            prob += pulp.lpSum([x_vars[p['id']] for p in players if p['pos'] == pos_id]) == count, f"Titulares_{pos_name}"
            
            # Limite de Reservas
            # Regra: 1 reserva para posições usadas, 0 para posições não usadas ou técnico
            res_count = 1 if (count > 0 and pos_id != 6) else 0
            prob += pulp.lpSum([y_vars[p['id']] for p in players if p['pos'] == pos_id]) == res_count, f"Reservas_{pos_name}"

        # 5. Restrição "Reserva de Luxo" (Big-M Method)
        # Preço do(s) Reserva(s) <= Preço de qualquer Titular da mesma posição
        M = 200  # Valor maior que o preço máximo de qualquer jogador
        for pos_name, count in req_positions.items():
            pos_id = pos_id_map[pos_name]
            if count > 0 and pos_id != 6:
                pos_players = [p for p in players if p['pos'] == pos_id]
                # Para cada par (reserva j, titular i)
                for j in pos_players:
                    for i in pos_players:
                        if i['id'] != j['id']:
                            # Se j é reserva (y=1) e i é titular (x=1), Preço(j) <= Preço(i) -> Preço(j)*y(j) <= Preço(i) + M*(1 - x(i))
                            prob += j['preco'] * y_vars[j['id']] <= i['preco'] + M * (1 - x_vars[i['id']]), f"BancLuxo_{j['id']}_vs_{i['id']}"

        # Resolver
        prob.solve(pulp.PULP_CBC_CMD(msg=0))

        # Compilar resultado
        titulares = []
        reservas = []
        cost = 0
        expected_points = 0

        for p in players:
            if pulp.value(x_vars[p['id']]) == 1:
                titulares.append(p)
                cost += p['preco']
                expected_points += p['pontos_esperados']
            elif pulp.value(y_vars[p['id']]) == 1:
                reservas.append(p)
                cost += p['preco']

        # Extrair Capitão: Jogador de linha com a maior pontuação esperada entre titulares
        field_players = [p for p in titulares if p['pos'] != 6]
        captain = max(field_players, key=lambda x: x['pontos_esperados']) if field_players else None

        if captain:
            expected_points += captain['pontos_esperados'] # Dobra apenas a pontuação principal real

        return {
            "status": pulp.LpStatus[prob.status],
            "pontos_esperados": expected_points,
            "custo": cost,
            "formacao": self.formation,
            "capitao_id": captain['id'] if captain else None,
            "titulares": titulares,
            "reservas": reservas
        }
