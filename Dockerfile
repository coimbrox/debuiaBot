# Use uma imagem oficial do Python como base
FROM python:3.11-slim

# Defina o diretório de trabalho dentro do container
WORKDIR /app

# Copie o arquivo de requisitos para o container e instale as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instale o FFmpeg (necessário para o bot de música)
# A imagem "slim" usa apt-get
RUN apt-get update && apt-get install -y ffmpeg

# Copie o restante dos arquivos do seu projeto para o container
COPY . .

# Comando para iniciar o seu bot
CMD ["python", "bot.py"]