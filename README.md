<div align="center">
  <img src="TLDR-bot_logo.png" alt="Project Logo" width="200"/>
  
  # TLDR Bot
  
  **A Telegram bot scrapes web articles and generates summaries**
  
  [![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/username/project/actions)
  

</div>

--- 

This Telegram bot scrapes web articles, extracts their content, and generates customizable summaries using the Google Gemini large language model.

## Features

- **Article Scraping**: Extracts the main content from any given URL.
- **AI-Powered Summaries**: Utilizes Google's Gemini models to generate high-quality, human-like summaries.
- **Customizable Prompts**: Supports multiple, customizable prompt templates to generate different summary styles (e.g., technical, ELI5, social media posts).
- **Configurable Models**: Allows users to choose from different Gemini models for summary generation.
- **Configurable Summary Language**: Allows users to set the output language for summaries via an environment variable.
- **Web Search Integration**: Can perform a web search to gather more context for the summary.
- **Telegraph Integration**: Publishes long-form summaries as clean, readable Telegraph pages.
- **API Quota Management**: Tracks API usage to prevent exceeding rate limits.
- **Password Protection**: Secures access to the bot with a password.
- **Docker Support**: Includes `Dockerfile` and `docker-compose.yml` for easy deployment.

## Quick Start

### 1. Prerequisites

- Python 3.11+
- Docker (optional)

### 2. Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-repo/article-summarizer-bot.git
    cd article-summarizer-bot
    ```

2.  **Create a `.env` file:**
    Copy the example file and fill in your credentials:
    ```bash
    cp .env.example .env
    ```

    You will need to provide:
    - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token.
    - `GEMINI_API_KEY`: Your Google Gemini API key.
    - `BOT_PASSWORD`: A password to protect your bot (optional).
    - `SUMMARY_LANGUAGE`: The desired language for the summaries (e.g., "English", "Italian"). Defaults to "English".

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### 3. Running the Bot

#### Without Docker

```bash
python src/bot.py
```

#### With Docker

```bash
docker-compose up -d
```

## Usage

1.  **Start a chat with your bot** on Telegram and enter the password if you have set one.
2.  **Send a URL** of an article you want to summarize.
3.  The bot will reply with a short summary and a button to generate a full Telegraph page.
4.  Use the keyboard commands to:
    - **Choose Prompt**: Select a different summary style.
    - **Change Model**: Switch between different Gemini models.
    - **Toggle Web Search**: Enable or disable web search for more context.
    - **Check API Quota**: View your current Gemini API usage.

## Project Structure

- `src/`: Main source code directory.
  - `core/`: Core logic for scraping, summarizing, and managing history.
  - `handlers/`: Telegram bot command and message handlers.
  - `prompts/`: Customizable prompt templates for the LLM.
- `data/`: Data files, including API quota and user history.
- `docs/`: In-depth documentation.
- `Dockerfile`: For building the bot's Docker image.
- `docker-compose.yml`: For running the bot with Docker Compose.
- `requirements.txt`: Python dependencies.
