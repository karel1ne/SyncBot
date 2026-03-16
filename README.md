# SyncBot — Telegram Message Mirroring Bot

A robust Telegram userbot built with Python 3.12 using the [Kurigram](https://github.com/Kurimuzard/kurigram) library (a Pyrogram fork). The bot automatically synchronizes messages and media groups between channels, with built-in support for bypassing content forwarding restrictions.

## Features

- **Real-time Mirroring:** Automatically copies messages from a source channel to a destination channel as they arrive.
- **Bypass Content Protection:** If the source channel has forwarding restricted (Content Protected), the bot automatically downloads the media and re-uploads it as a new message.
- **Media Group Support:** Correctly handles albums (photos, videos) while preserving captions and formatting.
- **History Synchronization:** On startup, the bot checks for missed messages (up to 100-200) to ensure no gaps occur during downtime.
- **State Persistence:** Uses `state.json` to track the last processed message and prevent duplicates.

## Technical Stack

- **Python:** 3.12+
- **Telegram Library:** `kurigram` (modern Pyrogram alternative)
- **Dependency Management:** `uv`
- **Configuration:** `pydantic-settings` (YAML/ENV support)
- **Logging:** `loguru`
- **Containerization:** Docker & Docker Compose

## Quick Start

### Prerequisites

1. Get your `API_ID` and `API_HASH` from [my.telegram.org](https://my.telegram.org).
2. Identify the IDs of your source and destination channels (or their usernames).
3. Install [uv](https://github.com/astral-sh/uv) (recommended for local development).

### Configuration

Create a `.env` file based on `.env.example`:

```env
API_ID=your_api_id
API_HASH=your_api_hash
SOURCE_CHANNEL=-100... or username
DEST_CHANNEL=-100... or username
# Optional:
SESSION_STRING=your_session_string
```

### Getting SESSION_STRING

If you plan to run the bot in Docker or on a remote server, it's easiest to use a `SESSION_STRING`. To generate one:

1. Fill in `API_ID` and `API_HASH` in your `.env`.
2. Run the helper script:
   ```bash
   uv run python get_session.py
   ```
3. Follow the instructions in your terminal. Copy the resulting string into your `.env` as `SESSION_STRING`.

### Local Run

1. **Install dependencies:**
   ```bash
   uv sync
   ```
2. **Start the bot:**
   ```bash
   uv run python -m syncbot
   ```
   *Note: On the first run (if `SESSION_STRING` is not provided), you will be prompted to log in via the terminal. This will create a `my_account.session` file.*

### Running with Docker

```bash
docker compose up -d --build
```
*For Docker usage, it is recommended to either provide a `SESSION_STRING` or mount your `my_account.session` file into the container.*

## Development and Testing

### Development Commands

- **Testing:** `uv run pytest`
- **Linting (Ruff):** `uv run ruff check src`
- **Formatting:** `uv run ruff format src`
- **Type Checking (Mypy):** `uv run mypy src`

### Project Structure

- `src/syncbot/`: Main application code.
    - `bot.py`: Main bot class and initialization logic.
    - `logic.py`: Core logic for message mirroring and restriction bypassing.
    - `handlers.py`: Telegram event handlers.
    - `config.py`: Configuration management via Pydantic.
    - `state.py`: State management (JSON).
- `state.json`: Stores the ID of the last processed message.
- `my_account.session`: Telegram session file (do not commit!).
- `get_session.py`: Script for generating `SESSION_STRING`.

## License

This project is intended for personal use. Please respect Telegram's Terms of Service and copyrights when mirroring content.
