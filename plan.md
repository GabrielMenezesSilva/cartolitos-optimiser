# 🏆 Planejamento Estratégico: Cartolitos Optimiser (Full-Stack Platform)

## 1. Lógica Pro (Inteligência de Dados e Solver)
**Objetivo:** Extrair e aplicar o conhecimento estatístico validado do repositório `henriquepgomide/caRtola`.

*   **Ingestão e Sincronização Automática:** 
    *   Pipeline contínuo buscando os dados da API Oficial do Cartola FC (mercado, pontuações parciais, status dos atletas) para a temporada atual (2025/2026), armazenando cache inteligente no Supabase.
*   **Modelos Preditivos (caRtola Docs):**
    *   **Regressão de Pontos (Mitar):** Utilização de médias móveis de pontuação, mando de campo e força defensiva do adversário para projetar Expected Value (EV) de cada jogador (Expectativa de Pontos).
    *   **Lógica de Valorização (Cartoletas):** Cálculo do diferencial entre média necessária e preço atual para projetar o ganho de cartoletas (Sistema de Valorização baseado nos notebooks validados).
*   **Motor de Otimização (PuLP):**
    *   Configuração do *Knapsack Problem* multi-restrição: 
        *   *Restrição 1:* Orçamento (Patrimônio definido via Slider).
        *   *Restrição 2:* Esquema Tático (ex: exatamente 1 GOL, 2 ZAG, 2 LAT, 3 MEI, 3 ATA, 1 TEC).
        *   *Restrição 3:* Status do jogador (Apenas "Prováveis").
    *   **Função Objetivo Dinâmica:** Alternagem entre maximizar Expectativa de Pontos (`Mitar`) ou maximizar Projeção Euclidiana de Valorização (`Valorizar`).

## 2. Frontend Visual (O "Campinho" Profissional)
**Objetivo:** Substituir tabelas de texto por um Dashboard altamente interativo, focado em Experiência do Usuário (UX).

*   **O Componente "Campinho" (Visual Pitch):**
    *   Layout em proporção real de um campo de futebol, mapeando a distribuição tática a partir da escolha do usuário (ex: 4-3-3 aloca zagueiros e laterais na defesa, triângulo no meio, tridente no ataque).
*   **Cards de Jogadores (Pitch Overlay):**
    *   Carregamento rápido da foto oficial da API da Globo.
    *   Mini-badge com o Custo (C$), Pontos Esperados (PE) e ícone do time.
    *   "Badge de Capitão" dinâmico (com a letra "C" dourada) atrelado ao jogador ofensivo com maior Variância/EV calculados pelo PuLP.
*   **Painel de Controles e Side-bar:**
    *   *Slider Fluido* de Orçamento/Cartoletas.
    *   *Switch Tático:* Selector rápido (4-3-3, 3-4-3, 3-5-2, 4-4-2).
    *   *Objetivo Toggle:* Botão estilizado com ícones (Raio ⚡ para "Mitar", Saco de Dinheiro 💰 para "Valorizar").
*   **Justificativa Interativa (Drawer/Modal):**
    *   Ao clicar no card do atleta no Campinho, uma layer lateral exibe o porquê de o Solver tê-lo escolhido (ex: "Joga em casa contra a 3ª pior defesa", "Precisa de apenas 1.5 pontos para valorizar", etc).

## 3. Arquitetura do Sistema
**Objetivo:** Arquitetura limpa, escalável e conectada às nossas ferramentas integradas.

*   **Banco de Dados (Point of Truth):**
    *   **Supabase PostgreSQL** (`https://vnufdzfedzncdiyxujgp.supabase.co`).
    *   Tabelas principais: `players_cache`, `teams_cache`, `rounds_history`. Gerenciamento via `Supabase MCP`.
*   **Motor Backend (Python / FastAPI):**
    *   Módulos: `analytics.py` (ETL e modelos de regressão), `market.py` (scraping/ingestão) e `solver.py` (PuLP API endpoint). 
    *   Serviço assíncrono para lidar rapidamente com a matriz de 500+ jogadores.
*   **Camada Frontend (React / Tailwind):**
    *   Consome a API Python e expõe no Dashboard. Interface rica e animações limpas para as trocas de jogador promovidas pelo algoritmo.
*   **Quality Gate:**
    *   Passagem de código e arquitetura pelo `SonarQube MCP` antes de commits pro GitHub, enviando relatórios formais via `Notion MCP`.
