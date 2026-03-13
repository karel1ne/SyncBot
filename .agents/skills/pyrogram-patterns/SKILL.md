# Pyrogram Patterns Skill

## Description
Expertise in Pyrogram patterns for message handling, media groups, and Telegram API interaction.

## Instructions
When working with Pyrogram in this project, follow these established patterns:

### 1. Handling Media Groups
Media groups (albums) must be handled collectively using `message.media_group_id`.
- Use a `set` or similar to track processed group IDs and avoid redundant processing.
- Collect all messages in the group before attempting to mirror them.
- When mirroring media groups manually, download all parts to a temporary directory and use `client.send_media_group`.

### 2. Error Resilience
- Always wrap API calls that can fail (like `copy` or `download`) in a `try-except` block.
- Specifically handle `FloodWait` (sleep for the duration specified in the exception).
- Use `manual_copy` as a fallback when `CHAT_FORWARDS_RESTRICTED` is encountered.

### 3. File Cleanup
- Always clean up temporary files after `manual_copy` or `manual_copy_group` operations to prevent disk space exhaustion.

### 4. Logging
- Use `loguru` with context: `with logger.contextualize(message_id=message.id):`.
- Log clear messages for each step (downloading, uploading, success/failure).

## Available Resources
- `src/syncbot/logic.py`: Contains existing mirroring logic and fallbacks.
- `src/syncbot/utils.py`: Contains `safe_sleep` and observability helpers.
