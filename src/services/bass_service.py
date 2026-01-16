import os
import logging
import subprocess
import shutil
from pydub import AudioSegment

logger = logging.getLogger("Autoplex.BassService")

class BassService:
    def __init__(self, temp_dir="/tmp/autoplex_processing"):
        self.temp_dir = temp_dir
        os.makedirs(self.temp_dir, exist_ok=True)

    def process_track(self, file_path, bass_gain_db=6):
        """
        Separates the track using Demucs, boosts bass, and remixes.
        Returns the path to the output MP3 file.
        """
        filename = os.path.basename(file_path)
        name_no_ext = os.path.splitext(filename)[0]
        output_folder = os.path.join(self.temp_dir, "separated", "htdemucs", name_no_ext)
        
        logger.info(f"Starting Demucs separation for: {filename}")
        
        # 1. Run Demucs
        # -n htdemucs: Use the default Hybrid Transformer model (good speed/quality trade-off)
        # --out: output directory
        command = [
            "demucs",
            "-n", "htdemucs", 
            "--out", os.path.join(self.temp_dir, "separated"),
            file_path
        ]
        
        try:
            # Running Demucs as a subprocess
            subprocess.run(command, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Demucs failed: {e.stderr.decode()}")
            raise RuntimeError("Audio separation failed.")

        # 2. Load Stems with Pydub
        # Demucs outputs to: {temp_dir}/separated/htdemucs/{name_no_ext}/{stem}.wav
        try:
            bass = AudioSegment.from_wav(os.path.join(output_folder, "bass.wav"))
            drums = AudioSegment.from_wav(os.path.join(output_folder, "drums.wav"))
            vocals = AudioSegment.from_wav(os.path.join(output_folder, "vocals.wav"))
            other = AudioSegment.from_wav(os.path.join(output_folder, "other.wav"))
        except FileNotFoundError:
            logger.error("Could not find separated stems.")
            raise RuntimeError("Stem separation failed.")

        # 3. Apply Boost
        logger.info(f"Boosting bass by {bass_gain_db}dB")
        bass = bass + bass_gain_db

        # 4. Mix all stems together
        mixed = bass.overlay(drums).overlay(vocals).overlay(other)

        # 5. Normalize to prevent clipping from bass boost
        # Target -1.0 dBFS headroom to avoid clipping
        peak_amplitude = mixed.max_dBFS
        if peak_amplitude > -1.0:
            reduction = peak_amplitude + 1.0  # How much we need to reduce
            logger.info(f"Normalizing output (peak was {peak_amplitude:.1f} dBFS)")
            mixed = mixed - reduction

        # 6. Export with Discord file size limits in mind (8MB limit, target 6MB)
        output_filename = f"{name_no_ext} (Bass Boosted).mp3"
        output_path = os.path.join(self.temp_dir, output_filename)
        max_size_mb = 6.0

        # Try progressively lower bitrates until under limit
        for bitrate in ["256k", "128k", "96k", "64k"]:
            logger.info(f"Exporting at {bitrate}...")
            mixed.export(output_path, format="mp3", bitrate=bitrate)
            file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"File size: {file_size_mb:.1f} MB")

            if file_size_mb <= max_size_mb:
                break

        # 7. Cleanup Stems (Optional: keep them if we want to cache, but for now delete)
        # shutil.rmtree(os.path.join(self.temp_dir, "separated"), ignore_errors=True)

        return output_path

    def cleanup(self):
        """Removes the temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            os.makedirs(self.temp_dir, exist_ok=True)
