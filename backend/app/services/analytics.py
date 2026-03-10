import math
import csv
import io
from typing import List, Dict, Any, Optional

class DataProcessor:
    """
    Processa os dados brutos do Cartola FC para o formato esperado pelo MathEngine.
    Inclui cálculo de IES (Densidade por minuto jogado), Distribuição de Poisson para SG e MV (Mínimo para Valorizar).
    """
    
    def __init__(self) -> None:
        self.historical_stats: Dict[int, Dict[str, float]] = {}
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

    def ingest_historical_csv(self, csv_text: str) -> None:
        if not csv_text or not csv_text.strip(): return
        reader = csv.DictReader(io.StringIO(csv_text))
        for row in reader:
            try:
                atleta_id_str = row.get('atletas.atleta_id') or row.get('atleta_id')
                if not atleta_id_str: continue
                atleta_id = int(atleta_id_str)
                
                media_str = row.get('atletas.media_num') or row.get('media_num', '0')
                jogos_str = row.get('atletas.jogos_num') or row.get('jogos_num', '0')
                
                self.historical_stats[atleta_id] = {
                    'media_num': float(media_str) if media_str.replace('.','',1).isdigit() else 0.0,
                    'jogos_num': float(jogos_str) if jogos_str.isdigit() else 0.0
                }
            except Exception:
                pass

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
        Pesos Exatos: Gol (8.0), Assistência (5.0), Trave (3.0), Defendida (1.2), Fora (0.8), Desarme (1.2), SG (5.0)
        """
        g  = float(scouts.get('G', 0) or 0)
        a  = float(scouts.get('A', 0) or 0)
        ft = float(scouts.get('FT', 0) or 0)
        fd = float(scouts.get('FD', 0) or 0)
        ff = float(scouts.get('FF', 0) or 0)
        ds = float(scouts.get('DS', 0) or 0)
        sg = float(scouts.get('SG', 0) or 0)
        
        total_actions = (g * 8.0) + (a * 5.0) + (ft * 3.0) + (fd * 1.2) + (ff * 0.8) + (ds * 1.2) + (sg * 5.0)
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
                        
                        # Poisson Lambda (xGA - Expected Goals Against)
                        # We simulate "Média Cedida com Mando de Campo" logic for defenders
                        # The lower the xGA, the higher the probability of Clean Sheet (SG)
                        if adv_pos >= 15: # Weak opponent (relegation zone)
                            lambda_xGA = 0.5 if is_home else 0.8
                        elif adv_pos <= 6: # Strong opponent (top table)
                            lambda_xGA = 1.6 if is_home else 2.0
                        else: # Mid table
                            lambda_xGA = 1.0 if is_home else 1.3
                        break
        
        # Poisson Formula: P(x; μ) = (e^-μ) (μ^x) / x!
        # For x = 0 (zero goals conceded, SG), P(0; μ) = e^-μ
        prob_sg = math.exp(-lambda_xGA)
        sg_points = prob_sg * 5.0
        return float(sg_points), float(f"{prob_sg * 100:.1f}")

    def _calculate_expected_points(self, player: Dict[str, Any], ousadia: int, matches: Optional[Dict[str, Any]] = None) -> tuple[float, str]:
        """
        Calcula os 'pontos_esperados' usando IES, Poisson para SG e scouts normais.
        Retorna (Expected Points, Reason).
        """
        scouts: Dict[str, Any] = player.get('scout', {})
        if not isinstance(scouts, dict): scouts = {}
        
        jogos_num_raw = player.get('jogos_num', 1)
        jogos_num: int = int(jogos_num_raw) if jogos_num_raw is not None else 1
        jogos_num = max(jogos_num, 1)
        
        weights: Dict[str, float] = self._get_interpolated_weights(ousadia)
        reasons: List[str] = []
        
        total_derived: float = 0.0
        for sk, sv in scouts.items():
            k = str(sk)
            if k in weights and k != 'SG': 
                val = float(sv) if sv is not None else 0.0
                w = float(weights[k])
                total_derived = float(total_derived + (val * w))
                
        base_projection: float = float(total_derived / float(jogos_num))
        
        if jogos_num < 3:
            atleta_id_raw = player.get('atleta_id', 0)
            atleta_id = int(atleta_id_raw) if atleta_id_raw is not None else 0
            
            media_num: float = 0.0
            if atleta_id in self.historical_stats:
                media_num = float(self.historical_stats[atleta_id].get('media_num', 0.0))
            else:
                media_num_raw = player.get('media_num', 0.0)
                media_num = float(media_num_raw) if media_num_raw is not None else 0.0
                
            base_projection = float((base_projection + (media_num * 2.0)) / 3.0)
            
        ies: float = float(self._calculate_ies(scouts, jogos_num))
        base_projection = float(base_projection + (ies * 100.0))
        
        if ies > 0.05:
            reasons.append(f"IES Alto ({ies:.3f} ações/min)")
            
        context_multiplier: float = 1.0 
        if matches and isinstance(matches, dict) and 'partidas' in matches:
            partidas = matches.get('partidas', [])
            if isinstance(partidas, list):
                clube_id = player.get('clube_id')
                pos_id_raw = player.get('posicao_id', 0)
                pos_id = int(pos_id_raw) if pos_id_raw is not None else 0
                for part in partidas:
                    if not isinstance(part, dict): continue
                    is_home = part.get('clube_casa_id') == clube_id
                    is_away = part.get('clube_visitante_id') == clube_id
                    
                    if is_home or is_away:
                        adv_pos_raw = part.get('clube_visitante_posicao' if is_home else 'clube_casa_posicao', 10)
                        adv_pos = int(adv_pos_raw) if adv_pos_raw is not None else 10
                        
                        # "Média Cedida com Mando de Campo" por posição
                        if is_home:
                            # Mandante: Vantagem geral base
                            context_multiplier = float(context_multiplier * 1.10)
                            
                            # Cede para Atacantes e Meias (Se adv fraco)
                            if pos_id in [4, 5] and adv_pos >= 14:
                                context_multiplier = float(context_multiplier * 1.30)
                                reasons.append(f"Mandante vs Defesa frágil (Adversário Pos {adv_pos})")
                            elif pos_id in [4, 5] and adv_pos <= 6:
                                context_multiplier = float(context_multiplier * 0.95)
                                
                            # Cede para Defensores (Desarmes/Faltas)
                            if pos_id in [2, 3] and adv_pos <= 8:
                                context_multiplier = float(context_multiplier * 1.15)
                                reasons.append(f"Mandante sofrendo pressão (Alto volume de Desarmes esperados)")
                                
                        else: # Visitante
                            context_multiplier = float(context_multiplier * 0.90) # Desvantagem geral base
                            
                            if pos_id in [4, 5] and adv_pos >= 16:
                                context_multiplier = float(context_multiplier * 1.10)
                                reasons.append(f"Visitante, mas contra defesa super frágil (Z4)")
                            elif pos_id in [2, 3] and adv_pos <= 6:
                                # Visitante contra time forte sofre pressão, muita chance de desarme, mas alto risco de perder SG
                                context_multiplier = float(context_multiplier * 1.20)
                                reasons.append(f"Visitante sob forte pressão (Potencial IES Defensivo)")
                                
                        break

        # Weight SG according to Ousadia
        # Ousadia baixa (Seguro) = Confia mais em média e IES
        # Ousadia alta (Ousado) = Confia mais em SG e confrontos favoráveis
        if ousadia > 6:
            sg_points = sg_points * 1.2
            context_multiplier = context_multiplier * 1.1
            
        base_projection = float(base_projection + float(sg_points))
        
        final_ep: float = float(base_projection * context_multiplier)
        
        if int(player.get('status_id', 0) or 0) != 7: 
            final_ep = -999.0
            
        if not reasons:
            media = float(player.get('media_num', 0.0) or 0.0)
            reasons.append(f"Baseado na média histórica ({media:.1f} pts)")
            
        main_reason = reasons[0]
        return final_ep, main_reason

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
            
            # Usando import inline para evitar ciclo, ou importando no modulo
            from app.services.market import cartola_service
            mv = cartola_service.calculate_mv(preco, ultima_pt)
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
