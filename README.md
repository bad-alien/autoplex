# Autoalex

**Autoalex** is a Discord bot and automation suite for Plex Media Server enthusiasts. It integrates Plex, Tautulli, and AI audio processing tools to provide rich stats, library management, and fun features like "AI Remix" directly from Discord.

## 📚 Documentation
Detailed documentation is located in the `docs/` directory:

*   **[Technical Specifications](docs/SPECIFICATIONS.md):** Architecture, features, and configuration details.
*   **[Commands Reference](docs/COMMANDS.md):** Full list of available Discord commands.

> **Note for LLMs:** If you are using tools like `repomix` to digest this codebase, the `docs/` folder provides the most up-to-date context on features and architecture.

## 🚀 Quick Start (Docker)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/autoalex.git
    cd autoalex
    ```

2.  **Configure Environment:**
    Copy the example file and edit it with your API keys.
    ```bash
    cp .env.example .env
    nano .env
    ```

3.  **Run with Docker Compose:**
    ```bash
    docker-compose up -d --build
    ```

## 🛠️ Development

### Prerequisites
*   Python 3.11+
*   FFmpeg (installed on system for local dev)
*   Docker (for container build)

### Local Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

## 🏗️ Architecture
*   **Bot:** `discord.py`
*   **AI Engine:** `demucs` (Meta's Hybrid Transformer for Source Separation)
*   **Monitoring:** Direct Docker Socket integration for log retrieval.
