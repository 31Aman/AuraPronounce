import hashlib
import os
import soundfile as sf
import numpy as np
import librosa
import warnings
from typing import Tuple, Optional

# Suppress librosa file format and deprecation warnings to keep logs clean
warnings.filterwarnings("ignore", category=UserWarning, module="librosa")
warnings.filterwarnings("ignore", category=FutureWarning, module="librosa")


class AudioValidationError(Exception):
    """Custom exception for audio validation failures."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class AudioValidator:
    # 10 MB maximum file size
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    # Supported magic bytes for format verification (Virus-safe codec checks)
    MAGIC_HEADERS = {
        b"RIFF": "wav",
        b"ID3": "mp3",
        b"\xff\xfb": "mp3",
        b"\xff\xf3": "mp3",
        b"\xff\xf2": "mp3",
        b"OggS": "ogg",
        b"\x1a\x45\xdf\xa3": "webm",  # WebM container
        b"ftyp": "m4a",  # MP4 / M4A containers (check starting offset 4)
    }

    @staticmethod
    def validate_file_size(file_path: str) -> int:
        file_size = os.path.getsize(file_path)
        if file_size > AudioValidator.MAX_FILE_SIZE:
            raise AudioValidationError(f"File size exceeds 10MB limit. Got {file_size / (1024*1024):.2f}MB.")
        return file_size

    @staticmethod
    def validate_file_signature(file_path: str, mime_type: str) -> str:
        """Validate actual file signature (magic bytes) rather than relying on file extension."""
        with open(file_path, "rb") as f:
            header = f.read(16)
        
        # Check standard headers
        detected_format = None
        for magic, fmt in AudioValidator.MAGIC_HEADERS.items():
            if header.startswith(magic):
                detected_format = fmt
                break
        
        # M4A check (starts with ftyp at offset 4)
        if not detected_format and b"ftyp" in header[4:12]:
            detected_format = "m4a"

        # OGG/AAC checks
        if not detected_format:
            # Check AAC (ADTS headers: 0xFFF1 or 0xFFF9 or 0xFFF0 or 0xFFF8)
            if len(header) >= 2 and header[0] == 0xFF and (header[1] & 0xF0) == 0xF0:
                detected_format = "aac"

        if not detected_format:
            raise AudioValidationError("Unsupported or corrupted audio codec. Only wav, mp3, m4a, aac, ogg, webm are accepted.")
        
        return detected_format

    @staticmethod
    def calculate_checksum(file_path: str) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for block in iter(lambda: f.read(4096), b""):
                sha256.update(block)
        return sha256.hexdigest()

    @staticmethod
    def validate_audio_content(file_path: str) -> Tuple[float, float, float]:
        """Reads audio and returns (duration, rms_energy_db, snr).
        Raises AudioValidationError if validation fails."""
        try:
            # Load audio for acoustic features and duration using librosa (handles WebM, MP3, M4A via ffmpeg)
            y, sr = librosa.load(file_path, sr=16000)
            duration = float(len(y) / sr)
            
            # Enforce 30 to 45 seconds
            if duration < 30.0 or duration > 45.0:
                raise AudioValidationError(
                    f"Audio duration must be between 30 and 45 seconds. Got {duration:.2f} seconds."
                )
            
            # 1. Silence check
            # Calculate RMS energy of each frame
            rms = librosa.feature.rms(y=y)[0]
            avg_rms_db = 20 * np.log10(np.mean(rms) + 1e-6)
            
            # If average energy is below -45dB, it's considered silent
            if avg_rms_db < -45.0:
                raise AudioValidationError("Audio is silent or has extremely low volume. Please check your microphone.")

            # 2. Noise Check (estimate Signal to Noise Ratio)
            # Estimate noise floor using the 10th percentile of frame energy
            noise_floor_rms = np.percentile(rms, 10) + 1e-6
            speech_rms = np.percentile(rms, 90) + 1e-6
            snr = 20 * np.log10(speech_rms / noise_floor_rms)
            
            # Extremely noisy audio (e.g. pure static/microphone hiss) will have low SNR
            if snr < 8.0:
                raise AudioValidationError("Audio has too much background noise. Please record in a quieter environment.")

            # 3. Flatline / corruption check
            # Check if there is variation in the signal
            if np.std(y) < 1e-4:
                raise AudioValidationError("Audio data appears corrupted or flatlined.")

            return duration, float(avg_rms_db), float(snr)

        except AudioValidationError:
            raise
        except Exception as e:
            raise AudioValidationError(f"Invalid or corrupted audio file structure: {str(e)}")
