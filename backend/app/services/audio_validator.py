import hashlib
import os
import subprocess
import tempfile
import soundfile as sf
import numpy as np
from typing import Tuple, Optional


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
    def convert_to_wav(file_path: str) -> str:
        """Converts any audio file to a standard 16kHz mono WAV file using ffmpeg."""
        temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_wav.close()
        
        try:
            subprocess.run([
                "ffmpeg", "-y", "-i", file_path, 
                "-ar", "16000", "-ac", "1", temp_wav.name
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return temp_wav.name
        except Exception as e:
            if os.path.exists(temp_wav.name):
                os.unlink(temp_wav.name)
            raise AudioValidationError(f"FFmpeg audio conversion failed: {e}")

    @staticmethod
    def validate_audio_content(file_path: str) -> Tuple[float, float, float]:
        """Reads audio and returns (duration, rms_energy_db, snr) using soundfile and numpy."""
        wav_path = None
        try:
            # 1. Try reading the file directly
            try:
                y, sr = sf.read(file_path)
                if len(y.shape) > 1:
                    y = np.mean(y, axis=1)
                # If sample rate is different, convert it via ffmpeg to be safe
                if sr != 16000:
                    raise ValueError("Needs resampling")
            except Exception:
                # 2. Fall back to converting via ffmpeg
                wav_path = AudioValidator.convert_to_wav(file_path)
                y, sr = sf.read(wav_path)
                if len(y.shape) > 1:
                    y = np.mean(y, axis=1)

            duration = float(len(y) / sr)
            
            # Enforce 30 to 45 seconds
            if duration < 30.0 or duration > 45.0:
                raise AudioValidationError(
                    f"Audio duration must be between 30 and 45 seconds. Got {duration:.2f} seconds."
                )
            
            # 3. Calculate RMS energy using numpy sliding window
            frame_length = 2048
            hop_length = 512
            rms = []
            for i in range(0, len(y) - frame_length, hop_length):
                frame = y[i:i+frame_length]
                rms.append(np.sqrt(np.mean(frame**2) + 1e-6))
            
            rms = np.array(rms)
            if len(rms) == 0:
                raise AudioValidationError("Audio file is empty or corrupted.")

            avg_rms_db = 20 * np.log10(np.mean(rms) + 1e-6)
            
            if avg_rms_db < -45.0:
                raise AudioValidationError("Audio is silent or has extremely low volume. Please check your microphone.")

            # Noise Check (estimate Signal to Noise Ratio)
            noise_floor_rms = np.percentile(rms, 10) + 1e-6
            speech_rms = np.percentile(rms, 90) + 1e-6
            snr = 20 * np.log10(speech_rms / noise_floor_rms)
            
            if snr < 8.0:
                raise AudioValidationError("Audio has too much background noise. Please record in a quieter environment.")

            # Flatline check
            if np.std(y) < 1e-4:
                raise AudioValidationError("Audio data appears corrupted or flatlined.")

            return duration, float(avg_rms_db), float(snr)

        except AudioValidationError:
            raise
        except Exception as e:
            raise AudioValidationError(f"Invalid or corrupted audio file structure: {str(e)}")
        finally:
            if wav_path and os.path.exists(wav_path):
                try:
                    os.unlink(wav_path)
                except Exception:
                    pass
