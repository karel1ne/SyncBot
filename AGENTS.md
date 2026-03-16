# SyncBot - Telegram Mirror Userbot

A robust Telegram message mirroring userbot built with Python 3.12 and [Kurigram](https://github.com/Kurimuzard/kurigram) (a modern Pyrogram fork). It synchronizes messages and media groups between channels, with built-in support for bypassing forward restrictions.

## Project Overview

*   **Purpose:** Automatically copy/mirror messages from a source Telegram channel to a destination channel using your own account.
*   **Key Feature:** Bypasses "Content Protected" (forwarding restricted) channels by downloading media and re-uploading it as new messages.
*   **State Management:** Tracks progress using `state.json` to avoid duplicate messages during restarts.
*   **Media Handling:** Supports single messages (text, photo, video, document, etc.) and Media Groups (albums), preserving captions and entities.

## Technical Stack

*   **Python:** 3.12+
*   **Telegram Library:** `kurigram` (Pyrogram fork)
*   **Dependency Management:** `uv`
*   **Configuration:** `pydantic-settings` (YAML and ENV support)
*   **Logging:** `loguru`
*   **Containerization:** Docker & Docker Compose
*   **Quality Tools:** Ruff (linting/formatting), Mypy (strict type checking), Pytest (testing)

## Getting Started

### Prerequisites

*   Telegram API ID and API Hash (from [my.telegram.org](https://my.telegram.org)).
*   Source and Destination channel IDs (or usernames).
*   `uv` installed locally (recommended).

### Configuration

Create a `.env` file based on `.env.example`:

```env
API_ID=your_api_id
API_HASH=your_api_hash
SOURCE_CHANNEL=-100... or username
DEST_CHANNEL=-100... or username
# Optional:
SESSION_STRING=optional_string_session
```

### Getting SESSION_STRING

To run in Docker or on a remote server without interactive login:
1.  Fill `API_ID` and `API_HASH` in `.env`.
2.  Run the helper script:
    ```bash
    uv run python get_session.py
    ```
3.  Follow the prompts and copy the resulting string to your `.env` as `SESSION_STRING`.

### Running Locally

1.  **Install dependencies:**
    ```bash
    uv sync
    ```
2.  **Start the userbot:**
    ```bash
    uv run python -m syncbot
    ```
    *Note: On first run (if SESSION_STRING is not provided), you will be prompted to log in to your Telegram account. This creates a `my_account.session` file.*

### Running with Docker

```bash
docker compose up -d --build
```
*Note: Use `SESSION_STRING` in `.env` for seamless Docker deployment.*

## Development

### Commands

*   **Test:** `uv run pytest`
*   **Lint:** `uv run ruff check src`
*   **Format:** `uv run ruff format src`
*   **Type Check:** `uv run mypy src`

### Key Files

*   `src/syncbot/`: Main package directory.
    *   `__main__.py`: Entry point.
    *   `bot.py`: Core userbot class (SyncBot).
    *   `config.py`: Configuration management (Pydantic).
    *   `handlers.py`: Message handlers.
    *   `logic.py`: Mirroring logic (manual copy, etc.).
    *   `state.py`: Persistence (state.json).
    *   `utils.py`: Helpers.
*   `state.json`: Persists the ID of the last processed message.
*   `get_session.py`: Script for generating `SESSION_STRING`.
*   `my_account.session`: Stores Telegram session credentials.
*   `pyproject.toml`: Project configuration and dependencies.
*   `tests/`: Comprehensive test suite using `pytest-asyncio` and mocks.

## Implementation Details

*   **History Sync:** On startup, the userbot checks `state.json` and fetches missed messages from the source channel (default limit 100-200).
*   **Manual Copy Fallback:** If `copy_message` fails with `CHAT_FORWARDS_RESTRICTED`, the userbot invokes `manual_copy` (or `manual_copy_group`), which downloads the media to a temporary file and sends it to the destination chat.
*   **Logging:** Detailed logs are saved to `bot.log` with rotation (10MB) and retention (7 days).
