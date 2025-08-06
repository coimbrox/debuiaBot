import discord
from discord.ext import commands
import random
import os
from dotenv import load_dotenv
import yt_dlp
import requests
import asyncio
import time
from googletrans import Translator

from flask import Flask
from threading import Thread

# --- Replit: Mantém o bot online ---
app = Flask(__name__)


@app.route("/")
def home():
    return "Olá, o bot está online!"


def run():
    app.run(host="0.0.0.0", port=8080)


def keep_alive():
    t = Thread(target=run)
    t.start()


# --- Configurações Iniciais ---
load_dotenv()
riot_api_key = os.getenv("RIOT_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Configuração de intenções
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

# Cria uma instância do bot
client = commands.Bot(command_prefix="!", intents=intents)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/115.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://lolalytics.com/",
}


# --- Funções Auxiliares para a API da Riot (síncronas) ---
def get_riot_api_data_sync(url: str):
    """Função síncrona para fazer requisições à API da Riot."""
    response = requests.get(url)
    if response.status_code == 429:
        print("Erro 429: Limite de requisições excedido. Aguardando 10 segundos...")
        time.sleep(10)
        return get_riot_api_data_sync(url)
    response.raise_for_status()
    return response.json()


# Evento de inicialização
@client.event
async def on_ready():
    await client.tree.sync()
    print(f"Bot logado como {client.user}")
    print("------")


# --- Comandos de texto e entretenimento ---
@client.tree.command(name="ping", description="Responde com Pong!")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")


@client.tree.command(name="dica", description="Fornece uma dica de League of Legends.")
async def dica(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Lembre-se de sempre comprar wards para ter visão do mapa!"
    )


@client.tree.command(
    name="curiosidade", description="Mostra uma curiosidade aleatória."
)
async def curiosidade(interaction: discord.Interaction):
    await interaction.response.defer()
    try:

        def fetch_fact():
            api_url = "https://uselessfacts.jsph.pl/random.json"
            response = requests.get(api_url)
            response.raise_for_status()
            return response.json()["text"]

        fato_ingles = await asyncio.to_thread(fetch_fact)
        translator = Translator()
        fato_traduzido = translator.translate(fato_ingles, dest="pt").text

        embed = discord.Embed(
            title="🧠 Curiosidade do Dia 🧠",
            description=fato_traduzido,
            color=discord.Color.teal(),
        )
        embed.set_footer(text="Fonte: uselessfacts.jsph.pl")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(f"Ocorreu um erro ao buscar curiosidade: {e}")
        await interaction.followup.send(
            "Ocorreu um erro ao tentar buscar uma curiosidade."
        )


cidades = {
    "Tokyo": "Asia/Tokyo",
    "Londres": "Europe/London",
    "Nova York": "America/New_York",
    "São Paulo": "America/Sao_Paulo",
    "Dubai": "Asia/Dubai",
    "Sydney": "Australia/Sydney",
    "Paris": "Europe/Paris",
}


@client.tree.command(
    name="timeguesser",
    description="Tente adivinhar a hora atual em uma cidade aleatória.",
)
async def time_guesser(interaction: discord.Interaction):
    await interaction.response.defer()
    cidade, timezone = random.choice(list(cidades.items()))

    embed_pergunta = discord.Embed(
        title="⏰ Timeguesser!",
        description=f"Qual é a hora atual em **{cidade}**? (Responda em formato HH:MM)",
        color=discord.Color.purple(),
    )
    await interaction.followup.send(embed=embed_pergunta)

    def check(m):
        return m.author == interaction.user and m.channel == interaction.channel

    try:

        def fetch_time(timezone_name):
            api_url = f"http://worldtimeapi.org/api/timezone/{timezone_name}"
            response = requests.get(api_url)
            response.raise_for_status()
            return response.json()["datetime"]

        resposta_usuario = await client.wait_for("message", check=check, timeout=30.0)
        palpite_texto = resposta_usuario.content

        palpite_valido = False
        try:
            hora_palpite, minuto_palpite = map(int, palpite_texto.split(":"))
            if 0 <= hora_palpite <= 23 and 0 <= minuto_palpite <= 59:
                palpite_valido = True
        except ValueError:
            pass

        if not palpite_valido:
            await interaction.channel.send(
                "Palpite inválido. Por favor, use o formato HH:MM."
            )
            return

        hora_correta_iso = await asyncio.to_thread(fetch_time, timezone)
        hora_correta = hora_correta_iso[11:16]
        hora_certa_hora, hora_certa_minuto = map(int, hora_correta.split(":"))

        if hora_palpite == hora_certa_hora and minuto_palpite == hora_certa_minuto:
            resultado = f"🎉 **Parabéns!** Você acertou! A hora exata em {cidade} é **{hora_correta}**."
        else:
            resultado = f"😔 Você errou. A hora exata em {cidade} é **{hora_correta}**."

        await interaction.channel.send(resultado)

    except asyncio.TimeoutError:
        await interaction.channel.send("O tempo acabou! Ninguém respondeu a tempo.")
    except Exception as e:
        print(f"Ocorreu um erro no jogo: {e}")
        await interaction.channel.send("Ocorreu um erro ao buscar a hora correta.")


@client.tree.command(
    name="dado", description="Rola um dado com o número de lados especificado."
)
async def dado(interaction: discord.Interaction, lados: int):
    if lados < 1:
        await interaction.response.send_message(
            "O número de lados deve ser pelo menos 1.", ephemeral=True
        )
        return
    resultado = random.randint(1, lados)
    await interaction.response.send_message(
        f"🎲 Você rolou um dado de {lados} lados e tirou **{resultado}**!"
    )


respostas = [
    "Sim, com certeza.",
    "É certo.",
    "Sem dúvida.",
    "Sim.",
    "Você pode contar com isso.",
    "Provavelmente.",
    "A resposta está nebulosa, tente novamente.",
    "Pergunte mais tarde.",
    "Não posso prever agora.",
    "Não conte com isso.",
    "Minhas fontes dizem não.",
    "Não parece bom.",
    "Muito duvidoso.",
    "Não.",
]


@client.tree.command(
    name="8ball", description="Responde a uma pergunta com uma resposta aleatória."
)
async def magic_8ball(interaction: discord.Interaction, pergunta: str):
    await interaction.response.send_message(
        f"🎱 **{pergunta}**\n**Resposta:** {random.choice(respostas)}"
    )


@client.tree.command(
    name="ship", description="Calcula a compatibilidade entre duas pessoas."
)
async def ship(interaction: discord.Interaction, nome1: str, nome2: str):
    await interaction.response.defer()
    metade1 = nome1[: len(nome1) // 2]
    metade2 = nome2[len(nome2) // 2 :]
    nome_do_navio = metade1 + metade2
    compatibilidade = random.randint(0, 100)

    embed = discord.Embed(
        title="💘 Análise de Compatibilidade 💘",
        description=f"O nome do navio é **{nome_do_navio.capitalize()}**!",
        color=discord.Color.brand_red(),
    )
    embed.add_field(
        name="Pessoas",
        value=f"{nome1.capitalize()} e {nome2.capitalize()}",
        inline=False,
    )
    embed.add_field(
        name="Nível de Compatibilidade", value=f"**{compatibilidade}%**", inline=False
    )
    embed.set_image(url="https://i.imgur.com/gYj7R2z.png")

    await interaction.followup.send(embed=embed)


@client.tree.command(
    name="lol-build", description="Sugere uma build para um campeão e lane."
)
async def lol_build(interaction: discord.Interaction, champion: str, lane: str):
    await interaction.response.defer()
    try:

        def fetch_build_sync(champion_name, lane_name):
            champion_lower = champion_name.lower()
            lane_lower = lane_name.lower()
            url = f"https://lolalytics.com/api/lol/{champion_lower}/build/?lane={lane_lower}&tier=platinum_plus&patch=14.14"
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()

        data = await asyncio.to_thread(fetch_build_sync, champion, lane)

        if "items" not in data or "core" not in data["items"]:
            await interaction.followup.send(
                f"Não encontrei dados para **{champion.capitalize()}** na lane **{lane}**."
            )
            return

        core_items = data["items"]["core"]["items"][:3]
        item_names = ", ".join([item["name"] for item in core_items])
        await interaction.followup.send(
            f"**{champion.capitalize()} ({lane.capitalize()})**: {item_names}"
        )

    except Exception as e:
        await interaction.followup.send(
            f"Erro ao buscar build para {champion} ({lane}): {e}"
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


# --- Comandos de voz (música) - NÃO FUNCIONA NO REPLIT! ---
FFMPEG_EXECUTABLE = (
    "/nix/store/15alrig3q4xjwfc3rbnsgj4bj29zn6ww-ffmpeg-7.1.1-bin/bin/ffmpeg"
)
YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "default_search": "ytsearch",
    "quiet": True,
    "extract_flat": "in_playlist",
    "force-ipv4": True,
}
song_queue = {}


class YTDLSource(discord.PCMVolumeTransformer):

    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get("title")
        self.url = data.get("url")

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await asyncio.to_thread(
            yt_dlp.YoutubeDL(YTDL_OPTIONS).extract_info, url, download=not stream
        )
        if "entries" in data:
            data = data["entries"][0]
        filename = (
            data["url"]
            if stream
            else yt_dlp.YoutubeDL(YTDL_OPTIONS).prepare_filename(data)
        )
        return cls(
            discord.FFmpegPCMAudio(
                filename,
                executable=FFMPEG_EXECUTABLE,
                before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            ),
            data=data,
        )


async def play_next_async(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    if guild_id in song_queue and song_queue[guild_id]:
        next_song = song_queue[guild_id].pop(0)
        try:
            player = await YTDLSource.from_url(
                next_song["url"], loop=client.loop, stream=True
            )
            interaction.guild.voice_client.play(
                player,
                after=lambda e: (
                    client.loop.create_task(play_next_async(interaction))
                    if not e
                    else print("Erro na reprodução:", e)
                ),
            )
            await interaction.channel.send(f"Tocando agora: **{player.title}**")
        except Exception as e:
            print(f"Erro ao tentar reproduzir a música: {e}")
            await interaction.channel.send(
                f"Ocorreu um erro ao tocar a música: **{next_song['title']}**"
            )
            await play_next_async(interaction)


@client.tree.command(name="musica", description="Toca uma música do YouTube.")
async def musica(interaction: discord.Interaction, url: str):
    await interaction.response.defer()
    if not interaction.user.voice:
        await interaction.followup.send("Entra na Desgraça da sala pra pedir musica!")
        return

    voice_client = interaction.guild.voice_client
    if not voice_client:
        try:
            voice_client = await interaction.user.voice.channel.connect()
        except discord.ClientException:
            await interaction.followup.send("Já estou conectado a um canal de voz.")
            return

    try:
        if voice_client.is_playing():
            if interaction.guild.id not in song_queue:
                song_queue[interaction.guild.id] = []
            song_queue[interaction.guild.id].append(
                {"url": url, "title": "Carregando..."}
            )
            await interaction.followup.send(f"Música adicionada à fila.")
        else:
            player = await YTDLSource.from_url(url, loop=client.loop, stream=True)
            voice_client.play(
                player,
                after=lambda e: (
                    client.loop.create_task(play_next_async(interaction))
                    if not e
                    else print("Erro na reprodução:", e)
                ),
            )
            await interaction.followup.send(f"Tocando agora: **{player.title}**")

    except Exception as e:
        print(f"Ocorreu um erro no comando /musica: {e}")
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
        await interaction.response.send_message(
            "Se não tem música, vc que que eu pule oq? sua mãe?"
        )
    else:
        await interaction.response.send_message(
            "O bot não está tocando música ou não está em um canal de voz."
        )


@client.tree.command(name="sair", description="Desconecta o bot do canal de voz.")
async def sair(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        if interaction.guild.id in song_queue:
            song_queue[interaction.guild.id] = []
        await interaction.response.send_message("Desconectado do canal de voz.")
    else:
        await interaction.response.send_message(
            "O bot não está conectado a um canal de voz."
        )


# --- Comandos de integração com a API da Riot (síncronos, com to_thread) ---
@client.tree.command(
    name="historicolol",
    description="Mostra o histórico das 5 partidas mais recentes de um invocador.",
)
async def lol_match(interaction: discord.Interaction, summoner_name: str):
    await interaction.response.defer()
    try:
        puuid, match_ids = await asyncio.to_thread(
            lambda: (
                get_riot_api_data_sync(
                    f"https://br1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}?api_key={riot_api_key}"
                )["puuid"],
                get_riot_api_data_sync(
                    f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=5&api_key={riot_api_key}"
                ),
            )
        )
        await interaction.followup.send(
            f"Buscando as últimas 5 partidas de **{summoner_name}**..."
        )

        for match_id in match_ids:
            match_data = await asyncio.to_thread(
                get_riot_api_data_sync,
                f"https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={riot_api_key}",
            )
            jogador = next(
                (p for p in match_data["info"]["participants"] if p["puuid"] == puuid),
                None,
            )
            if jogador:
                outcome = "Vitória" if jogador["win"] else "Derrota"
                champion = jogador["championName"]
                kda = f"{jogador['kills']}/{jogador['deaths']}/{jogador['assists']}"
                await interaction.channel.send(
                    f"**{champion}** - **{outcome}** - KDA: **{kda}**"
                )
            await asyncio.sleep(1)

    except requests.exceptions.HTTPError as err:
        if err.response.status_code == 404:
            await interaction.followup.send(
                f"Invocador **{summoner_name}** não encontrado."
            )
        else:
            await interaction.followup.send(
                f"Ocorreu um erro na requisição à API da Riot: {err}"
            )
    except Exception as e:
        await interaction.followup.send(f"Ocorreu um erro: {e}")


@client.tree.command(name="elolol", description="Retorna o elo e rank de um jogador.")
async def lol_rank(interaction: discord.Interaction, summoner_name: str):
    await interaction.response.defer()
    try:

        def fetch_data():
            summoner_url = f"https://br1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}?api_key={riot_api_key}"
            summoner_data = get_riot_api_data_sync(summoner_url)
            summoner_id = summoner_data["id"]
            rank_url = f"https://br1.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}?api_key={riot_api_key}"
            return get_riot_api_data_sync(rank_url), summoner_name

        rank_data, summoner_name = await asyncio.to_thread(fetch_data)

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
        if err.response.status_code == 404:
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
    await interaction.response.defer()
    try:

        def fetch_data_sync():
            summoner_url = f"https://br1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}?api_key={riot_api_key}"
            summoner_data = get_riot_api_data_sync(summoner_url)
            summoner_id = summoner_data["id"]
            live_game_url = f"https://br1.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/{summoner_id}?api_key={riot_api_key}"
            live_game_response = requests.get(live_game_url)
            return live_game_response

        live_game_response = await asyncio.to_thread(fetch_data_sync)
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
        if err.response.status_code == 404:
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
    name="lol-freechamps", description="Mostra a rotação semanal de campeões grátis."
)
async def lol_freechamps(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        data = await asyncio.to_thread(
            get_riot_api_data_sync,
            f"https://br1.api.riotgames.com/lol/platform/v3/champion-rotations?api_key={riot_api_key}",
        )
        free_champ_ids = data.get("freeChampionIds", [])
        await interaction.followup.send(
            f"**IDs dos Campeões da semana:** {', '.join(map(str, free_champ_ids))}"
        )
    except requests.exceptions.HTTPError as err:
        await interaction.followup.send(
            f"Ocorreu um erro na requisição à API da Riot: {err}"
        )
    except Exception as e:
        await interaction.followup.send(f"Ocorreu um erro: {e}")


@client.tree.command(
    name="lol-top", description="Mostra o top 5 de uma fila ranqueada."
)
async def lol_top(interaction: discord.Interaction, queue: str):
    try:
        await interaction.response.defer()
    except discord.NotFound:
        # Interação expirou, não podemos fazer nada
        return
    except discord.HTTPException:
        # Outro erro HTTP, também não podemos continuar
        return

    try:

        def fetch_top_sync():
            queue_upper = queue.upper()
            url = f"https://br1.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/{queue_upper}?api_key={riot_api_key}"
            return get_riot_api_data_sync(url)

        data = await asyncio.to_thread(fetch_top_sync)
        entries = sorted(
            data["entries"], key=lambda e: e["leaguePoints"], reverse=True
        )[:5]
        message = f"**Top 5 da fila {queue.replace('_', ' ')} (Challenger):**\n"
        for i, entry in enumerate(entries):
            message += f"{i+1}. {entry['summonerName']} - {entry['leaguePoints']} LP\n"

        await interaction.followup.send(message)
    except discord.NotFound:
        # Se der erro no followup também, significa que a interação realmente expirou
        pass
    except requests.exceptions.HTTPError as err:
        if err.response.status_code == 404:
            await interaction.followup.send(
                f"Nenhum dado encontrado para a fila **{queue}**."
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
            "   - Mostra os jogadores e campeões de uma partida em andamento.\n"
            "**`/lol-freechamps`**\n"
            "   - Mostra a rotação semanal de campeões grátis.\n"
            "**`/lol-top <fila>`**\n"
            "   - Mostra o top 5 de jogadores em uma fila ranqueada."
        ),
        inline=False,
    )
    embed.add_field(
        name="🎵 Comandos de Música",
        value=(
            "**`/musica <url>`**\n"
            "   - Toca uma música do YouTube.\n"
            "**`/parar`**\n"
            "   - Para a música e limpa a fila.\n"
            "**`/skip`**\n"
            "   - Pula para a próxima música da fila.\n"
            "**`/sair`**\n"
            "   - Desconecta o bot do canal de voz."
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
            "**`/lol-build <champion> <lane>`**\n"
            "   - Fornece um exemplo de build para um campeão e lane.\n"
            "**`/8ball <pergunta>`**\n"
            "   - Responde a uma pergunta aleatória.\n"
            "**`/dado <lados>`**\n"
            "   - Rola um dado com o número de lados especificado.\n"
            "**`/ship <nome1> <nome2>`**\n"
            "   - Calcula a compatibilidade entre duas pessoas.\n"
            "**`/curiosidade`**\n"
            "   - Mostra uma curiosidade aleatória.\n"
            "**`/timeguesser`**\n"
            "   - Tente adivinhar a hora em uma cidade aleatória."
        ),
        inline=False,
    )
    await interaction.response.send_message(embed=embed)


keep_alive()
client.run(DISCORD_TOKEN)
