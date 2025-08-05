#!/bin/bash

# Script para iniciar o bot Discord em segundo plano
# Autor: Gabriel Oliveira
# Data: 2023

# Verifica se o Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "Python 3 não está instalado. Instalando..."
    sudo yum install -y python3 python3-pip
fi

# Verifica se as dependências estão instaladas
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Verifica se o arquivo .env existe
if [ ! -f ".env" ]; then
    echo "Arquivo .env não encontrado. Criando um modelo..."
    echo "DISCORD_TOKEN=seu_token_aqui" > .env
    echo "RIOT_API_KEY=sua_chave_aqui" >> .env
    echo "Por favor, edite o arquivo .env com suas credenciais antes de continuar."
    exit 1
fi

# Verifica se o ffmpeg está instalado
if ! command -v ffmpeg &> /dev/null; then
    echo "ffmpeg não está instalado. Instalando..."
    sudo yum install -y ffmpeg
fi

# Inicia o bot em segundo plano usando nohup
echo "Iniciando o bot em segundo plano..."
nohup python3 bot.py > bot.log 2>&1 &

# Salva o PID para referência futura
echo $! > bot.pid
echo "Bot iniciado com PID $(cat bot.pid). Logs disponíveis em bot.log"
echo "Para parar o bot, execute: kill $(cat bot.pid)"