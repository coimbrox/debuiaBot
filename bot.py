import discord
from discord.ext import commands
import random
import os
from dotenv import load_dotenv
import yt_dlp
import requests
import asyncio

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
intents.message_content = True
intents.voice_states = True
intents.members = True

# Cria uma instância do bot, SEM prefixo de comando
client = commands.Bot(command_prefix="!", intents=intents)
# A classe commands.Bot já cria uma CommandTree, então a linha 'tree = ...' foi removida.


# Evento de inicialização
@client.event
async def on_ready():
    # Sincroniza os slash commands com o Discord usando client.tree
    await client.tree.sync()
    print(f"Bot logado como {client.user}")
    print("------")


# --- Comandos de texto e entretenimento (Convertidos para Slash Commands) ---


@client.tree.command(name="ping", description="Responde com Pong!")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")


@client.tree.command(name="dica", description="Fornece uma dica de League of Legends.")
async def dica(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Lembre-se de sempre comprar wards para ter visão do mapa!"
    )


@client.tree.command(name="lol-build", description="Sugere uma build para um campeão.")
async def lol_build(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Tryndamere: Gume do Infinito, Colhedor de Essência e Mata-Cráquens."
    )


@client.tree.command(name="debuia", description="Exibe a frase de efeito do time.")
async def debuia(interaction: discord.Interaction):
    await interaction.response.send_message("Mesmo na derrota vamos debuiaaa!")


@client.tree.command(name="piada", description="Conta uma piada aleatória.")
async def piada(interaction: discord.Interaction):
    piadas = [
        "O que o tomate foi fazer no banco? Foi tirar um extrato!",
        "O que o pato disse para a pata? Vem Quá!",
        "Por que a aranha é o animal mais inteligente da floresta? Porque ela tem uma teia de ideias!",
    ]
    piada_escolhida = random.choice(piadas)
    await interaction.response.send_message(piada_escolhida)


# --- Comandos de voz (música) (Convertidos para Slash Commands) ---
# --- Comandos de voz (música) (Convertidos para Slash Commands) ---

# Fila de músicas e outras variáveis de controle
song_queue = {}
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


def play_next(ctx):
    if ctx.guild.id in song_queue and song_queue[ctx.guild.id]:
        # Pega a próxima música da fila
        next_song = song_queue[ctx.guild.id].pop(0)

        # Reproduz a próxima música
        source = discord.FFmpegPCMAudio(next_song["filename"])
        ctx.voice_client.play(
            source,
            after=lambda e: (
                play_next(ctx) if not e else print("Erro na reprodução:", e)
            ),
        )

        # Envia uma mensagem informando qual música está tocando
        coro = ctx.channel.send(f'Tocando agora: **{next_song["title"]}**')
        client.loop.create_task(coro)


@client.tree.command(name="sair", description="Desconecta o bot do canal de voz.")
async def sair(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        # Limpa a fila ao sair, se ela existir
        if interaction.guild.id in song_queue:
            song_queue[interaction.guild.id] = []
        await interaction.response.send_message("Desconectado do canal de voz.")
    else:
        await interaction.response.send_message(
            "O bot não está conectado a um canal de voz."
        )


@client.tree.command(name="tocar", description="Toca uma música do YouTube.")
async def tocar(interaction: discord.Interaction, url: str):
    await interaction.response.defer()

    if not interaction.guild.voice_client:
        if not interaction.user.voice:
            await interaction.followup.send(
                f"{interaction.user.name} não está conectado a um canal de voz!"
            )
            return
        try:
            voice_client = await interaction.user.voice.channel.connect()
            await interaction.followup.send(
                f"Conectado ao canal de voz **{interaction.user.voice.channel.name}** e preparando a música..."
            )
        except discord.ClientException:
            await interaction.followup.send("Já estou conectado a um canal de voz.")
            return
    else:
        voice_client = interaction.guild.voice_client

    try:
        info = await asyncio.to_thread(ydl.extract_info, url, download=False)

        if "entries" in info:
            # É uma playlist
            await interaction.followup.send(
                f'Encontrei a playlist **{info.get("title", "Playlist")}**. Adicionando as músicas à fila...'
            )
            for entry in info["entries"]:
                sanitized_info = await asyncio.to_thread(ydl.sanitize_info, entry)
                filename = ydl.prepare_filename(sanitized_info)

                # Adiciona cada música à fila
                if interaction.guild.id not in song_queue:
                    song_queue[interaction.guild.id] = []
                song_queue[interaction.guild.id].append(
                    {
                        "filename": filename,
                        "title": sanitized_info.get("title", "Música"),
                    }
                )

            # Se a reprodução não estiver em andamento, inicia a primeira música da fila
            if not voice_client.is_playing():
                play_next(interaction)

        else:
            # É uma única música
            sanitized_info = await asyncio.to_thread(ydl.sanitize_info, info)
            filename = ydl.prepare_filename(sanitized_info)

            if voice_client.is_playing():
                if interaction.guild.id not in song_queue:
                    song_queue[interaction.guild.id] = []
                song_queue[interaction.guild.id].append(
                    {
                        "filename": filename,
                        "title": sanitized_info.get("title", "Música"),
                    }
                )
                await interaction.followup.send(
                    f'**{sanitized_info.get("title", "Música")}** adicionada à fila.'
                )
            else:
                await asyncio.to_thread(ydl.download, [url])
                source = discord.FFmpegPCMAudio(filename)
                voice_client.play(
                    source,
                    after=lambda e: (
                        play_next(interaction)
                        if not e
                        else print("Erro na reprodução:", e)
                    ),
                )
                await interaction.followup.send(
                    f'Tocando agora: **{sanitized_info.get("title", "Música")}**'
                )

    except Exception as e:
        print(f"Ocorreu um erro no comando /tocar: {e}")
        await interaction.followup.send(
            f"Ocorreu um erro ao tentar tocar a música: {e}"
        )


@client.tree.command(name="parar", description="Para a música e limpa a fila.")
async def parar(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        interaction.guild.voice_client.stop()
        if interaction.guild.id in song_queue:
            song_queue[interaction.guild.id] = []
        await interaction.response.send_message("Música parada e fila limpa.")
    else:
        await interaction.response.send_message(
            "O bot não está conectado a um canal de voz."
        )


@client.tree.command(name="skip", description="Pula para a próxima música da fila.")
async def skip(interaction: discord.Interaction):
    if (
        interaction.guild.voice_client
        and interaction.guild.id in song_queue
        and song_queue[interaction.guild.id]
    ):
        await interaction.response.send_message("Pulando para a próxima música.")
        interaction.guild.voice_client.stop()
    elif (
        interaction.guild.voice_client
        and interaction.guild.id in song_queue
        and not song_queue[interaction.guild.id]
    ):
        await interaction.response.send_message("Não há mais músicas na fila.")
    else:
        await interaction.response.send_message(
            "O bot não está tocando música ou não está em um canal de voz."
        )


# --- Comandos de integração com a API da Riot (Convertidos para Slash Commands) ---


@client.tree.command(
    name="historicolol",
    description="Mostra o histórico das 5 partidas mais recentes de um invocador.",
)
async def lol_match(interaction: discord.Interaction, summoner_name: str):
    summoner_url = f"https://br1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}?api_key={riot_api_key}"

    await interaction.response.send_message(
        f"Buscando as últimas 5 partidas de **{summoner_name}**..."
    )

    try:
        response = requests.get(summoner_url)
        response.raise_for_status()
        summoner_data = response.json()

        puuid = summoner_data["puuid"]

        match_history_url = f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=5&api_key={riot_api_key}"
        match_history_response = requests.get(match_history_url)
        match_ids = match_history_response.json()

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

            await interaction.channel.send(
                f"**{champion}** - **{outcome}** - KDA: **{kda}**"
            )

    except requests.exceptions.HTTPError as err:
        if response.status_code == 404:
            await interaction.channel.send(
                f"Invocador **{summoner_name}** não encontrado."
            )
        else:
            await interaction.channel.send(
                f"Ocorreu um erro na requisição à API da Riot: {err}"
            )
    except Exception as e:
        await interaction.channel.send(f"Ocorreu um erro: {e}")


@client.tree.command(name="elolol", description="Retorna o elo e rank de um jogador.")
async def lol_rank(interaction: discord.Interaction, summoner_name: str):
    summoner_url = f"https://br1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}?api_key={riot_api_key}"

    await interaction.response.defer()  # Usado para evitar timeout

    try:
        response = requests.get(summoner_url)
        response.raise_for_status()
        summoner_data = response.json()

        summoner_id = summoner_data["id"]

        rank_url = f"https://br1.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}?api_key={riot_api_key}"
        rank_response = requests.get(rank_url)
        rank_data = rank_response.json()

        if not rank_data:
            await interaction.followup.send(
                f"O invocador **{summoner_name}** não tem rank em filas ranqueadas."
            )
        else:
            rank_info = rank_data[0]
            tier = rank_info["tier"].capitalize()
            rank = rank_info["rank"]
            lp = rank_info["leaguePoints"]
            wins = rank_info["wins"]
            losses = rank_info["losses"]

            await interaction.followup.send(
                f"**{summoner_name}** está em **{tier} {rank}** com **{lp} LP**. ({wins} Vitórias / {losses} Derrotas)"
            )

    except requests.exceptions.HTTPError as err:
        if response.status_code == 404:
            await interaction.followup.send(
                f"Invocador **{summoner_name}** não encontrado."
            )
        else:
            await interaction.followup.send(
                f"Ocorreu um erro na requisição à API da Riot: {err}"
            )
    except Exception as e:
        await interaction.followup.send(f"Ocorreu um erro: {e}")


@client.tree.command(
    name="lol-live",
    description="Mostra os jogadores e campeões de uma partida em andamento.",
)
async def lol_live(interaction: discord.Interaction, summoner_name: str):
    summoner_url = f"https://br1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}?api_key={riot_api_key}"

    await interaction.response.defer()  # Usado para evitar timeout

    try:
        response = requests.get(summoner_url)
        response.raise_for_status()
        summoner_data = response.json()

        summoner_id = summoner_data["id"]

        live_game_url = f"https://br1.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/{summoner_id}?api_key={riot_api_key}"
        live_game_response = requests.get(live_game_url)

        if live_game_response.status_code == 404:
            await interaction.followup.send(
                f"O invocador **{summoner_name}** não está em uma partida ativa."
            )
            return

        live_game_response.raise_for_status()
        game_data = live_game_response.json()

        game_mode = game_data["gameMode"]

        blue_team = ""
        red_team = ""

        for participant in game_data["participants"]:
            player_name = participant["summonerName"]
            champion_name = participant["championName"]

            if participant["teamId"] == 100:
                blue_team += f" - {player_name} ({champion_name})\n"
            else:
                red_team += f" - {player_name} ({champion_name})\n"

        embed = discord.Embed(
            title=f"Partida em Andamento ({game_mode})", color=discord.Color.blue()
        )
        embed.add_field(name="Time Azul", value=blue_team, inline=False)
        embed.add_field(name="Time Vermelho", value=red_team, inline=False)

        await interaction.followup.send(embed=embed)

    except requests.exceptions.HTTPError as err:
        if response.status_code == 404:
            await interaction.followup.send(
                f"Invocador **{summoner_name}** não encontrado."
            )
        else:
            await interaction.followup.send(
                f"Ocorreu um erro na requisição à API da Riot: {err}"
            )
    except Exception as e:
        await interaction.followup.send(f"Ocorreu um erro: {e}")


@client.tree.command(
    name="comandos", description="Exibe a lista de todos os comandos do bot."
)
async def comandos(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 Comandos do Bot Debuia Team",
        description="Lista de todas as funcionalidades disponíveis.",
        color=discord.Color.gold(),
    )

    embed.add_field(
        name="🎮 Comandos de League of Legends",
        value=(
            "**`/elolol <nome>`**\n"
            "   - Retorna o elo e rank de um jogador.\n"
            "**`/historicolol <nome>`**\n"
            "   - Mostra o histórico das 5 partidas mais recentes.\n"
            "**`/lol-live <nome>`**\n"
            "   - Mostra os jogadores e campeões de uma partida em andamento."
        ),
        inline=False,
    )

    embed.add_field(
        name="🎵 Comandos de Música",
        value=(
            "**`/entrar`**\n"
            "   - Conecta o bot ao seu canal de voz.\n"
            "**`/sair`**\n"
            "   - Desconecta o bot do canal de voz.\n"
            "**`/tocar <url>`**\n"
            "   - Toca uma música do YouTube."
        ),
        inline=False,
    )

    embed.add_field(
        name="🎲 Comandos de Entretenimento",
        value=(
            "**`/ping`**\n"
            "   - Responde com `Pong!`.\n"
            "**`/piada`**\n"
            "   - Conta uma piada aleatória.\n"
            "**`/debuia`**\n"
            "   - Exibe a frase de efeito do time.\n"
            "**`/lol-build`**\n"
            "   - Fornece um exemplo de build para um campeão."
        ),
        inline=False,
    )

    await interaction.response.send_message(embed=embed)


keep_alive()
# Rodar o bot
token = os.getenv("DISCORD_TOKEN")
client.run(token)
