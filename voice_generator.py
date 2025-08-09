import requests
import os
from pathlib import Path
from typing import Optional, Dict, Any
from config import Config

class VoiceGenerator:
    def __init__(self):
        self.api_key = Config.ELEVENLABS_API_KEY
        self.voice_id = Config.ELEVENLABS_VOICE_ID
        self.base_url = "https://api.elevenlabs.io/v1"
        
        if not self.api_key:
            raise ValueError("ElevenLabs API key not found in configuration")
    
    def get_available_voices(self) -> Dict[str, Any]:
        """Get list of available voices from ElevenLabs."""
        headers = {
            "Accept": "application/json",
            "xi-api-key": self.api_key
        }
        
        try:
            response = requests.get(f"{self.base_url}/voices", headers=headers)
            response.raise_for_status()
            return response.json()
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
        
        url = f"{self.base_url}/text-to-speech/{self.voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",  # Use the latest multilingual model
            "voice_settings": default_settings
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            
            # Save the audio file
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            return str(output_path)
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to generate speech: {str(e)}")
    
    def generate_speech_streaming(self, text: str, output_filename: Optional[str] = None,
                                voice_settings: Optional[Dict] = None) -> str:
        """
        Generate speech using streaming for faster response (good for real-time applications).
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
        
        url = f"{self.base_url}/text-to-speech/{self.voice_id}/stream"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": default_settings
        }
        
        try:
            response = requests.post(url, json=data, headers=headers, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            
            return str(output_path)
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to generate streaming speech: {str(e)}")
    
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
        
        headers = {
            "Accept": "application/json",
            "xi-api-key": self.api_key
        }
        
        try:
            response = requests.get(f"{self.base_url}/voices/{target_voice_id}", headers=headers)
            response.raise_for_status()
            return response.json()
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
