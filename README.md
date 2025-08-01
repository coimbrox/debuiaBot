# Bot do Debuia Team

Um bot multifuncional para Discord, desenvolvido em Python, com funcionalidades de entretenimento e integração com a API de League of Legends e música.

---

### Funcionalidades

O bot responde aos seguintes comandos:

- **Comandos Gerais e de Entretenimento:**
  - `!ping`: Responde com `Pong!`, útil para verificar se o bot está online.
  - `!dica`: Fornece uma dica genérica de jogo.
  - `!lol-build`: Apresenta uma sugestão de build para um campeão de League of Legends.
  - `!debuia`: Uma frase de efeito do time.
  - `!piada`: Conta uma piada aleatória.

- **Comandos de Música:**
  - `!entrar`: Conecta o bot ao seu canal de voz.
  - `!sair`: Desconecta o bot do canal de voz.
  - `!tocar <URL>`: Toca uma música a partir de um link do YouTube.

- **Comandos de League of Legends (via API):**
  - `!elolol <nome_do_invocador>`: Retorna o elo e rank de um jogador.
  - `!historicolol <nome_do_invocador>`: Mostra o histórico das 5 partidas mais recentes do jogador.

---

### Instalação e Configuração

Siga estes passos para configurar e rodar o bot:

1.  **Pré-requisitos:**
    -   Instale o **Python 3.9** ou uma versão mais recente.
    -   Instale o **FFmpeg** e certifique-se de que ele esteja no PATH do seu sistema.

2.  **Clone o projeto:**
    ```bash
    git clone [https://stackoverflow.com/questions/67692712/for-git-is-it-absolutely-true-that-same-commit-hash-value-means-same-repository](https://stackoverflow.com/questions/67692712/for-git-is-it-absolutely-true-that-same-commit-hash-value-means-same-repository)
    cd [pasta do projeto]
    ```

3.  **Instale as dependências:**
    Abra o terminal na pasta do projeto e execute o comando:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuração do Bot e Chaves de API:**
    -   Crie um arquivo `.env` na mesma pasta do `bot.py`.
    -   Obtenha o seu token do Discord no [Portal de Desenvolvedores](https://discord.com/developers/applications) (na aba "Bot").
    -   Obtenha a sua chave da API da Riot no [Portal de Desenvolvedores da Riot](https://developer.riotgames.com/).
    -   Preencha o arquivo `.env` com suas chaves:
    ```
    DISCORD_TOKEN=seu_token_do_discord_aqui
    RIOT_API_KEY=sua_chave_da_riot_aqui
    ```

5.  **Adicionar o Bot ao seu Servidor:**
    -   Vá para a aba "OAuth2" -> "URL Generator" no Portal de Desenvolvedores do Discord.
    -   Selecione as permissões `bot` e `applications.commands`.
    -   Em "Bot Permissions", marque `Send Messages`, `Read Message History`, `Connect` e `Speak`.
    -   Copie o link gerado e use-o para adicionar o bot ao seu servidor.

---

### Como Rodar

Para iniciar o bot, execute o seguinte comando no terminal na pasta do projeto:

```bash
python bot.py