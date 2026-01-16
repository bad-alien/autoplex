# Feature Specification: AI Remix (Generalization of Bass Boost)

## Overview
A generalized "Remix" feature for the Discord bot that allows users to selectively **boost** or **reduce** specific stems (bass, drums, vocals, other) of a track using AI source separation. The system prioritizes audio quality using fine-tuned models and intelligent limiting.

## User Interface

### Commands
All commands support an optional `amount` in dB (defaulting to 5dB if omitted).

1.  **Boost:** `!plex boost [stem] [amount?] "Song Title"`
    *   *Example:* `!plex boost bass "Billie Jean"` (Boosts bass by default +5dB)
    *   *Example:* `!plex boost vocals 3 "Halo"` (Boosts vocals by +3dB)
2.  **Reduce:** `!plex reduce [stem] [amount?] "Song Title"`
    *   *Example:* `!plex reduce drums 10 "In the Air Tonight"` (Reduces drums by -10dB)

### Supported Stems
*   `bass`
*   `drums`
*   `vocals`
*   `other` (melody, synth, guitar, etc.)

### Feedback
*   **Progress Updates:** The bot provides status updates for "Downloading", "Separating (AI)", "Mixing", and "Uploading".
*   **Error Handling:** Reports specific errors (e.g., "Song too long", "File too large for Discord").

## Technical Implementation

### 1. Service Architecture
*   **Rename:** `BassService` -> `RemixService`.
*   **Responsibility:** Handles downloading, Demucs separation, FFmpeg mixing, and cleanup.

### 2. AI Separation (Demucs)
*   **Model:** `htdemucs_ft` (Fine-tuned Hybrid Transformer) for higher quality separation.
*   **Parameters:**
    *   `--shifts 2`: Performs random time shifts and averages predictions to reduce artifacts and improve Source-to-Distortion Ratio (SDR).
    *   `--jobs 4`: To speed up processing if CPU allows.
    *   `--mp3`: (Optional) Demucs can output MP3 directly, but WAV is preferred for intermediate mixing.

### 3. Intelligent Mixing (FFmpeg)
Instead of simple linear summing (which causes clipping) or hard normalization (which reduces volume drastically), we will use **FFmpeg's filter complex** for "intelligent" mixing.

**Pipeline:**
1.  **Inputs:** 4 WAV stems from Demucs.
2.  **Volume Filter:** Apply `volume=XdB` to the target stem.
3.  **Mix:** Use `amix` to combine the 4 streams.
    *   `inputs=4`: 4 input streams.
    *   `dropout_transition=0`: Hard transition (irrelevant for full duration).
    *   `normalize=0`: **Critical**. We disable `amix`'s auto-normalization to handle gain staging manually with a limiter.
4.  **Limiter:** Apply `alimiter` to the mixed output.
    *   `limit=0.95`: Prevents peaks above -0.5dB.
    *   `level_in=1.0`: Unity gain input.
    *   `level_out=1.0`: Unity gain output.
    *   `asc=1`: Enable ASC (Auto Leveling) to maximize loudness without crushing dynamics.
5.  **Output:** MP3 320kbps (or V0 VBR).

**Why FFmpeg?**
*   Avoids loading large WAVs into Python memory (Pydub).
*   `alimiter` provides professional-grade "soft clipping/limiting" behavior superior to simple normalization.
*   Faster execution (C-based processing).

### 4. File Output
*   **Naming Convention:** `{Title} ({Stem} {Action}).mp3`
    *   *Example:* `Billie Jean (Bass Boost).mp3`
    *   *Example:* `Halo (Vocals Reduce).mp3`
*   **Size Management:**
    *   Target: < 8MB (Standard Discord limit).
    *   Logic: If 320kbps results in > 8MB, retry encoding at 192kbps, then 128kbps.

## Migration Plan
1.  **Refactor:** Rename `src/services/bass_service.py` to `src/services/remix_service.py`.
2.  **Dependency Update:** ensure `demucs` is up to date in `requirements.txt`.
3.  **Code Logic:**
    *   Update `process_track` to accept `stem` and `gain_db` arguments.
    *   Replace Pydub mixing logic with `subprocess.run(["ffmpeg", ...])`.
4.  **Bot Commands:** Update `src/main.py` to replace `!plex bassboost` with the new command structure.

## Future Considerations
*   **"Instrumental" / "Acapella" commands:** Shortcuts for `!plex reduce vocals 100` or `!plex reduce drums 100`.
