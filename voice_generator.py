import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from elevenlabs import ElevenLabs
from config import Config

class VoiceGenerator:
    def __init__(self):
        self.api_key = Config.ELEVENLABS_API_KEY
        
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
    
    def get_available_models(self) -> Dict[str, Any]:
        """Get list of available models from ElevenLabs."""
        try:
            models = self.client.models.list()
            return {"models": models}
        except Exception as e:
            raise Exception(f"Failed to fetch available models: {str(e)}")
    
    def get_text_to_speech_models(self) -> Dict[str, Any]:
        """Get list of models that support text-to-speech."""
        try:
            all_models = self.client.models.list()
            tts_models = [model for model in all_models if model.can_do_text_to_speech]
            return {"models": tts_models}
        except Exception as e:
            raise Exception(f"Failed to fetch text-to-speech models: {str(e)}")
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        try:
            all_models = self.client.models.list()
            for model in all_models:
                if model.model_id == model_id:
                    return {"model": model}
            raise Exception(f"Model with ID '{model_id}' not found")
        except Exception as e:
            raise Exception(f"Failed to get model info: {str(e)}")
    
    def get_best_tts_model(self) -> str:
        """Get the best available text-to-speech model ID."""
        try:
            tts_models = self.get_text_to_speech_models()
            models = tts_models["models"]
            
            # Priority order for models (most preferred first)
            preferred_models = [
                "eleven_multilingual_v2",
                "eleven_turbo_v2", 
                "eleven_monolingual_v1",
                "eleven_multilingual_v1"
            ]
            
            # Try to find a preferred model
            for preferred in preferred_models:
                for model in models:
                    if model.model_id == preferred:
                        return model.model_id
            
            # If no preferred model found, return the first available TTS model
            if models:
                return models[0].model_id
            
            # Fallback to default
            return "eleven_multilingual_v2"
            
        except Exception as e:
            # Fallback to default model
            return "eleven_multilingual_v2"
    
    def generate_speech(self, text: str, output_filename: Optional[str] = None, 
                       voice_settings: Optional[Dict] = None, voice_id: Optional[str] = None,
                       model_id: Optional[str] = None) -> str:
        """
        Generate speech from text using ElevenLabs API.
        
        Args:
            text: The text to convert to speech
            output_filename: Optional filename for the output audio file
            voice_settings: Optional voice settings (stability, similarity_boost, style)
            voice_id: Optional ElevenLabs voice ID (if not provided, will use default)
            model_id: Optional ElevenLabs model ID (if not provided, will use best available)
        
        Returns:
            Path to the generated audio file
        """
        if not output_filename:
            output_filename = f"chad_response_{hash(text) % 10000}.mp3"
        
        output_path = Config.OUTPUT_DIR / output_filename
        
        # Default voice settings optimized for Chad's personality
        default_settings = {
            "stability": 0.49,
            "similarity_boost": 0.75,
            "style": 0.2,
            "use_speaker_boost": True
        }
        
        if voice_settings:
            default_settings.update(voice_settings)
        
        try:
            # Use provided voice_id or default to a common voice
            voice_id_to_use = voice_id or Config.DEFAULT_ELEVENLABS_VOICE_ID
            
            # Use provided model_id or get the best available TTS model
            model_id_to_use = model_id or self.get_best_tts_model()
            
            # Generate speech using the ElevenLabs SDK
            audio_stream = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id_to_use,
                model_id=model_id_to_use,
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
                                voice_settings: Optional[Dict] = None, voice_id: Optional[str] = None,
                                model_id: Optional[str] = None) -> str:
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
            # Use provided voice_id or default to a common voice
            voice_id_to_use = voice_id or Config.DEFAULT_ELEVENLABS_VOICE_ID
            
            # Use provided model_id or get the best available TTS model
            model_id_to_use = model_id or self.get_best_tts_model()
            
            # Generate speech using the ElevenLabs SDK
            audio_stream = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id_to_use,
                model_id=model_id_to_use,
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
        target_voice_id = voice_id or Config.DEFAULT_ELEVENLABS_VOICE_ID
        
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
