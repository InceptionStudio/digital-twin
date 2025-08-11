import requests
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any, Union
from config import Config

class VideoGenerator:
    def __init__(self):
        self.api_key = Config.HEYGEN_API_KEY
        self.talking_photo_id = Config.DEFAULT_HEYGEN_AVATAR_ID  # Using avatar_id config for talking_photo_id
        self.default_voice_id = Config.DEFAULT_HEYGEN_VOICE_ID  # Default voice ID
        self.base_url = "https://api.heygen.com/v2"
        
        if not self.api_key:
            raise ValueError("HeyGen API key not found in configuration")
    
    def get_avatars(self) -> Dict[str, Any]:
        """Get list of available avatars."""
        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(f"{self.base_url}/avatars", headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Failed to fetch avatars: {str(e)}")
    
    def get_voices(self) -> Dict[str, Any]:
        """Get list of available voices."""
        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(f"{self.base_url}/voices", headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Failed to fetch voices: {str(e)}")
    
    def create_video_from_text(self, text: str, output_filename: Optional[str] = None,
                              talking_photo_id: Optional[str] = None,
                              voice_id: Optional[str] = None,
                              background: Optional[str] = None,
                              persona_name: Optional[str] = None) -> str:
        """
        Create video from text using HeyGen Talking Photo V2 API.
        
        Args:
            text: The text for the talking photo to speak
            output_filename: Optional filename for the output video
            talking_photo_id: Optional specific talking photo ID to use
            voice_id: Optional voice ID (if different from default)
            background: Optional background setting
        
        Returns:
            Video ID for tracking the generation process
        """
        target_talking_photo_id = talking_photo_id or self.talking_photo_id
        
        # Debug: Print all parameters
        print(f"🔍 DEBUG - create_video_from_text:")
        print(f"   talking_photo_id parameter: {talking_photo_id}")
        print(f"   self.talking_photo_id (default): {self.talking_photo_id}")
        print(f"   target_talking_photo_id (final): {target_talking_photo_id}")
        print(f"   persona_name: {persona_name}")
        print(f"   voice_id: {voice_id}")
        print(f"   self.default_voice_id: {self.default_voice_id}")
        
        if not target_talking_photo_id:
            raise ValueError("Talking Photo ID not specified in config or parameters")
        
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-key": self.api_key
        }
        
        # Video data according to HeyGen V2 API specification
        title = f"{persona_name or 'Digital Twin'} Hot Take"
        video_data = {
            "caption": False,
            "title": title,
            "dimension": {
                "width": 1280,
                "height": 720
            },
            "video_inputs": [
                {
                    "character": {
                        "type": "talking_photo",
                        "talking_photo_id": target_talking_photo_id,
                        "scale": 1.0,
                        "talking_photo_style": "square",
                        "offset": {
                            "x": 0.0,
                            "y": 0.0
                        },
                        "talking_style": "stable",
                        "expression": "default",
                        "super_resolution": True,
                        "matting": True
                    },
                    "voice": {
                        "type": "text",
                        "voice_id": voice_id or self.default_voice_id,
                        "input_text": text,
                        "speed": 1,
                        "pitch": 0,
                        "emotion": "Excited"
                    }
                }
            ]
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/video/generate",
                headers=headers,
                json=video_data
            )
            response.raise_for_status()
            result = response.json()
            
            # Debug: print the full response
            print(f"HeyGen API Response (text): {result}")
            
            if result.get("error") is not None:
                raise Exception(f"HeyGen API error: {result['error']}")
            
            video_id = result.get("data", {}).get("video_id")
            if not video_id:
                raise Exception("No video ID returned from HeyGen API")
            
            return video_id
            
        except Exception as e:
            raise Exception(f"Failed to create video from text: {str(e)}")
    
    def create_video_from_audio(self, audio_path: str, output_filename: Optional[str] = None,
                               talking_photo_id: Optional[str] = None,
                               background: Optional[str] = None,
                               persona_name: Optional[str] = None) -> str:
        """
        Create video from audio file using HeyGen Talking Photo V2 API.
        
        Args:
            audio_path: Path to the audio file
            output_filename: Optional filename for the output video
            talking_photo_id: Optional specific talking photo ID to use
            background: Optional background setting
        
        Returns:
            Video ID for tracking the generation process
        """
        target_talking_photo_id = talking_photo_id or self.talking_photo_id
        
        # Debug: Print all parameters
        print(f"🔍 DEBUG - create_video_from_audio:")
        print(f"   talking_photo_id parameter: {talking_photo_id}")
        print(f"   self.talking_photo_id (default): {self.talking_photo_id}")
        print(f"   target_talking_photo_id (final): {target_talking_photo_id}")
        print(f"   persona_name: {persona_name}")
        print(f"   audio_path: {audio_path}")
        
        if not target_talking_photo_id:
            raise ValueError("Talking Photo ID not specified in config or parameters")
        
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # First upload the audio file
        audio_asset_id = self._upload_audio(audio_path)
        
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-key": self.api_key
        }
        
        # Video data according to HeyGen V2 API specification
        title = f"{persona_name or 'Digital Twin'} Hot Take"
        video_data = {
            "caption": False,
            "title": title,
            "dimension": {
                "width": 1280,
                "height": 720
            },
            "video_inputs": [
                {
                    "character": {
                        "type": "talking_photo",
                        "talking_photo_id": target_talking_photo_id,
                        "scale": 1.0,
                        "talking_photo_style": "square",
                        "offset": {
                            "x": 0.0,
                            "y": 0.0
                        },
                        "talking_style": "stable",
                        "expression": "default",
                        "super_resolution": True,
                        "matting": True
                    },
                    "voice": {
                        "type": "audio",
                        "audio_asset_id": audio_asset_id
                    }
                }
            ]
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/video/generate",
                headers=headers,
                json=video_data
            )
            response.raise_for_status()
            result = response.json()
            
            # Debug: print the full response
            print(f"HeyGen API Response (audio): {result}")
            
            if result.get("error") is not None:
                raise Exception(f"HeyGen API error: {result['error']}")
            
            video_id = result.get("data", {}).get("video_id")
            if not video_id:
                raise Exception("No video ID returned from HeyGen API")
            
            return video_id
            
        except Exception as e:
            raise Exception(f"Failed to create video from audio: {str(e)}")
    
    def _upload_audio(self, audio_path: str) -> str:
        """
        Upload audio file to HeyGen and return asset ID.
        
        Args:
            audio_path: Path to the audio file
        
        Returns:
            Asset ID of the uploaded audio
        """
        headers = {
            "Content-Type": "audio/mpeg",
            "X-Api-Key": self.api_key
        }
        
        try:
            with open(audio_path, 'rb') as audio_file:
                response = requests.post(
                    "https://upload.heygen.com/v1/asset",
                    headers=headers,
                    data=audio_file
                )
                response.raise_for_status()
                result = response.json()
                
                # Handle the HeyGen API response structure
                if result.get("code") == 100:
                    asset_id = result.get("data", {}).get("id")
                    if not asset_id:
                        raise Exception("No asset ID returned from HeyGen upload")
                    return asset_id
                else:
                    raise Exception(f"HeyGen upload error: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            raise Exception(f"Failed to upload audio: {str(e)}")
    
    def get_video_status(self, video_id: str) -> Dict[str, Any]:
        """Get the status of a video generation using the correct HeyGen API."""
        headers = {
            "X-Api-Key": self.api_key,
            "accept": "application/json"
        }
        
        try:
            response = requests.get(
                "https://api.heygen.com/v1/video_status.get",
                headers=headers,
                params={"video_id": video_id}
            )
            response.raise_for_status()
            result = response.json()
            
            # Handle the HeyGen API response structure
            if result.get("code") == 100:
                return result.get("data", {})
            else:
                raise Exception(f"HeyGen API error: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            raise Exception(f"Failed to get video status: {str(e)}")
    
    def wait_for_video_completion(self, video_id: str, max_wait_time: int = 1200,
                                 check_interval: int = 2) -> Dict[str, Any]:
        """
        Wait for video generation to complete.
        
        Args:
            video_id: The video ID to check
            max_wait_time: Maximum time to wait in seconds (default: 1200)
            check_interval: How often to check status in seconds (default: 2)
        
        Returns:
            Final video status
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                status = self.get_video_status(video_id)
                current_status = status.get("status", "unknown")
                
                # Check if video is complete
                if current_status == "completed":
                    print(f"✅ Video completed successfully! ID: {video_id}")
                    return status
                elif current_status == "failed":
                    error_info = status.get("error", {})
                    error_message = error_info.get("message", "Unknown error")
                    error_detail = error_info.get("detail", "")
                    raise Exception(f"Video generation failed: {error_message} - {error_detail}")
                
                # Print status for debugging
                print(f"🔄 Video status: {current_status} - ID: {video_id}")
                
                # Wait before checking again
                time.sleep(check_interval)
                
            except Exception as e:
                print(f"❌ Error checking video status: {str(e)}")
                time.sleep(check_interval)
        
        raise Exception(f"Video generation timed out after {max_wait_time} seconds")
    
    def download_video(self, video_url: str, output_filename: Optional[str] = None) -> str:
        """
        Download the generated video.
        
        Args:
            video_url: URL of the video to download
            output_filename: Optional filename for the output video
        
        Returns:
            Path to the downloaded video file
        """
        if not output_filename:
            output_filename = f"chad_video_{int(time.time())}.mp4"
        
        output_path = Config.OUTPUT_DIR / output_filename
        
        try:
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return str(output_path)
            
        except Exception as e:
            raise Exception(f"Failed to download video: {str(e)}")
    
    def generate_complete_video(self, audio_path: str, output_filename: Optional[str] = None,
                               talking_photo_id: Optional[str] = None,
                               persona_name: Optional[str] = None) -> str:
        """
        Generate a complete video from audio file and download it.
        
        Args:
            audio_path: Path to the audio file
            output_filename: Optional filename for the output video
            talking_photo_id: Optional specific talking photo ID to use
        
        Returns:
            Path to the generated video file
        """
        # Create video from audio
        video_id = self.create_video_from_audio(audio_path, output_filename, talking_photo_id, persona_name=persona_name)
        
        # Wait for completion
        final_status = self.wait_for_video_completion(video_id)
        
        # Download the video
        video_url = final_status.get("video_url")
        if not video_url:
            raise Exception("No video URL in final status")
        
        return self.download_video(video_url, output_filename)
    
    def generate_complete_video_from_text(self, text: str, output_filename: Optional[str] = None,
                                         talking_photo_id: Optional[str] = None,
                                         voice_id: Optional[str] = None,
                                         persona_name: Optional[str] = None) -> str:
        """
        Generate a complete video directly from text using HeyGen's voice synthesis.
        
        Args:
            text: The text for the talking photo to speak
            output_filename: Optional filename for the output video
            talking_photo_id: Optional specific talking photo ID to use
            voice_id: Optional voice ID to use
        
        Returns:
            Path to the generated video file
        """
        # Create video from text
        video_id = self.create_video_from_text(text, output_filename, talking_photo_id, voice_id, persona_name=persona_name)
        
        # Wait for completion
        final_status = self.wait_for_video_completion(video_id)
        
        # Download the video
        video_url = final_status.get("video_url")
        if not video_url:
            raise Exception("No video URL in final status")
        
        return self.download_video(video_url, output_filename)
    
    def test_connection(self) -> bool:
        """Test the HeyGen API connection."""
        try:
            self.get_avatars()
            return True
        except Exception:
            return False
    
    def cleanup_video_files(self, keep_latest: int = 3):
        """Clean up old video files, keeping only the most recent ones."""
        video_files = list(Config.OUTPUT_DIR.glob("chad_video_*.mp4"))
        video_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Remove all but the most recent files
        for file_to_remove in video_files[keep_latest:]:
            try:
                file_to_remove.unlink()
            except Exception:
                pass  # Ignore cleanup errors
