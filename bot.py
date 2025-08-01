import discord
from discord.ext import commands
import random
import os
from dotenv import load_dotenv
import yt_dlp
import requests

from flask import Flask
from threading import Thread

app = Flask(__name__)


@app.route("/")
def home():
    return "Olá, o bot está online!"


def run():
    app.run(host="0.0.0.0", port=8080)


def keep_alive():
    t = Thread(target=run)
    t.start()


# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()
riot_api_key = os.getenv("RIOT_API_KEY")

# Configuração de intenções
intents = discord.Intents.default()
intents.message_content = True  # Permite que o bot veja o conteúdo das mensagens
intents.voice_states = True  # Necessário para o bot de música

# Cria uma instância do bot, usando commands.Bot e definindo o prefixo para os comandos
client = commands.Bot(command_prefix="!", intents=intents)


# Evento de inicialização
@client.event
async def on_ready():
    print(f"Bot logado como {client.user}")
    print("------")


# Comandos de texto e entretenimento
@client.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong!")


@client.command(name="dica")
async def dica(ctx):
    await ctx.send("Lembre-se de sempre comprar wards para ter visão do mapa!")


@client.command(name="lol-build")
async def lol_build(ctx):
    await ctx.send(
        "Tryndamere: Gume do Infinito, Colhedor de Essência e Mata-Cráquens."
    )


@client.command(name="debuia")
async def debuia(ctx):
    await ctx.send("Mesmo na derrota vamos debuiaaa!")


@client.command(name="piada")
async def piada(ctx):
    piadas = [
        "O que o tomate foi fazer no banco? Foi tirar um extrato!",
        "O que o pato disse para a pata? Vem Quá!",
        "Por que a aranha é o animal mais inteligente da floresta? Porque ela tem uma teia de ideias!",
    ]
    piada_escolhida = random.choice(piadas)
    await ctx.send(piada_escolhida)


# Comandos de voz (música)
# Assegure-se de que o FFmpeg esteja instalado e no PATH do seu sistema.
ydl_opts = {
    "format": "bestaudio/best",
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
    "outtmpl": "song.%(ext)s",
}


@client.command(name="entrar")
async def entrar(ctx):
    if not ctx.message.author.voice:
        await ctx.send(
            f"{ctx.message.author.name} não está conectado a um canal de voz!"
        )
        return

    canal = ctx.message.author.voice.channel
    await canal.connect()
    await ctx.send(f"Conectado ao canal de voz **{canal.name}**.")


@client.command(name="sair")
async def sair(ctx):
    if ctx.voice_client:
        await ctx.guild.voice_client.disconnect()
        await ctx.send("Desconectado do canal de voz.")
    else:
        await ctx.send("O bot não está conectado a um canal de voz.")


@client.command(name="tocar")
async def tocar(ctx, *, url):
    if not ctx.voice_client:
        await ctx.send("O bot não está conectado a um canal de voz.")
        return

    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        source = discord.FFmpegPCMAudio(filename, executable="ffmpeg")
        ctx.voice_client.play(
            source, after=lambda e: print("Tocando música. Erro: %s" % e) if e else None
        )

        await ctx.send(f'Tocando agora: **{info.get("title", "Música")}**')

    except Exception as e:
        await ctx.send(f"Ocorreu um erro: {e}")


# Comandos de integração com a API da Riot
@client.command(name="historicolol")
async def lol_match(ctx, *, summoner_name):
    summoner_url = f"https://br1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}?api_key={riot_api_key}"

    try:
        response = requests.get(summoner_url)
        response.raise_for_status()
        summoner_data = response.json()

        puuid = summoner_data["puuid"]

        match_history_url = f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=5&api_key={riot_api_key}"
        match_history_response = requests.get(match_history_url)
        match_ids = match_history_response.json()

        await ctx.send(f"Buscando as últimas 5 partidas de **{summoner_name}**...")

        for match_id in match_ids:
            match_url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={riot_api_key}"
            match_response = requests.get(match_url)
            match_data = match_response.json()

            for participant in match_data["info"]["participants"]:
                if participant["puuid"] == puuid:
                    jogador = participant
                    break

            outcome = "Vitória" if jogador["win"] else "Derrota"
            champion = jogador["championName"]
            kda = f"{jogador['kills']}/{jogador['deaths']}/{jogador['assists']}"

            await ctx.send(f"**{champion}** - **{outcome}** - KDA: **{kda}**")

    except requests.exceptions.HTTPError as err:
        if response.status_code == 404:
            await ctx.send(f"Invocador **{summoner_name}** não encontrado.")
        else:
            await ctx.send(f"Ocorreu um erro na requisição à API da Riot: {err}")
    except Exception as e:
        await ctx.send(f"Ocorreu um erro: {e}")


import requests  # Certifique-se de que requests já está importado

# ... seu código existente ...


@client.command(name="lolaovivo")
async def lol_live(ctx, *, summoner_name):
    # Primeiro, busca o ID do invocador
    summoner_url = f"https://br1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}?api_key={riot_api_key}"

    try:
        response = requests.get(summoner_url)
        response.raise_for_status()
        summoner_data = response.json()

        summoner_id = summoner_data["id"]

        # Agora, usa o ID para checar a partida em tempo real
        live_game_url = f"https://br1.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/{summoner_id}?api_key={riot_api_key}"
        live_game_response = requests.get(live_game_url)

        if live_game_response.status_code == 404:
            await ctx.send(
                f"O invocador **{summoner_name}** não está em uma partida ativa."
            )
            return

        live_game_response.raise_for_status()
        game_data = live_game_response.json()

        # Constrói a mensagem com as informações da partida
        game_mode = game_data["gameMode"]

        await ctx.send(f"**{summoner_name}** está em uma partida de **{game_mode}**!")

        blue_team = ""
        red_team = ""

        for participant in game_data["participants"]:
            player_name = participant["summonerName"]
            champion_name = participant["championName"]

            # Formata a string para cada time
            if participant["teamId"] == 100:  # Time Azul
                blue_team += f" - {player_name} ({champion_name})\n"
            else:  # Time Vermelho
                red_team += f" - {player_name} ({champion_name})\n"

        embed = discord.Embed(
            title=f"Partida em Andamento ({game_mode})", color=discord.Color.blue()
        )
        embed.add_field(name="Time Azul", value=blue_team, inline=False)
        embed.add_field(name="Time Vermelho", value=red_team, inline=False)

        await ctx.send(embed=embed)

    except requests.exceptions.HTTPError as err:
        if response.status_code == 404:
            await ctx.send(f"Invocador **{summoner_name}** não encontrado.")
        else:
            await ctx.send(f"Ocorreu um erro na requisição à API da Riot: {err}")
    except Exception as e:
        await ctx.send(f"Ocorreu um erro: {e}")


@client.command(name="elolol")
async def lol_rank(ctx, *, summoner_name):
    summoner_url = f"https://br1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}?api_key={riot_api_key}"

    try:
        response = requests.get(summoner_url)
        response.raise_for_status()
        summoner_data = response.json()

        summoner_id = summoner_data["id"]

        rank_url = f"https://br1.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}?api_key={riot_api_key}"
        rank_response = requests.get(rank_url)
        rank_data = rank_response.json()

        if not rank_data:
            await ctx.send(
                f"O invocador **{summoner_name}** não tem rank em filas ranqueadas."
            )
        else:
            rank_info = rank_data[0]
            tier = rank_info["tier"].capitalize()
            rank = rank_info["rank"]
            lp = rank_info["leaguePoints"]
            wins = rank_info["wins"]
            losses = rank_info["losses"]

            await ctx.send(
                f"**{summoner_name}** está em **{tier} {rank}** com **{lp} LP**. ({wins} Vitórias / {losses} Derrotas)"
            )

    except requests.exceptions.HTTPError as err:
        if response.status_code == 404:
            await ctx.send(f"Invocador **{summoner_name}** não encontrado.")
        else:
            await ctx.send(f"Ocorreu um erro na requisição à API da Riot: {err}")
    except Exception as e:
        await ctx.send(f"Ocorreu um erro: {e}")


# Adicione este comando no seu arquivo bot.py
@client.command(name="comandos")
async def comandos(ctx):
    embed = discord.Embed(
        title="🤖 Comandos do Bot Debuia Team",
        description="Lista de todas as funcionalidades disponíveis.",
        color=discord.Color.gold(),
    )

    # Adicionando os campos de funcionalidades
    embed.add_field(
        name="🎮 Comandos de League of Legends",
        value=(
            "**`!elolol <nome_do_invocador>`**\n"
            "   - Retorna o elo e rank de um jogador.\n"
            "**`!historicolol <nome_do_invocador>`**\n"
            "   - Mostra o histórico das 5 partidas mais recentes.\n"
            "**`!lol-live <nome_do_invocador>`**\n"
            "   - Mostra os jogadores e campeões de uma partida em andamento."
        ),
        inline=False,
    )

    embed.add_field(
        name="🎵 Comandos de Música",
        value=(
            "**`!entrar`**\n"
            "   - Conecta o bot ao seu canal de voz.\n"
            "**`!sair`**\n"
            "   - Desconecta o bot do canal de voz.\n"
            "**`!tocar <URL>`**\n"
            "   - Toca uma música do YouTube."
        ),
        inline=False,
    )

    embed.add_field(
        name="🎲 Comandos de Entretenimento",
        value=(
            "**`!ping`**\n"
            "   - Responde com `Pong!`.\n"
            "**`!piada`**\n"
            "   - Conta uma piada aleatória.\n"
            "**`!debuia`**\n"
            "   - Exibe a frase de efeito do time.\n"
            "**`!lol-build`**\n"
            "   - Fornece um exemplo de build para um campeão."
        ),
        inline=False,
    )

    # Envia a mensagem embed no canal
    await ctx.send(embed=embed)


keep_alive()
# Rodar o bot
token = os.getenv("DISCORD_TOKEN")
client.run(token)
