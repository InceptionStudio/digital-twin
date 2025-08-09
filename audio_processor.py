import os
import tempfile
from pathlib import Path
from typing import Optional
import openai
from pydub import AudioSegment
from config import Config

class AudioProcessor:
    def __init__(self):
        self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
    
    def extract_audio_from_video(self, video_path: str) -> str:
        """Extract audio from video file and save as WAV."""
        try:
            # Load video and extract audio
            audio = AudioSegment.from_file(video_path)
            
            # Convert to WAV format for Whisper
            audio_path = Config.TEMP_DIR / f"extracted_audio_{os.path.basename(video_path)}.wav"
            audio.export(str(audio_path), format="wav")
            
            return str(audio_path)
        except Exception as e:
            raise Exception(f"Failed to extract audio from video: {str(e)}")
    
    def transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio to text using OpenAI Whisper."""
        try:
            with open(audio_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            return transcript
        except Exception as e:
            raise Exception(f"Failed to transcribe audio: {str(e)}")
    
    def process_input(self, file_path: str) -> str:
        """Process audio or video input and return transcribed text."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")
        
        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > Config.MAX_FILE_SIZE_MB:
            raise ValueError(f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed size ({Config.MAX_FILE_SIZE_MB}MB)")
        
        # Determine file type and process accordingly
        file_extension = file_path.suffix.lower()
        
        if file_extension in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
            # Video file - extract audio first
            audio_path = self.extract_audio_from_video(str(file_path))
            transcript = self.transcribe_audio(audio_path)
            # Clean up temporary audio file
            os.unlink(audio_path)
            return transcript
        
        elif file_extension in ['.wav', '.mp3', '.m4a', '.flac', '.ogg']:
            # Audio file - transcribe directly
            return self.transcribe_audio(str(file_path))
        
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    def cleanup_temp_files(self):
        """Clean up temporary files in the temp directory."""
        temp_files = list(Config.TEMP_DIR.glob("extracted_audio_*"))
        for temp_file in temp_files:
            try:
                temp_file.unlink()
            except Exception:
                pass  # Ignore cleanup errors
