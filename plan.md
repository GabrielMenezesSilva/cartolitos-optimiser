# Cartolitos Optimiser - Technical Plan (Phase 1)

## 1. Visão Geral da Arquitetura (The Divine Stack)
A solução será baseada em uma arquitetura Serverless orientada a microsserviços, garantindo escalabilidade nos picos de fechamento do mercado.
*   **Frontend**: React (Vite) + TailwindCSS + Lucide Icons para renderizar o "Soccer Field" e os cards de justificativa ("Por que ele?").
*   **Backend / Solver**: Cloud Functions em Python 3.12+ (FastAPI) e Firebase (Firestore/Realtime Database). Cache utilizando Redis.
*   **Math Engine**: Biblioteca `PuLP` configurada para resolver o "Problema da Mochila Multi-Objetivo". 

## 2. Abordagem de Integração (Globo API Pipeline)
O fluxo de ingestão e autenticação foi projetado para contornar bloqueios (401/403) usando o protocolo **OIDC/JWT** estruturado para 2026.

### Autenticação Segura (OIDC/JWT)
1.  **Captura de Identidade**: O usuário deverá inserir credenciais seguras. A requisição inicial `POST` para `https://login.globo.com/api/authentication` conterá as credenciais e o `ServiceId: 438`.
2.  **Headers de Elite**: Todas as requisições autenticadas da aplicação embutirão:
    *   `User-Agent` customizado (rotacionável se necessário ou mimetizando browsers reais).
    *   `Content-Type: application/json`
    *   `X-GLB-Token` (obtido via cookie / jwt payload: o `glbId`).
3.  **Proxy / Webview (Fallback)**: Uso de injeção em app/WebView em cenários de persistência de cookie para capturar e renovar tokens de forma invisível.

### Escalação Automatizada (Auth API)
Uma vez com o `X-GLB-Token` válido:
*   A requisição de escalação faz o `POST` final para `/auth/time/salvar`.
*   O JSON Body enviado representará perfeitamente o esquema tático, banco de luxo e a identificação precisa do "Capitão" do time (peso 2x), todos mapeados pelas recomendações do Math Engine.

## 3. O Motor Matemático (Contexto & Risco via PuLP)
Modelado sobre Python (`PuLP`), a função de maximização buscará otimizar:
$$ Z = \sum (\\omega_i \cdot E[P_i] \cdot x_i) $$

### Variáveis e Parâmetros
*   **Variáveis Binárias ($x_i$)**: $1$ se o atleta $i$ é escalado, $0$ caso contrário.
*   **Multiplicadores Contextuais ($\\omega_i$)**: Baseado em probabilidades de SG (Odds implícitas > 60%), FDR (Dificuldade do adversário) e stats de xG/xA (Expected Goals/Assists) injetados via banco histórico próprio e Sportmonks API.

### Constraints (Restrições)
1.  **Formação Tática**: O número de $x_i$ por posição (ZAG, LAT, MEI, ATA, TEC) deve espelhar a formação escolhida (ex: 4-3-3).
2.  **Orçamento Máximo**: $\sum (Price_i \cdot x_i) \leq C$, onde $C$ são as cartoletas disponíveis.
3.  **Slider de Ousadia (1-10)**: Um parâmetro $\alpha$ que distribui os pesos entre o "piso de pontuação segura" e o "teto máximo (risco de negativação)".

### Lógica da Reserva de Luxo
Para o banco de reservas $R$, o sistema avaliará:
$$ \max (E[Teto_R]) \text{ sujeito a } Price_R \leq \min_{i \in Titulares, Pos_i=Pos_R}(Price_i) $$
Assegurando o substituto matemático de maior impacto caso um titular não inicie a partida (detecção via *The Panic Button* monitorando `status` do atleta no último minuto).

## 4. Backtesting & Validação
*   O sistema treinará um branch validando o modelo preditivo construído via ML usando base histórica aberta (`caRtola` com dados desde 2014) contra as "médias óbvias". 
*   **Aprovações QA**: Antes da recomendação, o motor validará cenários onde restam dúvidas sobre o goleiro / SG provável.

---
> **Aguardando aprovação ("Aprovado") para transição ao ambiente de execução (`@loki-mode -> Phase 2`).**
