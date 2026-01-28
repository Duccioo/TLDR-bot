<div align="center">
  <img src="TLDR-bot_logo.png" alt="TLDR Bot Logo" width="200"/>
  
  # 🤖 TLDR Bot

  **Your AI-Powered Article Summarizer for Telegram**

  [![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
  [![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
  [![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](Dockerfile)
  [![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue?logo=telegram)](https://core.telegram.org/bots)

  *Scrape any web article, extract its content, and get AI-generated summaries in seconds!*

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔗 **Smart Web Scraping** | Extracts main content from any URL using advanced parsing |
| 🧠 **Multi-LLM Support** | Choose from **Gemini**, **Groq**, or **OpenRouter** models |
| 📝 **Customizable Prompts** | Multiple summary styles: Technical, ELI5, Q&A, Social Media, and more |
| 🌍 **Multi-Language Output** | Configure summary output language via environment variable |
| 🔍 **Web Search Integration** | Enhance summaries with additional web context |
| 📰 **Telegraph Publishing** | Generate beautiful, readable Telegraph pages for long summaries |
| 📊 **API Quota Tracking** | Monitor usage and prevent rate limit issues |
| 🔐 **Password Protection** | Secure bot access with optional authentication |
| 🐳 **Docker Ready** | Easy deployment with Docker and Docker Compose |
| 📌 **Linkwarden Integration** | Save summarized articles directly to your Linkwarden instance |
| 🛡️ **FlareSolverr Support** | Bypass Cloudflare protection for difficult sites |

---

## 🚀 Quick Start

### Prerequisites

- 🐍 Python 3.11+
- 🐳 Docker *(optional, for containerized deployment)*
- 🔑 API Keys:
  - [Telegram Bot Token](https://core.telegram.org/bots#botfather)
  - [Google Gemini API Key](https://makersuite.google.com/app/apikey) *(and/or Groq/OpenRouter)*

### Installation

#### 1️⃣ Clone the Repository

```bash
git clone https://github.com/Duccioo/TLDR-bot.git
cd TLDR-bot
```

#### 2️⃣ Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Required
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_gemini_api_key

# Optional: Additional LLM Providers
GROQ_API_KEY=your_groq_api_key
OPENROUTER_API_KEY=your_openrouter_api_key

# Optional: Bot Settings
BOT_PASSWORD=your_secure_password
SUMMARY_LANGUAGE=English

# Optional: Linkwarden
LINKWARDEN_URL=https://linkwarden.yourdomain.com
LINKWARDEN_API_KEY=your_linkwarden_api_key

# Optional: Advanced
FLARESOLVERR_URL=http://localhost:8191/v1
```

#### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Running the Bot

### 🖥️ Local Development

```bash
python src/bot.py
```

### 🐳 Docker Deployment

```bash
docker-compose up -d
```

---

## 📖 Usage

1. **🚀 Start the bot** — Open your Telegram bot and enter the password (if configured)
2. **🔗 Send a URL** — Paste any article link
3. **📄 Get your summary** — Receive an instant AI-generated summary
4. **📰 Expand to Telegraph** — Click the button to generate a full Telegraph article

### ⌨️ Available Commands

| Command | Description |
|---------|-------------|
| 🎨 **Choose Prompt** | Select summary style (Technical, ELI5, Q&A, etc.) |
| 🔄 **Change Model** | Switch between Gemini, Groq, or OpenRouter models |
| 🔍 **Toggle Web Search** | Enable/disable web context enrichment |
| 📊 **Check Quota** | View your current API usage |

---

## 📁 Project Structure

```
TLDR-bot/
├── 📂 src/                    # Source code
│   ├── 📂 core/               # Core logic
│   │   ├── extractor.py       # Content extraction
│   │   ├── scraper.py         # Web scraping
│   │   ├── summarizer.py      # LLM integration
│   │   ├── quota_manager.py   # API quota tracking
│   │   ├── history_manager.py # User history
│   │   └── user_manager.py    # User management
│   ├── 📂 handlers/           # Telegram bot handlers
│   │   ├── auth_handlers.py   # Authentication
│   │   ├── command_handlers.py
│   │   ├── message_handlers.py
│   │   └── callback_handlers.py
│   ├── 📂 prompts/            # Summary prompt templates
│   │   ├── technical_summary.md
│   │   ├── eli5_summary.md
│   │   ├── social_media_post.md
│   │   ├── qna.md
│   │   └── ...
│   ├── bot.py                 # Main entry point
│   ├── config.py              # Configuration
│   └── keyboards.py           # Telegram keyboards
├── 📂 data/                   # Runtime data (quota, history)
├── 📂 docs/                   # Documentation
│   ├── ARCHITECTURE.md
│   ├── CONFIGURATION.md
│   ├── CONTRIBUTING.md
│   └── INSTALLATION.md
├── 🐳 Dockerfile
├── 🐳 docker-compose.yml
├── 📋 requirements.txt
└── 📄 LICENSE
```

---

## 🤖 Supported LLM Providers

| Provider | Models | Free Tier |
|----------|--------|-----------|
| **Google Gemini** | gemini-2.5-flash, gemini-2.0-flash | ✅ Yes |
| **Groq** | Various open-source models | ✅ Yes |
| **OpenRouter** | Multiple models (`:free` suffix) | ✅ Yes |

---

## 📚 Documentation

For more detailed information, check the `/docs` folder:

- 📐 [Architecture](docs/ARCHITECTURE.md) — System design and components
- ⚙️ [Configuration](docs/CONFIGURATION.md) — All configuration options
- 🛠️ [Installation](docs/INSTALLATION.md) — Detailed setup guide
- 🤝 [Contributing](docs/CONTRIBUTING.md) — How to contribute

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](docs/CONTRIBUTING.md) for details on how to submit pull requests.

---

## 📄 License

This project is licensed under the **Apache License 2.0** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

  **Made with ❤️ for the open-source community**

  ⭐ **Star this repo if you find it useful!** ⭐

</div>
