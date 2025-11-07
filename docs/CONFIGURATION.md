# Configuration Guide

The bot is configured using environment variables. Create a `.env` file in the project root by copying the `.env.example` file.

```bash
cp .env.example .env
```

Below is a detailed explanation of each variable.

## Core Configuration

### `TELEGRAM_BOT_TOKEN` (Required)

-   **Description**: The authentication token for your Telegram bot.
-   **How to get it**: Talk to the [@BotFather](https://t.me/BotFather) on Telegram to create a new bot and receive your token.

### `GEMINI_API_KEY` (Required)

-   **Description**: Your API key for the Google Gemini API.
-   **How to get it**: Obtain your key from the [Google AI Studio](https://aistudio.google.com/app/apikey).

## Security

### `BOT_PASSWORD` (Optional)

-   **Description**: A password to restrict access to the bot. If set, users will need to enter this password using the `/start` command before they can use the bot.
-   **Default**: If not set, the bot will be accessible to anyone who can find it.

## Summarization Settings

### `SUMMARY_LANGUAGE` (Optional)

-   **Description**: The language in which the article summaries should be generated.
-   **Examples**: `English`, `Italian`, `Spanish`, `French`
-   **Default**: `English`

## Advanced Configuration (Optional)

These variables are not included in the `.env.example` but can be added if you need to customize the bot's behavior further.

### `LOG_LEVEL`

-   **Description**: Sets the logging level for the application.
-   **Values**: `DEBUG`, `INFO`, `WARNING`, `ERROR`
-   **Default**: `INFO`
