from typing import List, Dict, Any, Optional

class DataProcessor:
    """
    Processa os dados brutos do Cartola FC para o formato esperado pelo MathEngine.
    """
    
    def __init__(self):
        # Definição de pesos para os Scouts Dependendo do Perfil de Risco
        self.strategy_weights = {
            'SEGURO': {
                'DS': 1.5,
                'FC': -0.3,
                'FS': 1.2,
                'PI': -0.1,
                'FD': 1.2, 
                'FF': 0.8,
                'DE': 1.3,
                'DP': 7.0,
                'GS': -1.0,
                'G': 0.8,
                'A': 0.9,
                'SG': 1.1,
                'xG': 0.5,
                'xA': 0.5,
                'FT': 3.0,
                'CV': -3.0,
                'CA': -1.0,
                'PP': -4.0,
                'GC': -3.0,
            },
            'OUSADO': {
                'DS': 0.8,
                'FC': -0.3,
                'FS': 0.7,
                'PI': -0.1,
                'FD': 1.2,
                'FF': 0.8,
                'DE': 1.0,
                'DP': 7.0,
                'GS': -1.0,
                'G': 2.0,
                'A': 1.8,
                'SG': 1.4,
                'xG': 1.5,
                'xA': 1.5,
                'FT': 3.0,
                'CV': -3.0,
                'CA': -1.0,
                'PP': -4.0,
                'GC': -3.0,
            }
        }

    def _get_interpolated_weights(self, ousadia: int) -> Dict[str, float]:
        if ousadia <= 4:
            return self.strategy_weights['SEGURO']
        elif ousadia >= 7:
            return self.strategy_weights['OUSADO']
        else:
            # Interpolation for mid-range (5, 6)
            # 4 -> 0% ousado, 7 -> 100% ousado. 5 -> 33%, 6 -> 66%
            ratio = (ousadia - 4) / 3.0
            weights = {}
            for key in self.strategy_weights['SEGURO'].keys():
                w_seguro = self.strategy_weights['SEGURO'][key]
                w_ousado = self.strategy_weights['OUSADO'][key]
                weights[key] = w_seguro + (w_ousado - w_seguro) * ratio
            return weights

    def _calculate_expected_points(self, player: Dict[str, Any], ousadia: int, matches: Optional[Dict[str, Any]] = None) -> float:
        """
        Calcula os 'pontos_esperados' misturando média do jogador com os scouts multiplicados pelo fator de Ousadia dict.
        """
        scouts = player.get('scout', {})
        jogos_num = max(player.get('jogos_num', 1), 1) # Evitar div/0
        
        weights = self._get_interpolated_weights(ousadia)
        
        # Calculate points based on available scouts
        total_derived_points: float = 0.0
        for scout_key, scout_value in scouts.items():
            if scout_key in weights:
                total_derived_points += float(scout_value) * float(weights[scout_key])
                
        # Fake xG / xA processing for the example (as they don't natively come from simple Cartola API)
        total_derived_points += float(player.get('xG', 0)) * float(weights.get('xG', 1.0))
        total_derived_points += float(player.get('xA', 0)) * float(weights.get('xA', 1.0))
        
        # Average per game
        hybrid_projection = total_derived_points / jogos_num
        
        # Fallback to standard base points if history is too poor
        base_points = player.get('media_num', 0.0)
        if jogos_num < 3:
            hybrid_projection = (hybrid_projection + base_points * 2) / 3.0
        
        # Context Factor (Mando de Campo, Dificuldade do Adversário)
        context_multiplier: float = 1.0 
        
        if matches is not None and isinstance(matches, dict) and 'partidas' in matches:
            clube_id = player.get('clube_id')
            pos_id = int(player.get('posicao_id', 0))
            
            for part in matches['partidas']:
                is_home = part.get('clube_casa_id') == clube_id
                is_away = part.get('clube_visitante_id') == clube_id
                
                if is_home or is_away:
                    adv_pos_raw = part.get('clube_visitante_posicao' if is_home else 'clube_casa_posicao', 10)
                    adv_pos = int(adv_pos_raw) if adv_pos_raw else 10
                    if adv_pos == 0: adv_pos = 10 # Em início de campeonato pode vir 0
                    
                    # Regras do Notion:
                    # Fator Mandante: 1.15x
                    if is_home:
                        context_multiplier *= 1.15
                    
                    # Prob. SG > 60% (Proxy: Adversário fraco, Z4 ou quase) para Defesa
                    if pos_id in [1, 2, 3] and adv_pos >= 15:
                        context_multiplier *= 1.25
                        
                    # Adversário Z-4: 1.20x para Ataque/Meia
                    if pos_id in [4, 5] and adv_pos >= 17:
                        context_multiplier *= 1.20
                        
                    # Classico Regional: 0.9x (Proxy simplificado: times muito próximos na tabela em disputa direta)
                    my_pos = part.get('clube_casa_posicao' if is_home else 'clube_visitante_posicao', 10)
                    if abs(my_pos - adv_pos) <= 2 and my_pos < 10:
                        context_multiplier *= 0.90
                        
                    break
        
        if player.get('status_id') != 7: # 7: Provável
            hybrid_projection = -999.0
            
        return hybrid_projection * context_multiplier

    def _calculate_expected_valuation(self, player: Dict[str, Any]) -> float:
        """
        Calcula expectativa de valorização baseada na regra: 
        Preço atual * 0.45 - Média 
        """
        points_needed = player.get('preco_num', 0) * 0.45
        diff = player.get('media_num', 0) - points_needed 
        return diff

    def normalize_players(self, cartola_atletas: Dict[str, Any], ousadia: int = 5, objective: str = "mitagem", cartola_partidas: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Transforma o payload de `/atletas/mercado` para a estrutura requerida pelo Engine Matemático.
        """
        players = []
        raw_players = cartola_atletas.get('atletas', [])
        
        for rp in raw_players:
            pos = rp.get('posicao_id')
            clube = rp.get('clube_id')
            preco = rp.get('preco_num', 0.0)
            
            if objective == "mitagem":
                pts_esperados = self._calculate_expected_points(rp, ousadia, cartola_partidas)
            else:
                pts_esperados = self._calculate_expected_valuation(rp)
            
            p = {
                "id": rp.get('atleta_id'),
                "nome": rp.get('apelido'),
                "pos": pos,
                "preco": preco,
                "pontos_esperados": pts_esperados,
                "clube_id": clube,
                "status_id": rp.get('status_id'),
                "foto": rp.get('foto')  # Important for frontend UI
            }
            if p['status_id'] == 7: # Provável apenas
                players.append(p)
                
        return players

data_processor = DataProcessor()
