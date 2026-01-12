# Autoplex Specification

## Overview
Autoplex is a Dockerized Python automation suite designed for Unraid. It acts as a bridge between Plex Media Server, Tautulli, and Discord, providing advanced metadata management, automated playlist generation, and interactive usage statistics via a Discord bot.

## Architecture
*   **Platform:** Docker (Unraid compatible).
*   **Language:** Python 3.11+.
*   **Interface:** Discord Bot (Command & Response).

## Integrations
1.  **Plex Media Server:**
    *   Library Management (Read/Write).
    *   Playlists (Read/Write).
    *   Metadata (Read/Write).
    *   Library: `PlexAPI`.
2.  **Tautulli:**
    *   Live Activity Monitoring (Read).
    *   History/Statistics (Read).
    *   Library: HTTP Requests (Requests/Aiohttp) to Tautulli API.
3.  **Discord:**
    *   Command Interface.
    *   Rich Embed Responses.
    *   Library: `discord.py`.
4.  **External Metadata Sources (Music):**
    *   MusicBrainz or Discogs API (for fetching Jazz instrumentalists).

## Core Features

### 1. Discord Bot Commands
*   **`!plex usage`**
    *   **Source:** Tautulli API (`get_activity`).
    *   **Output:** A Discord Embed listing current streams, users, titles, devices, and transcoding status.
*   **`!plex completion [artist_name]`**
    *   **Source:** Plex Library (Total Tracks) & Tautulli/Plex History (Played Tracks).
    *   **Logic:**
        1.  Find Artist in Plex.
        2.  Get all tracks for that Artist.
        3.  Check play count for each track.
        4.  Calculate % of unique tracks played > 0 times.
    *   **Output:** "You have listened to X% (N/Total) of [Artist]'s collection on this server."

### 2. Metadata Enrichment ("The Jazz Feature")
*   **Trigger:** Command based (e.g., `!plex enrich [album_id/search]`).
*   **Function:**
    1.  Search external DB (MusicBrainz/Discogs) for the album.
    2.  Extract credited instrumentalists/performers.
    3.  Format list (e.g., "John Coltrane: Sax | McCoy Tyner: Piano").
    4.  Prepend or Append to the Plex Album "Summary" field.

### 3. Automated Playlists
*   **Goal:** "Top Rated" Sync.
*   **Trigger:** Scheduled Task (e.g., hourly/daily) or Command (`!plex sync_playlists`).
*   **Logic:**
    1.  Query Plex for all Music Tracks with Rating >= 4 stars.
    2.  Get specific playlist "My Top Rated".
    3.  Diff the lists and update the playlist to match the query results.

## Configuration (.env)
*   `DISCORD_TOKEN`: Bot token.
*   `PLEX_URL`: Local URL of Plex Server.
*   `PLEX_TOKEN`: X-Plex-Token.
*   `TAUTULLI_URL`: Local URL of Tautulli.
*   `TAUTULLI_API_KEY`: API Key.
*   `MUSICBRAINZ_USER_AGENT`: (Optional) For polite API usage.

## Deliverables
*   `src/`: Python source code.
*   `Dockerfile`: For containerization.
*   `docker-compose.yml`: For easy deployment on Unraid.
*   `requirements.txt`: Python dependencies.
