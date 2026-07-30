# Discord Bot

Python Discord bot using `discord.py` plus a small Flask keep-alive web server.

## Run

```bash
python bot/main.py
```

Requires `DISCORD_BOT_TOKEN` env var.

## Commands

- `!ping` / `/ping` — show latency
- `!hello` / `/hello` — greet the user

## Endpoints

- `GET /` — bot status JSON
- `GET /health` — health check
