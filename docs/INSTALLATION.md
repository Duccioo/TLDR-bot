# Installation Guide

This guide provides detailed instructions for setting up the Article Summarizer Telegram Bot.

## Method 1: Running with Docker (Recommended)

Using Docker is the easiest and most reliable way to run the bot, as it handles all dependencies and environment setup for you.

### Prerequisites

- Docker: [Install Docker](https://docs.docker.com/get-docker/)
- Docker Compose: [Install Docker Compose](https://docs.docker.com/compose/install/)

### Steps

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-repo/article-summarizer-bot.git
    cd article-summarizer-bot
    ```

2.  **Create and Configure the `.env` File:**
    Copy the provided example file:
    ```bash
    cp .env.example .env
    ```
    Open the `.env` file and fill in your credentials. See the [Configuration](CONFIGURATION.md) guide for more details on each variable.

3.  **Build and Run the Container:**
    ```bash
    docker-compose up --build -d
    ```
    This command will build the Docker image and start the bot in the background.

4.  **Verify the Bot is Running:**
    Check the container logs to ensure everything started correctly:
    ```bash
    docker-compose logs -f
    ```

## Method 2: Running Directly with Python

If you prefer not to use Docker, you can run the bot directly on your machine.

### Prerequisites

- Python 3.11 or higher
- `pip` for package management

### Steps

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-repo/article-summarizer-bot.git
    cd article-summarizer-bot
    ```

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Create and Configure the `.env` File:**
    Copy the example file:
    ```bash
    cp .env.example .env
    ```
    Open the `.env` file and fill in your credentials. See the [Configuration](CONFIGURATION.md) guide for more details.

5.  **Run the Bot:**
    ```bash
    python src/bot.py
    ```

Your bot should now be running and connected to the Telegram API.
