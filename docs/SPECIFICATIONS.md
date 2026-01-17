# Autoalex Technical Specifications

## 1. Overview
**Autoalex** is a comprehensive Dockerized automation suite and Discord bot designed for Unraid environments. It bridges Plex Media Server, Tautulli, and external services to provide advanced library management, interactive usage statistics, AI-powered audio remixing, and system health monitoring.

## 2. System Architecture
*   **Platform:** Docker (Unraid compatible).
*   **Language:** Python 3.11+.
*   **Interface:** Discord Bot (Command & Response) using `discord.py`.
*   **Core Libraries:** `PlexAPI`, `demucs` (AI Audio), `docker` (SDK), `ffmpeg`.

## 3. Core Features

### 3.1. Media Intelligence (Plex & Tautulli)
Interact with library data and user history.

*   **Usage Stats (`!alex usage`):**
    *   **Source:** Tautulli API (`get_activity`).
    *   **Output:** Real-time stream status (User, Title, Device, Transcode status).
*   **Artist Completion (`!alex completion`):**
    *   **Logic:** Calculates the percentage of an artist's discography a user has listened to.
    *   **Data:** Correlates Plex Library (Total Tracks) with Tautulli History (Played Tracks).
    *   **Visualization:** Generates progress bars and "In Progress" album lists.
*   **Listening Battles (`!alex compare`):**
    *   **Logic:** Compares completion stats between two users for a specific artist.

### 3.2. AI Remix Engine
A generalized feature allowing users to selectively boost or reduce specific audio stems (bass, drums, vocals, other) using the **Demucs** Hybrid Transformer model.

*   **Commands:** `!alex boost`, `!alex reduce`.
*   **Supported Stems:** `bass`, `drums`, `vocals`, `other`.
*   **Defaults:**
    *   `boost`: +4dB (amplify stem)
    *   `reduce`: -60dB (effectively removes stem; use lower values for partial reduction)
*   **Pipeline:**
    1.  **Search & Download:** Fetches track from Plex.
    2.  **AI Separation:** Uses `demucs` (`htdemucs_ft` model) to split audio into 4 stems.
    3.  **Intelligent Mixing:** Uses FFmpeg filter complexes (`volume`, `amix`, `alimiter`) to apply gain and prevent clipping.
    4.  **Delivery:** Uploads processed MP3 (320kbps) to Discord.
*   **Constraints:** File size limits (8MB standard), CPU usage.

### 3.3. Infrastructure Monitoring
Actively monitors the health of the Plex Media Server container.

*   **Mechanism:** Polls Plex HTTP endpoint every 30s.
*   **Auto-Diagnostics:** If Plex is unresponsive, connects to the host Docker socket (`/var/run/docker.sock`) to fetch recent container logs.
*   **Alerting:** Sends a Discord alert with status and recent logs to a configured admin channel.
*   **Recovery:** Notifies when service is restored.

### 3.4. Metadata Management
*   **Enrichment:** Adds "Credits" (instrumentalists) to Album summaries using MusicBrainz/Discogs data (Jazz focus).
*   **Playlist Sync:** Syncs "Top Rated" smart playlists based on star ratings.

## 4. Configuration
Environment variables required in `.env`:

### Services
*   `DISCORD_TOKEN`: Bot token.
*   `PLEX_URL`: Local URL of Plex Server.
*   `PLEX_TOKEN`: X-Plex-Token.
*   `TAUTULLI_URL`: Local URL of Tautulli.
*   `TAUTULLI_API_KEY`: API Key.

### Monitoring
*   `DISCORD_ALERT_CHANNEL_ID`: Channel ID for system alerts.
*   `PLEX_CONTAINER_NAME`: Docker container name (default: `binhex-plexpass`).
*   `PLEX_POLL_INTERVAL`: Poll frequency in seconds (default: `30`).

### External
*   `MUSICBRAINZ_APP_NAME`: For API identification.
*   `MUSICBRAINZ_CONTACT`: Contact email.

## 5. Deployment
*   **Docker:** Requires mapping `/var/run/docker.sock` for monitoring features.
*   **Dependencies:** `ffmpeg` installed in the container image.
