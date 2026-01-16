# Feature Specification: Bass Boost (AI-Powered)

## Overview
A Discord command `!plex bassboost "Song Title"` that retrieves a track from the Plex library, uses AI source separation (Demucs) to isolate and amplify the bass line, and sends the resulting 320kbps MP3 back to Discord.

## User Workflow
1.  **User:** types `!plex bassboost "Billie Jean"` in Discord.
2.  **Bot:** "Searching for 'Billie Jean'..."
3.  **Bot:** "Found 'Billie Jean' by Michael Jackson. Downloading..."
4.  **Bot:** "Processing audio (separating stems)... this may take a moment."
5.  **Bot:** Uploads `Billie Jean (Bass Boosted).mp3` to the chat.

## Technical Implementation

### 1. Search & Download (PlexService)
*   **Method:** `search(title, libtype='track')`
*   **Action:** Select the best match (highest popularity or exact match).
*   **IO:** Download the file to a temporary directory (`/tmp/autoplex/...`).

### 2. Audio Processing (BassBoostService)
*   **Engine:** `demucs` (Hybrid Transformer for Music Source Separation).
*   **Separation:** Split audio into 4 stems: `bass`, `drums`, `vocals`, `other`.
*   **Boost:** Apply +4dB to +6dB gain to the `bass` stem.
*   **Mixing:** Re-combine all stems using `ffmpeg`.
*   **Encoding:** Convert final output to MP3 320kbps.

### 3. Delivery (Discord)
*   **Upload:** Send file via `discord.File`.
*   **Cleanup:** Remove all temp files (original source, stems, output).

## Dependencies
*   **System:** `ffmpeg` (required for Demucs and final conversion).
*   **Python:** `demucs`, `pydub` (optional, for easy mixing) or direct `ffmpeg` subprocess calls.

## Constraints
*   **File Size:** Discord upload limit (8MB for non-Nitro, 50MB-500MB for Nitro boosts). 320kbps MP3 is approx 2.4MB per minute. A 5-min song is ~12MB. We might need to check file size and fallback to 192kbps if > 8MB.
*   **Performance:** Demucs on CPU is resource intensive. Processing might take 1-2x realtime (e.g., 3 min song = 3-6 mins processing).
