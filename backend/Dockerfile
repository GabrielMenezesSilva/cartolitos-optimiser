# Usa a imagem oficial do Python restrita e leve
FROM python:3.12-slim

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia os arquivos de dependência
COPY requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY . .

# Expõe a porta que o Render fornece via PORT env var, ou 8000 default
EXPOSE 8000

# Comando para rodar a aplicação usando Uvicorn, lendo a porta dinâmica do Render
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
