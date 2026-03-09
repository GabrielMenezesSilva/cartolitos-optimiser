import math
from typing import List, Dict, Any, Optional

class DataProcessor:
    """
    Processa os dados brutos do Cartola FC para o formato esperado pelo MathEngine.
    Inclui cálculo de IES (Densidade por minuto jogado), Distribuição de Poisson para SG e MV (Mínimo para Valorizar).
    """
    
    def __init__(self) -> None:
        # Definição de pesos originais híbridos (Média + IES/Poisson vão incrementar isso)
        self.strategy_weights = {
            'SEGURO': {
                'DS': 1.5, 'FC': -0.3, 'FS': 1.2, 'PI': -0.1, 'FD': 1.2, 
                'FF': 0.8, 'DE': 1.3, 'DP': 7.0, 'GS': -1.0, 'G': 0.8,
                'A': 0.9, 'SG': 1.1, 'xG': 0.5, 'xA': 0.5, 'FT': 3.0,
                'CV': -3.0, 'CA': -1.0, 'PP': -4.0, 'GC': -3.0,
            },
            'OUSADO': {
                'DS': 0.8, 'FC': -0.3, 'FS': 0.7, 'PI': -0.1, 'FD': 1.2,
                'FF': 0.8, 'DE': 1.0, 'DP': 7.0, 'GS': -1.0, 'G': 2.0,
                'A': 1.8, 'SG': 1.4, 'xG': 1.5, 'xA': 1.5, 'FT': 3.0,
                'CV': -3.0, 'CA': -1.0, 'PP': -4.0, 'GC': -3.0,
            }
        }

    def _get_interpolated_weights(self, ousadia: int) -> Dict[str, float]:
        if ousadia <= 4: return self.strategy_weights['SEGURO']
        elif ousadia >= 7: return self.strategy_weights['OUSADO']
        
        ratio = (ousadia - 4) / 3.0
        weights: Dict[str, float] = {}
        for key in self.strategy_weights['SEGURO'].keys():
            w_seguro = self.strategy_weights['SEGURO'][key]
            w_ousado = self.strategy_weights['OUSADO'][key]
            weights[key] = w_seguro + (w_ousado - w_seguro) * ratio
        return weights

    def _calculate_ies(self, scouts: Dict[str, Any], jogos_num: int) -> float:
        """
        Calcula o IES (Índice de Eficiência de Scout): Densidade por minuto jogado.
        Pesos: DS(1.2), FD(1.2), FF(0.8), FS(0.5), PS(1.0)
        """
        ds = float(scouts.get('DS', 0) or 0)
        fd = float(scouts.get('FD', 0) or 0)
        ff = float(scouts.get('FF', 0) or 0)
        fs = float(scouts.get('FS', 0) or 0)
        ps = float(scouts.get('PS', 0) or 0)
        
        total_actions = (ds * 1.2) + (fd * 1.2) + (ff * 0.8) + (fs * 0.5) + (ps * 1.0)
        minutos_jogados = float(max(jogos_num * 90, 90)) # Aproximação
        
        return float(total_actions / minutos_jogados)

    def _calculate_poisson_sg(self, player: Dict[str, Any], matches: Optional[Dict[str, Any]] = None) -> tuple[float, float]:
        """
        Usa a Distribuição de Poisson para prever a probabilidade de SG (valendo +5.0 pontos).
        Retorna (Expected SG Points, Probability %).
        """
        pos_id = int(player.get('posicao_id', 0) or 0)
        if pos_id not in [1, 2, 3]:
            return 0.0, 0.0
            
        clube_id = player.get('clube_id')
        lambda_xGA = 1.1 
        
        if matches and isinstance(matches, dict) and 'partidas' in matches:
            partidas = matches.get('partidas', [])
            if isinstance(partidas, list):
                for part in partidas:
                    if not isinstance(part, dict): continue
                    is_home = part.get('clube_casa_id') == clube_id
                    is_away = part.get('clube_visitante_id') == clube_id
                    if is_home or is_away:
                        adv_pos = int(part.get('clube_visitante_posicao' if is_home else 'clube_casa_posicao', 10) or 10)
                        if adv_pos == 0: adv_pos = 10
                        
                        if adv_pos >= 15:
                            lambda_xGA = 0.6 if is_home else 0.85
                        elif adv_pos <= 6:
                            lambda_xGA = 1.4 if is_home else 1.7
                        else:
                            lambda_xGA = 0.9 if is_home else 1.2
                        break
        
        prob_sg = math.exp(-lambda_xGA)
        sg_points = prob_sg * 5.0
        return float(sg_points), float(f"{prob_sg * 100:.1f}")

    def _calculate_expected_points(self, player: Dict[str, Any], ousadia: int, matches: Optional[Dict[str, Any]] = None) -> tuple[float, str]:
        """
        Calcula os 'pontos_esperados' usando IES, Poisson para SG e scouts normais.
        Retorna (Expected Points, Reason).
        """
        scouts = player.get('scout', {})
        if not isinstance(scouts, dict): scouts = {}
        jogos_num = int(player.get('jogos_num', 1) or 1)
        jogos_num = max(jogos_num, 1)
        
        weights = self._get_interpolated_weights(ousadia)
        reasons: List[str] = []
        
        total_derived = 0.0
        for sk, sv in scouts.items():
            if sk in weights and sk != 'SG': 
                total_derived += float(sv or 0) * float(weights[sk])
                
        base_projection = float(total_derived / jogos_num)
        
        if jogos_num < 3:
            media_num = float(player.get('media_num', 0.0) or 0.0)
            base_projection = float((base_projection + media_num * 2) / 3.0)
            
        ies = self._calculate_ies(scouts, jogos_num)
        base_projection += (ies * 100) 
        
        if ies > 0.05:
            reasons.append(f"IES Alto ({ies:.3f} ações/min)")
            
        sg_points, sg_prob = self._calculate_poisson_sg(player, matches)
        base_projection += sg_points
        
        if sg_prob > 40.0:
            reasons.append(f"Prob. de SG alta (Poisson: {sg_prob}%)")
            
        context_multiplier = 1.0 
        if matches and isinstance(matches, dict) and 'partidas' in matches:
            partidas = matches.get('partidas', [])
            if isinstance(partidas, list):
                clube_id = player.get('clube_id')
                pos_id = int(player.get('posicao_id', 0) or 0)
                for part in partidas:
                    if not isinstance(part, dict): continue
                    is_home = part.get('clube_casa_id') == clube_id
                    is_away = part.get('clube_visitante_id') == clube_id
                    
                    if is_home or is_away:
                        if is_home: context_multiplier *= 1.15
                        adv_pos = int(part.get('clube_visitante_posicao' if is_home else 'clube_casa_posicao', 10) or 10)
                        if pos_id in [4, 5] and adv_pos >= 17:
                            context_multiplier *= 1.20
                            reasons.append(f"Enfrenta equipe no Z4 (Pos: {adv_pos})")
                        break

        final_ep = float(base_projection * context_multiplier)
        
        if int(player.get('status_id', 0) or 0) != 7: 
            final_ep = -999.0
            
        if not reasons:
            media = float(player.get('media_num', 0.0) or 0.0)
            reasons.append(f"Baseado na média histórica ({media:.1f} pts)")
            
        main_reason = reasons[0]
        return final_ep, main_reason

    def _calculate_mv(self, preco_atual: float, ultima_pontuacao: float) -> float:
        return float((preco_atual * 0.45) + (ultima_pontuacao * 0.1))

    def normalize_players(self, cartola_atletas: Dict[str, Any], ousadia: int = 5, objective: str = "mitagem", cartola_partidas: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        players: List[Dict[str, Any]] = []
        raw_players = cartola_atletas.get('atletas', [])
        if not isinstance(raw_players, list): return players
        
        for rp in raw_players:
            if not isinstance(rp, dict): continue
            pos = rp.get('posicao_id')
            clube = rp.get('clube_id')
            preco = float(rp.get('preco_num', 0.0) or 0.0)
            ultima_pt = float(rp.get('pontos_num', 0.0) or 0.0) 
            
            pts_esperados, reason = self._calculate_expected_points(rp, ousadia, cartola_partidas)
            
            mv = self._calculate_mv(preco, ultima_pt)
            pts_valorizacao = float(pts_esperados - mv)
            
            if objective == "valorizacao":
                solver_score = pts_valorizacao
                if pts_valorizacao > 0:
                    reason = f"Precisa de apenas {mv:.1f} pts para valorizar (EV Val: {pts_valorizacao:.1f})"
            else:
                solver_score = pts_esperados
            
            p = {
                "id": rp.get('atleta_id'),
                "nome": rp.get('apelido'),
                "pos": pos,
                "preco": preco,
                "pontos_esperados": pts_esperados,
                "pontos_valorizacao": pts_valorizacao,
                "solver_score": solver_score,
                "clube_id": clube,
                "status_id": rp.get('status_id'),
                "foto": rp.get('foto'),
                "reason": reason
            }
            if p['status_id'] == 7: 
                players.append(p)
                
        return players

data_processor = DataProcessor()
