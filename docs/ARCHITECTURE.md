# Architecture Overview

This document provides an overview of the bot's technical architecture, project structure, and the interaction between its components.

## Project Structure

The project is organized into a modular structure to separate concerns and improve maintainability.

```
.
├── .env.example
├── data/
│   ├── quota.json
│   └── history/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── CONFIGURATION.md
│   ├── CONTRIBUTING.md
│   └── INSTALLATION.md
├── src/
│   ├── core/
│   │   ├── extractor.py
│   │   ├── summarizer.py
│   │   ├── history_manager.py
│   │   └── quota_manager.py
│   ├── handlers/
│   │   ├── auth_handlers.py
│   │   ├── command_handlers.py
│   │   └── ...
│   ├── prompts/
│   │   ├── one_paragraph_summary_V2.md
│   │   └── ...
│   ├── bot.py
│   ├── config.py
│   └── keyboards.py
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

### Key Directories and Files

-   **`src/`**: Contains all the main source code.
    -   **`core/`**: The business logic of the application.
        -   `extractor.py`: Handles scraping and extracting content from URLs.
        -   `summarizer.py`: Interacts with the Gemini API to generate summaries.
        -   `history_manager.py`: Manages user-specific article history.
        -   `quota_manager.py`: Tracks and manages API usage and rate limits.
    -   **`handlers/`**: Manages user interactions with the Telegram bot. It contains handlers for commands (`/start`, `/help`), messages (URL processing), and callbacks (button presses).
    -   **`prompts/`**: Stores Markdown templates for the summarization prompts. Each file represents a different summary style.
    -   **`bot.py`**: The main entry point of the application. It initializes the bot and registers the handlers.
    -   **`config.py`**: Loads and manages configuration from environment variables.
    -   **`keyboards.py`**: Defines the custom keyboards and UI buttons for the bot.
-   **`data/`**: Persists application data.
    -   `quota.json`: Stores the current state of the API usage quota.
    -   `history/`: Contains JSON files for each user's article history.
-   **`docs/`**: Project documentation.

## Core Components and Interaction Flow

### 1. User Interaction (Telegram)

-   The user sends a message to the bot (e.g., a URL or a command).
-   The `python-telegram-bot` library receives the update and routes it to the appropriate handler in the `src/handlers/` directory.

### 2. Content Extraction

-   When a URL is received, the `summarize_url` handler in `message_handlers.py` is triggered.
-   It calls the `scrape_article` function from `src/core/extractor.py`.
-   The extractor uses the `trafilatura` library to fetch the URL and extract the main article content, title, author, and other metadata.

### 3. Summarization

-   The extracted content is passed to the `summarize_article` function in `src/core/summarizer.py`.
-   This function reads a prompt template from the `src/prompts/` directory.
-   It then calls the Google Gemini API via the `_call_llm_api` function, sending the article content and the formatted prompt.
-   The API call is wrapped with rate-limiting checks from `quota_manager.py` and a retry mechanism for network errors.

### 4. Response Generation

-   The summary received from the Gemini API is formatted into a Telegram message.
-   A custom keyboard is generated using `src/keyboards.py` to provide further actions (e.g., "Create Telegraph Page").
-   The final message is sent back to the user.

### 5. Asynchronous Operations

-   To avoid blocking the main event loop, long-running operations like web scraping and API calls are executed in separate threads using `asyncio.to_thread`.
-   Loading animations are handled concurrently using `asyncio.create_task` to provide a responsive user experience.
