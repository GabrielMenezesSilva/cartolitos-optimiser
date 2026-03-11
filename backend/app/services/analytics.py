"""
analytics.py — Motor de Inteligência do Cartolitos Optimiser
Baseado na referência técnica do projeto caRtola (Henrique Gomide & Arnaldo Gualberto).

MÓDULOS IMPLEMENTADOS:
1. Regressão de Poisson com λ real (histórico de gols por time, casa/fora)
2. Média Cedida por Posição com mando de campo (feature de dificuldade real)
3. Cadeias de Markov para análise de consistência (filtrar jogadores inconsistentes)
4. Affinity Propagation para clustering de perfil técnico (finalizadores vs garçons etc.)
5. Random Forest como modelo preditivo treinado com as features anteriores
6. IES (Índice de Eficiência de Scout) — densidade por minuto
"""

import math
import csv
import io
import logging
import warnings
from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# 1. CONSTANTES DE PESOS DE SCOUT
# ──────────────────────────────────────────────────────────────
SCOUT_WEIGHTS: Dict[str, float] = {
    'DS': 1.2, 'FC': -0.3, 'FS': 1.0, 'PI': -0.1, 'FD': 1.2,
    'FF': 0.8, 'DE': 1.2, 'DP': 7.0, 'GS': -1.0, 'G': 1.5,
    'A': 1.4, 'SG': 1.2, 'xG': 1.0, 'xA': 1.0, 'FT': 3.0,
    'CV': -3.0, 'CA': -1.0, 'PP': -4.0, 'GC': -3.0,
}

# Mapeamento de posicao_id → nome legível
POS_NAMES = {1: "Goleiro", 2: "Lateral", 3: "Zagueiro", 4: "Meia", 5: "Atacante", 6: "Técnico"}

# Posições defensivas para análise de SG
DEFENSIVE_POSITIONS = {1, 2, 3}

# ──────────────────────────────────────────────────────────────
# CONSTANTES DE DOMÍNIO
# ──────────────────────────────────────────────────────────────
ESTADOS_CLUBES = {
    2305: 'SP', 262: 'RJ', 263: 'RJ', 264: 'SP', 265: 'BA', 
    266: 'RJ', 267: 'RJ', 275: 'SP', 276: 'SP', 277: 'SP', 
    280: 'SP', 282: 'MG', 283: 'MG', 284: 'RS', 285: 'RS', 
    287: 'BA', 293: 'PR', 294: 'PR', 315: 'SC', 364: 'PA'
}

def get_tier(posicao: int) -> int:
    """Classifica a força do time em Tiers (1=Elite, 5=Rebaixamento)."""
    if posicao <= 4: return 1
    if posicao <= 8: return 2
    if posicao <= 12: return 3
    if posicao <= 16: return 4
    return 5



# ──────────────────────────────────────────────────────────────────────────────
# 2. MÓDULO: REGRESSÃO DE POISSON REAL (λ baseado em histórico de gols)
# Referência PDF §1: "Regressão de Poisson para modelar a expectativa de gols (λ)
# de cada equipe, ajustado pelo mando de campo"
# ──────────────────────────────────────────────────────────────────────────────
class PoissonModel:
    """
    Modela a expectativa de gols (λ) por equipe usando histórico real de partidas.
    Diferencia desempenho em casa (home) e fora (away).
    """

    def __init__(self) -> None:
        # {clube_id: {'home_scored': [], 'home_conceded': [], 'away_scored': [], 'away_conceded': []}}
        self._goals_data: Dict[int, Dict[str, List[float]]] = defaultdict(
            lambda: {'home_scored': [], 'home_conceded': [], 'away_scored': [], 'away_conceded': []}
        )
        self._is_fitted = False

    def ingest_match_result(self, home_id: int, away_id: int, home_goals: int, away_goals: int) -> None:
        """Ingere resultado de uma partida no histórico de gols."""
        self._goals_data[home_id]['home_scored'].append(float(home_goals))
        self._goals_data[home_id]['home_conceded'].append(float(away_goals))
        self._goals_data[away_id]['away_scored'].append(float(home_goals))  # inversed — away conceded
        self._goals_data[away_id]['away_conceded'].append(float(home_goals))
        self._is_fitted = True

    def ingest_from_csv_rows(self, rows: List[Dict[str, str]]) -> None:
        """
        Tenta extrair informações de gols dos CSVs do caRtola.
        O CSV histórico não tem placar direto, mas tem GS (gols sofridos) nos scouts.
        Estimamos λ a partir das médias dos scouts de GS por clube.
        """
        # Acumular GS (gols sofridos) por clube e mando
        club_gs: Dict[int, Dict[str, List[float]]] = defaultdict(
            lambda: {'home': [], 'away': []}
        )

        for row in rows:
            try:
                clube_id_str = row.get('atletas.clube_id') or row.get('clube_id', '')
                gs_str = row.get('atletas.scout.GS') or row.get('GS', '0')
                mando_str = row.get('mando', 'home')  # nem sempre presente

                if not clube_id_str:
                    continue

                clube_id = int(clube_id_str)
                gs = float(gs_str) if gs_str and gs_str.replace('.', '', 1).lstrip('-').isdigit() else 0.0
                mando = mando_str.lower()

                if mando == 'home' or mando == 'casa':
                    club_gs[clube_id]['home'].append(gs)
                else:
                    club_gs[clube_id]['away'].append(gs)
            except Exception:
                continue

        for clube_id, data in club_gs.items():
            if data['home']:
                avg_gs_home = float(np.mean(data['home']))
                self._goals_data[clube_id]['home_conceded'].append(avg_gs_home)
            if data['away']:
                avg_gs_away = float(np.mean(data['away']))
                self._goals_data[clube_id]['away_conceded'].append(avg_gs_away)

        self._is_fitted = len(self._goals_data) > 0

    def get_lambda_xGA(self, clube_id: int, is_home: bool) -> float:
        """
        Retorna λ (Expected Goals Against) para um clube dado o mando.
        Se não houver dados históricos, usa fallback conservador baseado em mando.
        """
        if not self._is_fitted or clube_id not in self._goals_data:
            # Fallback: sem dados históricos, usa media geral do futebol brasileiro
            return 1.0 if is_home else 1.3

        key = 'home_conceded' if is_home else 'away_conceded'
        history = self._goals_data[clube_id].get(key, [])

        if not history:
            return 1.0 if is_home else 1.3

        # Média ponderada — rodadas mais recentes têm peso maior (decay exponencial)
        n = len(history)
        weights = [math.exp(0.1 * i) for i in range(n)]
        total_w = sum(weights)
        lambda_val = sum(h * w for h, w in zip(history, weights)) / total_w
        return max(0.1, float(lambda_val))

    def prob_clean_sheet(self, clube_id: int, is_home: bool) -> float:
        """P(SG) = e^(-λ), onde λ é a expectativa de gols adversários."""
        lam = self.get_lambda_xGA(clube_id, is_home)
        return math.exp(-lam)

    def get_attack_strength(self, clube_id: int, is_home: bool) -> float:
        """
        Retorna o λ de ataque do clube (Expected Goals Scored).
        Usado para estimar probabilidade de Atacantes/Meias marcarem.
        """
        if not self._is_fitted or clube_id not in self._goals_data:
            return 1.2 if is_home else 0.9

        key = 'home_scored' if is_home else 'away_scored'
        history = self._goals_data[clube_id].get(key, [])

        if not history:
            return 1.2 if is_home else 0.9

        n = len(history)
        weights = [math.exp(0.1 * i) for i in range(n)]
        total_w = sum(weights)
        return max(0.1, sum(h * w for h, w in zip(history, weights)) / total_w)


# ──────────────────────────────────────────────────────────────────────────────
# 3. MÓDULO: MÉDIA CEDIDA POR POSIÇÃO COM MANDO DE CAMPO
# Referência PDF §2: "Calcular a média de pontos que cada time cede para cada
# posição (casa vs. fora)"
# ──────────────────────────────────────────────────────────────────────────────
class MediaCedidaEngine:
    """
    Calcula a "Média Cedida com Mando de Campo" por posição para cada clube.
    Exemplo: Time X cede em média 8.5 pontos para Atacantes adversários quando joga em casa.
    """

    def __init__(self) -> None:
        # {clube_id: {pos_id: {mando: [pontos_cedidos, ...]}}}
        self._cedido: Dict[int, Dict[int, Dict[str, List[float]]]] = defaultdict(
            lambda: defaultdict(lambda: {'home': [], 'away': []})
        )
        self._is_fitted = False

    def ingest_from_csv_rows(self, rows: List[Dict[str, str]]) -> None:
        """
        Processa linhas do CSV histórico do caRtola para calcular pontos cedidos por posição.
        Cada linha = um jogador em uma rodada. 'pontos_num' representa os pontos que ele fez
        CONTRA o clube adversário (que portanto "cedeu" aqueles pontos).
        """
        for row in rows:
            try:
                # Identificar o clube ADVERSÁRIO (quem cedeu os pontos)
                # O CSV tem o clube do jogador, precisamos do adversário
                # Tentamos ler colunas alternativas presentes no caRtola
                clube_id_str = row.get('atletas.clube_id') or row.get('clube_id', '')
                pontos_str = row.get('atletas.pontos_num') or row.get('pontos_num', '0')
                pos_str = row.get('atletas.posicao_id') or row.get('posicao_id', '0')
                mando_str = (row.get('mando', '') or '').lower()

                if not clube_id_str or not pos_str:
                    continue

                # O adversário (que cedeu) é registrado no mando invertido
                # Se o jogador joga em casa (mando='home'), os pontos foram cedidos pelo visitante
                clube_id = int(clube_id_str)
                pos_id = int(pos_str)
                pontos = float(pontos_str) if pontos_str else 0.0

                if pos_id not in [1, 2, 3, 4, 5]:
                    continue

                # Mando = perspectiva do jogador que marcou pontos
                # cedido_por = adversário = mando invertido
                cedido_mando = 'away' if (mando_str == 'home' or mando_str == 'casa') else 'home'
                self._cedido[clube_id][pos_id][cedido_mando].append(pontos)

            except Exception:
                continue

        self._is_fitted = len(self._cedido) > 0

    def get_media_cedida(self, clube_id: int, pos_id: int, is_home: bool) -> Optional[float]:
        """
        Retorna a média de pontos cedidos pelo clube_id para a posição pos_id.
        is_home é a perspectiva do clube que está cedendo (Not the attacker).
        """
        if not self._is_fitted or clube_id not in self._cedido:
            return None

        mando_key = 'home' if is_home else 'away'
        historico = self._cedido[clube_id].get(pos_id, {}).get(mando_key, [])

        if not historico:
            return None

        return float(np.mean(historico[-10:]))  # últimas 10 rodadas

    def get_difficulty_multiplier(self, adversario_clube_id: int, pos_id: int, adversario_is_home: bool) -> float:
        """
        Retorna um multiplicador de dificuldade baseado na média cedida pelo adversário.
        Media cedida alta = adversário fraco na marcação = multiplicador > 1.0 (fácil)
        Media cedida baixa = adversário forte na marcação = multiplicador < 1.0 (difícil)
        """
        media = self.get_media_cedida(adversario_clube_id, pos_id, adversario_is_home)

        if media is None:
            return 1.0  # sem dados: neutro

        # Benchmarks por posição (media geral do brasileirão aproximada)
        benchmarks = {1: 3.5, 2: 4.0, 3: 3.8, 4: 5.5, 5: 6.0}
        bench = benchmarks.get(pos_id, 5.0)

        ratio = media / bench if bench > 0 else 1.0
        # Normalizar: ratio > 1 = adversário cede mais que a média = mais fácil
        # Clamp entre 0.7 e 1.5
        return max(0.70, min(1.50, ratio))


# ──────────────────────────────────────────────────────────────────────────────
# 4. MÓDULO: CADEIAS DE MARKOV PARA ANÁLISE DE CONSISTÊNCIA
# Referência PDF: "Cadeias de Markov implementadas para avaliar a consistência,
# filtrando jogadores que 'oscilam' demais entre pontuações altas e negativas."
# ──────────────────────────────────────────────────────────────────────────────
class MarkovConsistencyAnalyzer:
    """
    Analisa a consistência de um jogador usando Cadeias de Markov de 3 estados:
    - NEGATIVO (pts < 0)
    - MÉDIO    (0 ≤ pts < 6)
    - BONS     (pts ≥ 6)
    
    Calcula a probabilidade de atingir estado BOM a partir do estado atual.
    """

    STATES = {'negative': 0, 'medium': 1, 'good': 2}
    STATE_LABELS = ['negative', 'medium', 'good']

    def __init__(self) -> None:
        self._player_histories: Dict[int, List[float]] = defaultdict(list)

    def ingest_score(self, atleta_id: int, pontos: float) -> None:
        self._player_histories[atleta_id].append(pontos)

    def ingest_from_csv_rows(self, rows: List[Dict[str, str]]) -> None:
        for row in rows:
            try:
                atleta_id_str = row.get('atletas.atleta_id') or row.get('atleta_id', '')
                pontos_str = row.get('atletas.pontos_num') or row.get('pontos_num', '0')

                if not atleta_id_str:
                    continue

                atleta_id = int(atleta_id_str)
                pontos = float(pontos_str) if pontos_str else 0.0
                self._player_histories[atleta_id].append(pontos)
            except Exception:
                continue

    def _classify_state(self, pontos: float) -> int:
        if pontos < 0:
            return self.STATES['negative']
        elif pontos < 6:
            return self.STATES['medium']
        else:
            return self.STATES['good']

    def _build_transition_matrix(self, atleta_id: int) -> Optional[np.ndarray]:
        history = self._player_histories.get(atleta_id, [])
        if len(history) < 4:
            return None

        # Matriz de transição 3×3
        matrix = np.zeros((3, 3))
        states = [self._classify_state(p) for p in history]

        for i in range(len(states) - 1):
            matrix[states[i]][states[i + 1]] += 1

        # Normalizar por linha
        row_sums = matrix.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1
        return matrix / row_sums

    def get_consistency_score(self, atleta_id: int) -> float:
        """
        Retorna um score de consistência entre 0.0 e 1.0.
        1.0 = jogador sempre faz pontos bons (muito consistente)
        0.0 = jogador muito oscilante
        """
        matrix = self._build_transition_matrix(atleta_id)
        if matrix is None:
            return 0.5  # default neutro sem histórico

        # Calcular distribuição estacionária (estado de longo prazo)
        try:
            eigenvalues, eigenvectors = np.linalg.eig(matrix.T)
            # Autovetor associado ao autovalor 1
            idx = np.argmin(np.abs(eigenvalues - 1.0))
            stationary = np.real(eigenvectors[:, idx])
            stationary = stationary / stationary.sum()
            stationary = np.maximum(stationary, 0)

            # Probabilidade de longo prazo de estar no estado BOM
            prob_good = float(stationary[self.STATES['good']])
            return max(0.0, min(1.0, prob_good))
        except Exception:
            # Fallback: proporção simples de rodadas com pontuação BOA
            history = self._player_histories.get(atleta_id, [])
            if not history:
                return 0.5
            good_rounds = sum(1 for p in history if p >= 6)
            return float(good_rounds) / len(history)

    def get_volatility_penalty(self, atleta_id: int) -> float:
        """
        Retorna a penalidade de volatilidade (0.0 = sem penalidade, 1.0 = muito volátil).
        Alta volatilidade = jogador que oscila muito = penalidade no score final.
        """
        history = self._player_histories.get(atleta_id, [])
        if len(history) < 3:
            return 0.0

        # Desvio padrão normalizado (coeficiente de variação)
        arr = np.array(history, dtype=float)
        std = float(np.std(arr))
        mean = float(np.mean(arr))
        if abs(mean) < 0.01:
            return min(1.0, std / 10.0)

        cv = abs(std / mean)
        # CV > 1.5 é muito volátil
        return max(0.0, min(1.0, cv / 2.0))


# ──────────────────────────────────────────────────────────────────────────────
# 5. MÓDULO: AFFINITY PROPAGATION — CLUSTERING DE PERFIL TÉCNICO
# Referência PDF: "Affinity Propagation que agrupa jogadores por perfil técnico
# (ex: 'finalizadores' vs 'garçons') sem necessidade de definir nº de grupos"
# ──────────────────────────────────────────────────────────────────────────────
class PlayerProfileClusterer:
    """
    Agrupa jogadores por perfil técnico usando Affinity Propagation.
    Features: G, A, FT, DS, DE, FS, FC (normalizadas por jogo).
    """

    CLUSTER_LABELS = {
        0: "Finalizador",
        1: "Garçom",
        2: "Defensivo",
        3: "Box-to-Box",
        4: "Polivalente",
    }

    def __init__(self) -> None:
        self._model = None
        self._player_features: Dict[int, np.ndarray] = {}
        self._cluster_map: Dict[int, int] = {}
        self._is_fitted = False

    def ingest_player_features(self, atleta_id: int, scouts: Dict[str, Any], jogos: int) -> None:
        """Calcula feature vector por jogo para o jogador."""
        j = max(jogos, 1)
        features = np.array([
            float(scouts.get('G', 0) or 0) / j,
            float(scouts.get('A', 0) or 0) / j,
            float(scouts.get('FT', 0) or 0) / j,
            float(scouts.get('DS', 0) or 0) / j,
            float(scouts.get('DE', 0) or 0) / j,
            float(scouts.get('FS', 0) or 0) / j,
            float(scouts.get('FC', 0) or 0) / j,
        ], dtype=float)
        self._player_features[atleta_id] = features

    def fit(self) -> bool:
        """
        Executa Affinity Propagation em todos os jogadores ingeridos.
        Retorna True se o fitting foi bem-sucedido.
        """
        if len(self._player_features) < 5:
            return False

        try:
            from sklearn.cluster import AffinityPropagation
            from sklearn.preprocessing import StandardScaler

            ids = list(self._player_features.keys())
            X = np.array([self._player_features[i] for i in ids])

            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # damping entre 0.7 e 0.9 para evitar oscilação
            ap = AffinityPropagation(damping=0.8, max_iter=300, random_state=42)
            labels = ap.fit_predict(X_scaled)

            for atleta_id, label in zip(ids, labels):
                self._cluster_map[atleta_id] = int(label)

            self._is_fitted = True
            return True
        except Exception as e:
            logger.warning(f"Affinity Propagation falhou: {e}")
            return False

    def get_cluster_label(self, atleta_id: int) -> str:
        """Retorna o rótulo do cluster do jogador."""
        if not self._is_fitted or atleta_id not in self._cluster_map:
            return "Desconhecido"
        cluster_id = self._cluster_map[atleta_id] % len(self.CLUSTER_LABELS)
        return self.CLUSTER_LABELS.get(cluster_id, "Polivalente")

    def get_cluster_bonus(self, atleta_id: int, pos_id: int) -> float:
        """
        Retorna bônus/penalidade de score baseado no alinhamento entre
        o perfil do jogador (cluster) e a posição táctica.
        Ex: Finalizador como Atacante → bônus; Finalizador como Zagueiro → penalidade.
        """
        label = self.get_cluster_label(atleta_id)
        bonuses = {
            # (label, pos_id) → multiplicador
            ("Finalizador", 5): 1.15,
            ("Finalizador", 4): 1.05,
            ("Finalizador", 2): 0.90,
            ("Finalizador", 3): 0.85,
            ("Garçom", 4): 1.15,
            ("Garçom", 5): 1.05,
            ("Garçom", 2): 1.00,
            ("Defensivo", 1): 1.15,
            ("Defensivo", 2): 1.10,
            ("Defensivo", 3): 1.10,
            ("Defensivo", 4): 0.90,
            ("Defensivo", 5): 0.80,
            ("Box-to-Box", 4): 1.10,
            ("Box-to-Box", 2): 1.05,
            ("Box-to-Box", 5): 1.00,
        }
        return bonuses.get((label, pos_id), 1.0)


# ──────────────────────────────────────────────────────────────────────────────
# 6. MÓDULO: RANDOM FOREST — MODELO PREDITIVO
# Referência PDF §3: "Treinar um regressor (Random Forest ou XGBoost) usando as
# médias de mando e a dificuldade como variáveis de entrada."
# ──────────────────────────────────────────────────────────────────────────────
class RandomForestPredictor:
    """
    Modelo preditivo de pontuação por jogador usando Random Forest.
    Features de entrada:
    - media_historica: média de pontos do jogador no histórico
    - ies: Índice de Eficiência de Scout (ações/min)
    - lambda_xga: λ esperado de gols adversários (Poisson)
    - media_cedida_pos: média de pontos cedidos pelo adversário para esta posição
    - is_home: 1 se mandante, 0 se visitante
    - consistency_score: score de Cadeias de Markov (0-1)
    - pos_id: posição (1-5)
    """

    def __init__(self) -> None:
        self._model = None
        self._is_fitted = False
        self._X_train: List[List[float]] = []
        self._y_train: List[float] = []

    def add_training_sample(
        self,
        media: float,
        ies: float,
        lambda_xga: float,
        media_cedida: float,
        is_home: int,
        consistency: float,
        pos_id: int,
        pontos_reais: float,
    ) -> None:
        """Adiciona uma amostra de treinamento (jogador × rodada histórica)."""
        self._X_train.append([media, ies, lambda_xga, media_cedida, is_home, consistency, float(pos_id)])
        self._y_train.append(pontos_reais)

    def fit(self) -> bool:
        """Treina o Random Forest se houver amostras suficientes (mínimo 30)."""
        if len(self._X_train) < 30:
            logger.info(f"RF: amostras insuficientes ({len(self._X_train)}). Usando fallback determinístico.")
            return False
        try:
            from sklearn.ensemble import RandomForestRegressor
            from sklearn.preprocessing import StandardScaler

            X = np.array(self._X_train, dtype=float)
            y = np.array(self._y_train, dtype=float)

            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            rf = RandomForestRegressor(
                n_estimators=100,
                max_depth=6,
                min_samples_leaf=3,
                random_state=42,
                n_jobs=-1,
            )
            rf.fit(X_scaled, y)

            self._model = (rf, scaler)
            self._is_fitted = True
            logger.info(f"RF: treinado com {len(self._X_train)} amostras.")
            return True
        except Exception as e:
            logger.warning(f"RF: treinamento falhou — {e}")
            return False

    def predict(
        self,
        media: float,
        ies: float,
        lambda_xga: float,
        media_cedida: float,
        is_home: int,
        consistency: float,
        pos_id: int,
    ) -> Optional[float]:
        """Prediz pontuação esperada. Retorna None se modelo não treinado."""
        if not self._is_fitted or self._model is None:
            return None
        try:
            rf, scaler = self._model
            X = np.array([[media, ies, lambda_xga, media_cedida, is_home, consistency, float(pos_id)]])
            X_scaled = scaler.transform(X)
            return float(rf.predict(X_scaled)[0])
        except Exception:
            return None


# ──────────────────────────────────────────────────────────────────────────────
# 7. PROCESSADOR PRINCIPAL — DataProcessor
# ──────────────────────────────────────────────────────────────────────────────
class DataProcessor:
    """
    Orquestra todos os módulos de IA para gerar a pontuação esperada de cada jogador.
    Pipeline:
    1. Ingestão do CSV histórico → alimenta Poisson, MediaCedida, Markov, RF
    2. Clustering por Affinity Propagation
    3. Normalização de jogadores com score final composto
    """

    def __init__(self) -> None:
        self.historical_stats: Dict[int, Dict[str, float]] = {}
        self.scout_weights = SCOUT_WEIGHTS

        # Módulos de IA
        self.poisson = PoissonModel()
        self.media_cedida = MediaCedidaEngine()
        self.markov = MarkovConsistencyAnalyzer()
        self.clusterer = PlayerProfileClusterer()
        self.rf_predictor = RandomForestPredictor()

        self._csv_rows_cache: List[Dict[str, str]] = []
        self._pipeline_fitted = False

    # ------------------------------------------------------------------
    # INGESTÃO DE DADOS HISTÓRICOS
    # ------------------------------------------------------------------
    def ingest_historical_csv(self, csv_text: str) -> None:
        """
        Ingere CSV histórico do caRtola e alimenta todos os módulos de IA.
        Formato esperado: rodada-{N}.csv do repositório henriquepgomide/caRtola.
        """
        if not csv_text or not csv_text.strip():
            return

        try:
            reader = csv.DictReader(io.StringIO(csv_text))
            rows = list(reader)
        except Exception:
            return

        self._csv_rows_cache.extend(rows)

        # Alimentar cada módulo
        self.poisson.ingest_from_csv_rows(rows)
        self.media_cedida.ingest_from_csv_rows(rows)
        self.markov.ingest_from_csv_rows(rows)

        for row in rows:
            try:
                atleta_id_str = row.get('atletas.atleta_id') or row.get('atleta_id', '')
                if not atleta_id_str:
                    continue
                atleta_id = int(atleta_id_str)

                media_str = row.get('atletas.media_num') or row.get('media_num', '0')
                jogos_str = row.get('atletas.jogos_num') or row.get('jogos_num', '0')
                pontos_str = row.get('atletas.pontos_num') or row.get('pontos_num', '0')

                media = float(media_str) if media_str and media_str.replace('.', '', 1).isdigit() else 0.0
                jogos = int(jogos_str) if jogos_str and jogos_str.isdigit() else 0
                pontos = float(pontos_str) if pontos_str and pontos_str.replace('.', '', 1).lstrip('-').isdigit() else 0.0

                self.historical_stats[atleta_id] = {
                    'media_num': media,
                    'jogos_num': float(jogos),
                }

                # Preparar features para clustering
                scouts_raw = {k.replace('atletas.scout.', ''): v for k, v in row.items() if 'scout.' in k}
                if scouts_raw:
                    self.clusterer.ingest_player_features(atleta_id, scouts_raw, max(jogos, 1))

            except Exception:
                continue

    def fit_ml_pipeline(self) -> None:
        """Treina os modelos de ML (clustering + RF) com os dados ingeridos."""
        if self._pipeline_fitted:
            return

        logger.info("Fitting clustering (Affinity Propagation)...")
        self.clusterer.fit()

        logger.info("Fitting Random Forest...")
        self.rf_predictor.fit()

        self._pipeline_fitted = True

    # ------------------------------------------------------------------
    # IES — Índice de Eficiência de Scout
    # ------------------------------------------------------------------
    def _calculate_ies(self, scouts: Dict[str, Any], jogos_num: int) -> float:
        """
        IES = Densidade de Ações por Minuto Jogado.
        Ações ponderadas: Gol (8.0), A (5.0), FT (3.0), FD (1.2), FF (0.8), DS (1.2), SG (5.0).
        """
        g  = float(scouts.get('G', 0) or 0)
        a  = float(scouts.get('A', 0) or 0)
        ft = float(scouts.get('FT', 0) or 0)
        fd = float(scouts.get('FD', 0) or 0)
        ff = float(scouts.get('FF', 0) or 0)
        ds = float(scouts.get('DS', 0) or 0)
        sg = float(scouts.get('SG', 0) or 0)

        total_actions = (g * 8.0) + (a * 5.0) + (ft * 3.0) + (fd * 1.2) + (ff * 0.8) + (ds * 1.2) + (sg * 5.0)
        minutos = float(max(jogos_num * 90, 90))
        return float(total_actions / minutos)

    # ------------------------------------------------------------------  
    # CÁLCULO DE PONTOS ESPERADOS — PIPELINE COMPLETO
    # ------------------------------------------------------------------
    def _calculate_expected_points(
        self,
        player: Dict[str, Any],
        matches: Optional[Dict[str, Any]] = None,
        clubes_dict: Optional[Dict[str, Any]] = None,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Pipeline completo de cálculo de pontuação esperada:
        1. Score base (scouts × pesos fixos) por jogo
        2. Blend com histórico se jogos_num < 3
        3. IES boost
        4. Poisson SG com λ real (histórico de gols)
        5. Média Cedida por Posição como multiplicador de dificuldade
        6. Clustering bonus (Affinity Propagation)
        7. Consistência penalidade (Markov)
        8. Random Forest override se modelo treinado
        """
        scouts: Dict[str, Any] = player.get('scout', {})
        if not isinstance(scouts, dict):
            scouts = {}

        atleta_id = int(player.get('atleta_id', 0) or 0)
        pos_id = int(player.get('posicao_id', 0) or 0)
        clube_id = player.get('clube_id')
        jogos_num = max(int(player.get('jogos_num', 1) or 1), 1)
        reasons: List[str] = []

        # ── STEP 1: Score base por pesos fixos de scouts ──────────────
        total_derived = 0.0
        for sk, sv in scouts.items():
            k = str(sk)
            if k in self.scout_weights and k != 'SG':
                val = float(sv) if sv is not None else 0.0
                total_derived += val * self.scout_weights[k]

        base_projection = total_derived / float(jogos_num)

        # ── STEP 2: Blend com histórico (Para jogadores com poucos jogos) ──
        if jogos_num < 3:
            if atleta_id in self.historical_stats:
                media_num = self.historical_stats[atleta_id].get('media_num', 0.0)
            else:
                media_num = float(player.get('media_num', 0.0) or 0.0)
            base_projection = (base_projection + (media_num * 2.0)) / 3.0

        # ── STEP 3: IES Boost ──────────────────────────────────────────
        ies = self._calculate_ies(scouts, jogos_num)
        base_projection += ies * 100.0
        if ies > 0.05:
            reasons.append(f"IES Alto ({ies:.3f} ações/min)")

        # ── STEPS 4-7: Contexto da partida (Poisson, Média Cedida, Clustering, Markov) ──
        context_multiplier = 1.0
        lambda_xga = 1.1  # default
        media_cedida_val = 5.0  # default neutro
        is_home = True  # default

        explain_dict = {
            "reasons": reasons,
            "base_media": 0.0,
            "is_home": True,
            "adv_name": "N/A",
            "adv_slug": "N/A",
            "tier_diff": 0,
            "is_derby": False,
            "difficulty_adjusted": 1.0,
            "lambda_xga": lambda_xga,
            "media_cedida_val": media_cedida_val,
        }

        if matches and isinstance(matches, dict) and 'partidas' in matches:
            partidas = matches.get('partidas', [])
            if isinstance(partidas, list):
                for part in partidas:
                    if not isinstance(part, dict):
                        continue
                    home_match = part.get('clube_casa_id') == clube_id
                    away_match = part.get('clube_visitante_id') == clube_id

                    if not (home_match or away_match):
                        continue

                    valida = part.get('valida', True)
                    if not valida:
                        explain_dict["reasons"].append("Jogo Inválido (Cancelado/Adiado)")
                        return 0.0, explain_dict

                    is_home = home_match
                    explain_dict["is_home"] = is_home
                    
                    adv_id = part.get('clube_visitante_id' if is_home else 'clube_casa_id')
                    if adv_id and clubes_dict:
                        explain_dict["adv_name"] = clubes_dict.get(str(adv_id), {}).get("nome", "???")
                        explain_dict["adv_slug"] = clubes_dict.get(str(adv_id), {}).get("slug", "???")

                    adv_pos = int(part.get('clube_visitante_posicao' if is_home else 'clube_casa_posicao', 10) or 10)
                    my_pos = int(part.get('clube_casa_posicao' if is_home else 'clube_visitante_posicao', 10) or 10)
                    
                    if adv_pos == 0: adv_pos = 10
                    if my_pos == 0: my_pos = 10

                    # ────────────────────────────────────────────────────────
                    # NOVO: Momentum com Decaimento e Favoritismo usando Tiers
                    # ────────────────────────────────────────────────────────
                    aprov_meu = part.get('aproveitamento_mandante' if is_home else 'aproveitamento_visitante', [])
                    aprov_adv = part.get('aproveitamento_visitante' if is_home else 'aproveitamento_mandante', [])
                    
                    if isinstance(aprov_meu, list) and isinstance(aprov_adv, list):
                        def calcula_momentum(aprov_list):
                            score = 0.0
                            valid_list = [r for r in aprov_list if r in ('v', 'e', 'd')]
                            n = len(valid_list)
                            for i, res in enumerate(valid_list):
                                weight = 1.0 - ((n - 1 - i) * 0.2) # Decai 20% a cada jogo p/ trás
                                if res == 'v': score += 1.0 * weight
                                elif res == 'e': score += 0.4 * weight
                                elif res == 'd': score -= 0.5 * weight
                            return score

                        score_meu = calcula_momentum(aprov_meu)
                        score_adv = calcula_momentum(aprov_adv)
                        
                        momentum_diff = score_meu - score_adv
                        context_multiplier *= max(0.80, min(1.20, 1.0 + (momentum_diff * 0.05)))

                    # ────────────────────────────────────────────────────────
                    # Clássicos, Tiers e Probabilidade SG Cruzada
                    # ────────────────────────────────────────────────────────
                    my_uf = ESTADOS_CLUBES.get(clube_id, 'MY')
                    adv_uf = ESTADOS_CLUBES.get(adv_id, 'ADV')
                    is_derby = (my_uf == adv_uf)

                    my_tier = get_tier(my_pos)
                    adv_tier = get_tier(adv_pos)
                    tier_diff = my_tier - adv_tier
                    explain_dict["tier_diff"] = tier_diff

                    if is_derby:
                        tier_diff = 0 # Anula discrepância extrema da tabela
                        explain_dict["is_derby"] = True
                        reasons.append("Clássico Regional: Jogo tende a ser muito disputado e imprevisível.")

                    if tier_diff >= 2: # Zebra
                        underdog_penalty = max(0.40, 1.0 - (tier_diff * 0.15))
                        if not is_home: underdog_penalty *= 0.85
                        context_multiplier *= underdog_penalty
                        reasons.append(f"Jogo Difícil: Enfrenta um adversário mais forte{' fora de casa' if not is_home else ''}.")
                    elif tier_diff <= -2: # Favorito
                        favorite_bonus = min(1.30, 1.0 + (abs(tier_diff) * 0.08))
                        if is_home: favorite_bonus *= 1.10
                        context_multiplier *= favorite_bonus
                        reasons.append(f"Amplo Favorito: É superior ao adversário{' e joga com apoio da torcida' if is_home else ''}.")

                    # STEP 4: Poisson Cruzado com λ REAL e Força do Oponente
                    if pos_id in DEFENSIVE_POSITIONS:
                        lambda_xga = self.poisson.get_lambda_xGA(clube_id, is_home)
                        adv_atk_strength = self.poisson.get_attack_strength(adv_id, not is_home) if adv_id else 1.1
                        
                        # Multiplica lambda base pela força ofensiva do oponente
                        lambda_adjusted = lambda_xga * (adv_atk_strength / 1.1)
                        prob_sg = math.exp(-lambda_adjusted)
                        
                        if tier_diff >= 2: # Zebra dificilmente segura SG
                            prob_sg *= max(0.15, 1.0 - (tier_diff * 0.20))
                            if not is_home: prob_sg *= 0.7
                        elif tier_diff <= -2: # Favorito tem mais chance
                            prob_sg = min(0.95, prob_sg * (1.0 + (abs(tier_diff) * 0.10)))
                            if is_home: prob_sg *= 1.1
                            
                        prob_sg = min(0.95, prob_sg)
                        sg_points = prob_sg * 5.0
                        base_projection += sg_points
                        
                        sg_pct = prob_sg * 100
                        if sg_pct > 40:
                            reasons.append(f"Defesa Sólida: Alta probabilidade de garantir saldo de gols (+5 pontos) nesta rodada ({sg_pct:.0f}% chance).")
                    else:
                        atk_strength = self.poisson.get_attack_strength(clube_id, is_home)
                        adv_xga = self.poisson.get_lambda_xGA(adv_id, not is_home) if adv_id else 1.1
                        lambda_xga = atk_strength * (adv_xga / 1.1)
                        if lambda_xga > 1.5:
                            reasons.append(f"Ataque Potente: Ótima expectativa de que este time marque muitos gols no jogo.")

                    # STEP 5: Média Cedida por Posição (Cruzada contra Tiers)
                    if adv_id:
                        adv_is_home = not is_home
                        difficulty_mult = self.media_cedida.get_difficulty_multiplier(adv_id, pos_id, adv_is_home)
                        mc = self.media_cedida.get_media_cedida(adv_id, pos_id, adv_is_home)
                        media_cedida_val = mc if mc is not None else media_cedida_val

                        # Ajusta dificuldade baseado no favoritismo. Favoritos furam mais defesas, zebras menos.
                        diff_cross_weight = 1.0 - (tier_diff * 0.05)
                        difficulty_adjusted = difficulty_mult * max(0.8, min(1.2, diff_cross_weight))
                        explain_dict["difficulty_adjusted"] = difficulty_adjusted

                        context_multiplier *= difficulty_adjusted

                        if difficulty_adjusted > 1.15:
                            reasons.append(f"Adversário Frágil: O time oponente costuma ceder muitos pontos para essa posição.")
                        elif difficulty_adjusted < 0.85:
                            reasons.append(f"Marcação Dura: O time oponente costuma anular jogadores dessa posição.")
                    else:
                        if is_home: context_multiplier *= 1.10
                        else: context_multiplier *= 0.90

                    break  # só processa a primeira partida encontrada
                    
        explain_dict["lambda_xga"] = lambda_xga
        explain_dict["media_cedida_val"] = media_cedida_val

        # STEP 6: Bônus de perfil técnico (Affinity Propagation)
        cluster_bonus = self.clusterer.get_cluster_bonus(atleta_id, pos_id)
        context_multiplier *= cluster_bonus
        cluster_label = self.clusterer.get_cluster_label(atleta_id)
        if cluster_label != "Desconhecido" and abs(cluster_bonus - 1.0) > 0.05:
            reasons.append(f"Beneficiado: Seu estilo de jogo '{cluster_label}' o favorece estatisticamente.")

        # STEP 7: Penalidade de consistência (Markov)
        volatility = self.markov.get_volatility_penalty(atleta_id)
        consistency = self.markov.get_consistency_score(atleta_id)
        # Penalidade: reduz até 20% para jogadores muito voláteis
        markov_factor = 1.0 - (volatility * 0.20)
        context_multiplier *= markov_factor
        if volatility > 0.5:
            reasons.append(f"Risco de Zebra: Jogador oscila muito e tem histórico instável, pontos ajustados por segurança.")

        # ── STEP 8: Random Forest override ─────────────────────────────
        media_hist = float(
            self.historical_stats.get(atleta_id, {}).get('media_num', 0.0)
            or player.get('media_num', 0.0)
            or 0.0
        )
        rf_pred = self.rf_predictor.predict(
            media=media_hist,
            ies=ies,
            lambda_xga=lambda_xga,
            media_cedida=media_cedida_val,
            is_home=int(is_home),
            consistency=consistency,
            pos_id=pos_id,
        )

        if rf_pred is not None:
            # Blend: 60% RF + 40% determinístico para não perder transparência
            base_projection = (rf_pred * 0.60) + (base_projection * 0.40)
            reasons.append(f"Aprovado: Nossa IA preditiva projeta uma excelente partida para ele.")

        # ── SCORE FINAL ─────────────────────────────────────────────
        final_ep = float(base_projection * context_multiplier)

        # Jogador não disponível → score inutilizável
        if int(player.get('status_id', 0) or 0) != 7:
            final_ep = -999.0

        explain_dict["base_media"] = media_hist
        
        return final_ep, explain_dict

    # ------------------------------------------------------------------
    # NORMALIZAÇÃO DE JOGADORES (interface com o Solver)
    # ------------------------------------------------------------------
    def normalize_players(
        self,
        cartola_atletas: Dict[str, Any],
        objective: str = "mitagem",
        cartola_partidas: Optional[Dict[str, Any]] = None,
        ousadia: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Normaliza os atletas do Cartola para o formato do MathEngine (PuLP Solver).
        Alimenta também o clusterer e treina o pipeline ML antes de calcular scores.
        """
        # Fitar o pipeline ML com os dados históricos ingeridos
        self.fit_ml_pipeline()

        players: List[Dict[str, Any]] = []
        raw_players = cartola_atletas.get('atletas', [])
        clubes_dict = cartola_atletas.get('clubes', {})
        if not isinstance(raw_players, list):
            return players

        for rp in raw_players:
            if not isinstance(rp, dict):
                continue

            pos = rp.get('posicao_id')
            clube = rp.get('clube_id')
            preco = float(rp.get('preco_num', 0.0) or 0.0)
            ultima_pt = float(rp.get('pontos_num', 0.0) or 0.0)
            
            # Buscar a sigla do clube 
            clube_slug = '??'
            if clube and str(clube) in clubes_dict:
                clube_info = clubes_dict[str(clube)]
                clube_slug = clube_info.get('abreviacao') or clube_info.get('slug') or '??'

            # Alimentar clusterer com dados do mercado atual
            scouts_cur = rp.get('scout', {})
            if isinstance(scouts_cur, dict) and scouts_cur:
                atleta_id_cur = int(rp.get('atleta_id', 0) or 0)
                jogos_cur = max(int(rp.get('jogos_num', 1) or 1), 1)
                self.clusterer.ingest_player_features(atleta_id_cur, scouts_cur, jogos_cur)

            pts_esperados, explain_dict = self._calculate_expected_points(rp, cartola_partidas, clubes_dict)

            # MV (Mínimo para Valorizar)
            from app.services.market import cartola_service
            mv = cartola_service.calculate_mv(preco, ultima_pt)
            pts_valorizacao = float(pts_esperados - mv)

            # Ousadia: 1-9 escala o risco/retorno
            # Ousadia alta → favorece pontuação absoluta (mitagem)
            # Ousadia baixa → penaliza jogadores voláteis
            ousadia_factor = 0.8 + (ousadia * 0.04)  # 0.84 a 1.16

            explain_dict["valorizacao_mv"] = mv
            explain_dict["expected_valorization"] = pts_valorizacao
            
            if objective == "valorizacao":
                solver_score = pts_valorizacao * ousadia_factor
            else:
                solver_score = pts_esperados * ousadia_factor

            # Enriquecer o output com informações de perfil e consistência
            atleta_id = int(rp.get('atleta_id', 0) or 0)
            cluster_label = self.clusterer.get_cluster_label(atleta_id)
            consistency_score = self.markov.get_consistency_score(atleta_id)

            # Adicionar heurísticas positivas baseadas em preço e projeção (Custo-Benefício)
            reasons_list = explain_dict.get("reasons", [])
            if preco > 0:
                cb_ratio = pts_esperados / preco
                if preco <= 5.0 and pts_esperados >= 2.0:
                    reasons_list.append("Bom Custo-Benefício: Jogador muito barato que ajuda a libertar cartoletas para outras posições (Enabler).")
                elif cb_ratio >= 1.0 and pts_esperados >= 5.0:
                    reasons_list.append("Custo-Benefício Excelente: Projeção de pontos muito alta em relação ao seu preço atual.")
                elif preco >= 15.0 and pts_esperados >= 8.0:
                    reasons_list.append("Premium Confirmado: Jogador caro mas com projeção forte que justifica o investimento.")
            
            explain_dict["reasons"] = reasons_list

            p = {
                "id": rp.get('atleta_id'),
                "nome": rp.get('apelido'),
                "pos": pos,
                "preco": preco,
                "pontos_esperados": pts_esperados,
                "pontos_valorizacao": pts_valorizacao,
                "solver_score": solver_score,
                "clube_id": clube,
                "clube_slug": clube_slug,
                "status_id": rp.get('status_id'),
                "foto": rp.get('foto'),
                "metadata_explicativa": explain_dict,
                "perfil": cluster_label,
                "consistencia": round(consistency_score, 2),
                "reason": " • ".join(explain_dict.get("reasons", [])) if explain_dict.get("reasons") else "Análise estatística padrão."
            }

            if p['status_id'] == 7:
                players.append(p)

        return players

    def get_top_sgs(self, cartola_partidas: Dict[str, Any], cartola_atletas: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Calcula os times com maior probabilidade de SG na rodada atual."""
        if not cartola_partidas or 'partidas' not in cartola_partidas:
            return []
            
        clubes_dict = cartola_atletas.get('clubes', {})
        top_sgs = []
        
        for part in cartola_partidas.get('partidas', []):
            if not part.get('valida', True):
                continue
                
            casa_id = part.get('clube_casa_id')
            vis_id = part.get('clube_visitante_id')
            casa_pos = int(part.get('clube_casa_posicao', 10) or 10)
            vis_pos = int(part.get('clube_visitante_posicao', 10) or 10)
            
            casa_uf = ESTADOS_CLUBES.get(casa_id, 'MY')
            vis_uf = ESTADOS_CLUBES.get(vis_id, 'ADV')
            is_derby = (casa_uf == vis_uf)

            tier_casa = get_tier(casa_pos)
            tier_vis = get_tier(vis_pos)

            # Prob SG Casa
            lambda_xga_casa = self.poisson.get_lambda_xGA(casa_id, True)
            adv_atk_strength_vis = self.poisson.get_attack_strength(vis_id, False) if vis_id else 1.1
            lambda_adjusted_casa = lambda_xga_casa * (adv_atk_strength_vis / 1.1)
            prob_sg_casa = math.exp(-lambda_adjusted_casa)
            
            diff_casa = tier_casa - tier_vis
            if not is_derby:
                if diff_casa >= 2: prob_sg_casa *= max(0.15, 1.0 - (diff_casa * 0.20))
                elif diff_casa <= -2: prob_sg_casa = min(0.95, prob_sg_casa * (1.0 + (abs(diff_casa) * 0.10)) * 1.1)
            prob_sg_casa = min(0.95, prob_sg_casa)

            # Prob SG Visitante
            lambda_xga_vis = self.poisson.get_lambda_xGA(vis_id, False)
            adv_atk_strength_casa = self.poisson.get_attack_strength(casa_id, True) if casa_id else 1.1
            lambda_adjusted_vis = lambda_xga_vis * (adv_atk_strength_casa / 1.1)
            prob_sg_vis = math.exp(-lambda_adjusted_vis)
            
            diff_vis = tier_vis - tier_casa
            if not is_derby:
                if diff_vis >= 2: prob_sg_vis *= max(0.15, 1.0 - (diff_vis * 0.20)) * 0.7
                elif diff_vis <= -2: prob_sg_vis = min(0.95, prob_sg_vis * (1.0 + (abs(diff_vis) * 0.10)))
            prob_sg_vis = min(0.95, prob_sg_vis)

            # Insert Casa
            if casa_id and str(casa_id) in clubes_dict:
                c_info = clubes_dict[str(casa_id)]
                top_sgs.append({
                    "clube_id": casa_id,
                    "nome": c_info.get("nome"),
                    "escudo": c_info.get("escudos", {}).get("60x60"),
                    "prob_sg": prob_sg_casa,
                    "adversario": clubes_dict.get(str(vis_id), {}).get("nome", "???"),
                    "mando": "casa",
                    "motivo": f"Favorito em casa contra {clubes_dict.get(str(vis_id), {}).get('nome', '???')}. Alta chance de não sofrer gol." if adv_atk_strength_vis < 1.0 else "Probabilidade sólida calculada via força defensiva e mando de campo."
                })
            # Insert Visitante
            if vis_id and str(vis_id) in clubes_dict:
                v_info = clubes_dict[str(vis_id)]
                top_sgs.append({
                    "clube_id": vis_id,
                    "nome": v_info.get("nome"),
                    "escudo": v_info.get("escudos", {}).get("60x60"),
                    "prob_sg": prob_sg_vis,
                    "adversario": clubes_dict.get(str(casa_id), {}).get("nome", "???"),
                    "mando": "fora",
                    "motivo": f"Enfrenta {clubes_dict.get(str(casa_id), {}).get('nome', '???')} com ataque fraco e histórico ruim. IA calcula SG provável." if adv_atk_strength_casa < 1.0 else "Calculado via Poisson considerando tiers e força defensiva."
                })
                
        top_sgs.sort(key=lambda x: x["prob_sg"], reverse=True)
        return top_sgs[:4]

# Singleton global
data_processor = DataProcessor()
