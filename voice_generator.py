import os
from pathlib import Path
from typing import Optional, Dict, Any
from elevenlabs import ElevenLabs
from config import Config

class VoiceGenerator:
    def __init__(self):
        self.api_key = Config.ELEVENLABS_API_KEY
        self.voice_id = Config.ELEVENLABS_VOICE_ID
        
        if not self.api_key:
            raise ValueError("ElevenLabs API key not found in configuration")
        
        # Initialize ElevenLabs client
        self.client = ElevenLabs(api_key=self.api_key)
    
    def get_available_voices(self) -> Dict[str, Any]:
        """Get list of available voices from ElevenLabs."""
        try:
            voices = self.client.voices.get_all()
            return {"voices": voices}
        except Exception as e:
            raise Exception(f"Failed to fetch available voices: {str(e)}")
    
    def generate_speech(self, text: str, output_filename: Optional[str] = None, 
                       voice_settings: Optional[Dict] = None) -> str:
        """
        Generate speech from text using ElevenLabs API.
        
        Args:
            text: The text to convert to speech
            output_filename: Optional filename for the output audio file
            voice_settings: Optional voice settings (stability, similarity_boost, style)
        
        Returns:
            Path to the generated audio file
        """
        if not output_filename:
            output_filename = f"chad_response_{hash(text) % 10000}.mp3"
        
        output_path = Config.OUTPUT_DIR / output_filename
        
        # Default voice settings optimized for Chad's personality
        default_settings = {
            "stability": 0.75,
            "similarity_boost": 0.75,
            "style": 0.8,  # Higher style for more expressive delivery
            "use_speaker_boost": True
        }
        
        if voice_settings:
            default_settings.update(voice_settings)
        
        try:
            # Generate speech using the ElevenLabs SDK
            audio_stream = self.client.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128",
                voice_settings=default_settings
            )
            
            # Save the audio file by consuming the generator
            with open(output_path, 'wb') as f:
                for chunk in audio_stream:
                    f.write(chunk)
            
            return str(output_path)
            
        except Exception as e:
            raise Exception(f"Failed to generate speech: {str(e)}")
    
    def generate_speech_streaming(self, text: str, output_filename: Optional[str] = None,
                                voice_settings: Optional[Dict] = None) -> str:
        """
        Generate speech using the ElevenLabs SDK (same as regular method for now).
        """
        if not output_filename:
            output_filename = f"chad_response_stream_{hash(text) % 10000}.mp3"
        
        output_path = Config.OUTPUT_DIR / output_filename
        
        default_settings = {
            "stability": 0.75,
            "similarity_boost": 0.75,
            "style": 0.8,
            "use_speaker_boost": True
        }
        
        if voice_settings:
            default_settings.update(voice_settings)
        
        try:
            # Generate speech using the ElevenLabs SDK
            audio_stream = self.client.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128",
                voice_settings=default_settings
            )
            
            # Save the audio file by consuming the generator
            with open(output_path, 'wb') as f:
                for chunk in audio_stream:
                    f.write(chunk)
            
            return str(output_path)
            
        except Exception as e:
            raise Exception(f"Failed to generate speech: {str(e)}")
    
    def test_connection(self) -> bool:
        """Test the ElevenLabs API connection."""
        try:
            self.get_available_voices()
            return True
        except Exception:
            return False
    
    def get_voice_info(self, voice_id: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a specific voice."""
        target_voice_id = voice_id or self.voice_id
        
        try:
            voice_info = self.client.voices.get(voice_id=target_voice_id)
            return voice_info
        except Exception as e:
            raise Exception(f"Failed to get voice info: {str(e)}")
    
    def cleanup_audio_files(self, keep_latest: int = 5):
        """Clean up old audio files, keeping only the most recent ones."""
        audio_files = list(Config.OUTPUT_DIR.glob("chad_response_*.mp3"))
        audio_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Remove all but the most recent files
        for file_to_remove in audio_files[keep_latest:]:
            try:
                file_to_remove.unlink()
            except Exception:
                pass  # Ignore cleanup errors
