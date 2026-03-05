from typing import List, Dict, Any, Optional

class DataProcessor:
    """
    Processa os dados brutos do Cartola FC para o formato esperado pelo MathEngine.
    """
    
    def __init__(self):
        # Definição de pesos para os Scouts Dependendo do Perfil de Risco (1 a 10)
        # Ousadia 1 = Mais focado em regularidade (Modo Seguro)
        # Ousadia 10 = Mais focado em impacto (Modo Kamikaze)
        
        self.scout_values = {
            # Regularidade
            'DS': 1.2,  # Desarme
            'FC': -0.3, # Falta Cometida
            'FS': 0.5,  # Falta Sofrida
            'PI': -0.1, # Passe Incompleto
            'FD': 1.2,  # Finalização Defendida
            'FF': 0.8,  # Finalização para Fora
            'DE': 1.0,  # Defesa (Goleiro)
            'DP': 7.0,  # Defesa de Pênalti
            'GS': -1.0, # Gol Sofrido
            
            # Impacto
            'G': 8.0,   # Gol
            'A': 5.0,   # Assistência
            'SG': 5.0,  # Saldo de Gols (Defesa)
            'FT': 3.0,  # Finalização na Trave
            'CV': -3.0, # Cartão Vermelho
            'CA': -1.0, # Cartão Amarelo
            'PP': -4.0, # Pênalti Perdido
            'GC': -3.0, # Gol Contra
        }

    def _calculate_expected_points(self, player: Dict[str, Any], ousadia: int, matches: Optional[Dict[str, Any]] = None) -> float:
        """
        Calcula os 'pontos_esperados' misturando média do jogador com os scouts multiplicados pelo fator de Ousadia.
        Se faltar dados históricos densos, utiliza a média_num como base.
        """
        scouts = player.get('scout', {})
        jogos_num = max(player.get('jogos_num', 1), 1) # Evitar div/0
        
        # Média básica como fundação
        base_points = player.get('media_num', 0.0)
        
        # Avaliar Scouts de Regularidade (DS, FS, FF) divididos num de jogos
        reg_points = (
            scouts.get('DS', 0) * self.scout_values['DS'] +
            scouts.get('FS', 0) * self.scout_values['FS'] +
            scouts.get('FF', 0) * self.scout_values['FF'] +
            scouts.get('DE', 0) * self.scout_values['DE']
        ) / jogos_num
        
        # Avaliar Scouts de Impacto (G, A, SG, FT)
        imp_points = (
            scouts.get('G', 0) * self.scout_values['G'] +
            scouts.get('A', 0) * self.scout_values['A'] +
            scouts.get('SG', 0) * self.scout_values['SG'] +
            scouts.get('FT', 0) * self.scout_values['FT']
        ) / jogos_num
        
        # Normaliza a ousadia para fator entre 0.0 e 1.0 (0=Seguro, 1=Impacto)
        alpha = (ousadia - 1) / 9.0
        
        # Formula hibrida (base + mix) -> Ajuste fino será feito por MachineLearning (Backtesting) depois.
        # Por hora, aplicamos um sistema de heurística que recompensa o peso determinado.
        hybrid_projection = base_points * 0.4 + (reg_points * (1 - alpha) + imp_points * alpha) * 0.6
        
        # Context Factor (Mando de Campo, Dificuldade do Adversário)
        context_multiplier = 1.0 
        
        if matches and 'partidas' in matches:
            clube_id = player.get('clube_id')
            pos_id = player.get('posicao_id', 0)
            
            for part in matches['partidas']:
                if part.get('clube_casa_id') == clube_id:
                    adv_pos = part.get('clube_visitante_posicao', 10)
                    if adv_pos == 0: adv_pos = 10 # Em início de campeonato pode vir 0
                    
                    context_multiplier += 0.05 # Bônus de mandante
                    context_multiplier += (adv_pos - 10) * 0.005 # FDR Bonus (Adversário fraco)
                    
                    if pos_id in [1, 2, 3] and adv_pos > 10:
                        context_multiplier += 0.05 # Bônus de Clean Sheet
                    break
                    
                elif part.get('clube_visitante_id') == clube_id:
                    adv_pos = part.get('clube_casa_posicao', 10)
                    if adv_pos == 0: adv_pos = 10
                    
                    context_multiplier -= 0.05 # Pênalti de visitante
                    context_multiplier += (adv_pos - 10) * 0.005 # FDR Penalty (Adversário forte)
                    
                    if pos_id in [1, 2, 3] and adv_pos < 10:
                        context_multiplier -= 0.05 # Risco de perder SG
                    break
        
        if player.get('status_id') != 7: # 7: Provável
            # Penalidade rigorosa se não for provável
            hybrid_projection = -999.0
            
        return hybrid_projection * context_multiplier

    def _calculate_expected_valuation(self, player: Dict[str, Any]) -> float:
        """
        Calcula expectativa de valorização baseada na regra: 
        Preço atual * 0.4 - Média (Variável a cada ano, mas a grosso modo E[V] = f(Preco, Média anterior)).
        """
        # Regra empírica Cartola: para valorizar, a pessoa precisa fazer aprox (Preço atual * 0.45) pontos
        points_needed = player.get('preco_num', 0) * 0.45
        diff = player.get('media_num', 0) - points_needed 
        # Lógica simplificada de valorização (Modo Cartoleta)
        return diff

    def normalize_players(self, cartola_atletas: Dict[str, Any], ousadia: int = 5, objective: str = "mitagem", cartola_partidas: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Transforma o payload de `/atletas/mercado` para a estrutura requerida pelo Engine Matemático.
        """
        players = []
        raw_players = cartola_atletas.get('atletas', [])
        
        for rp in raw_players:
            # Posições (1:GOL, 2:LAT, 3:ZAG, 4:MEI, 5:ATA, 6:TEC)
            pos = rp.get('posicao_id')
            clube = rp.get('clube_id')
            preco = rp.get('preco_num', 0.0)
            
            # Identificar motor objetivo
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
                "status_id": rp.get('status_id')
            }
            # Filtrar jogadores inválidos? Deixar para MathEngine, pois tem restrição budget.
            # Aqui podemos cortar só quem tem pt esperado mt baixo pra otimizar o ILP solver (opcional).
            if p['status_id'] == 7: # Provável apenas
                players.append(p)
                
        return players

data_processor = DataProcessor()
