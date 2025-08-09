import requests
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any, Union
from config import Config

class VideoGenerator:
    def __init__(self):
        self.api_key = Config.HEYGEN_API_KEY
        self.avatar_id = Config.HEYGEN_AVATAR_ID
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
    
    def create_video_from_text(self, text: str, output_filename: Optional[str] = None,
                              avatar_id: Optional[str] = None,
                              voice_id: Optional[str] = None,
                              background: Optional[str] = None) -> str:
        """
        Create video from text using HeyGen Avatar IV.
        
        Args:
            text: The text for the avatar to speak
            output_filename: Optional filename for the output video
            avatar_id: Optional specific avatar ID to use
            voice_id: Optional voice ID (if different from default)
            background: Optional background setting
        
        Returns:
            Video ID for tracking the generation process
        """
        target_avatar_id = avatar_id or self.avatar_id
        
        if not target_avatar_id:
            raise ValueError("Avatar ID not specified in config or parameters")
        
        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        # Default video settings optimized for Chad's personality
        video_data = {
            "video_inputs": [
                {
                    "character": {
                        "type": "avatar",
                        "avatar_id": target_avatar_id,
                        "avatar_style": "normal"
                    },
                    "voice": {
                        "type": "text",
                        "input_text": text,
                        "voice_id": voice_id or "default"
                    },
                    "background": {
                        "type": background or "color",
                        "value": "#1a1a1a" if not background else background
                    }
                }
            ],
            "dimension": {
                "width": 1920,
                "height": 1080
            },
            "aspect_ratio": "16:9"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/video/generate",
                headers=headers,
                json=video_data
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("error"):
                raise Exception(f"HeyGen API error: {result['error']}")
            
            video_id = result.get("data", {}).get("video_id")
            if not video_id:
                raise Exception("No video ID returned from HeyGen API")
            
            return video_id
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to create video: {str(e)}")
    
    def create_video_from_audio(self, audio_path: str, output_filename: Optional[str] = None,
                               avatar_id: Optional[str] = None,
                               background: Optional[str] = None) -> str:
        """
        Create video from audio file using HeyGen Avatar IV.
        
        Args:
            audio_path: Path to the audio file
            output_filename: Optional filename for the output video
            avatar_id: Optional specific avatar ID to use
            background: Optional background setting
        
        Returns:
            Video ID for tracking the generation process
        """
        target_avatar_id = avatar_id or self.avatar_id
        
        if not target_avatar_id:
            raise ValueError("Avatar ID not specified in config or parameters")
        
        # First, upload the audio file
        audio_url = self._upload_audio(audio_path)
        
        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        video_data = {
            "video_inputs": [
                {
                    "character": {
                        "type": "avatar",
                        "avatar_id": target_avatar_id,
                        "avatar_style": "normal"
                    },
                    "voice": {
                        "type": "audio",
                        "audio_url": audio_url
                    },
                    "background": {
                        "type": background or "color",
                        "value": "#1a1a1a" if not background else background
                    }
                }
            ],
            "dimension": {
                "width": 1920,
                "height": 1080
            },
            "aspect_ratio": "16:9"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/video/generate",
                headers=headers,
                json=video_data
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("error"):
                raise Exception(f"HeyGen API error: {result['error']}")
            
            video_id = result.get("data", {}).get("video_id")
            if not video_id:
                raise Exception("No video ID returned from HeyGen API")
            
            return video_id
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to create video from audio: {str(e)}")
    
    def _upload_audio(self, audio_path: str) -> str:
        """Upload audio file to HeyGen and return the URL."""
        headers = {
            "X-Api-Key": self.api_key
        }
        
        with open(audio_path, 'rb') as audio_file:
            files = {
                'file': ('audio.mp3', audio_file, 'audio/mpeg')
            }
            
            try:
                response = requests.post(
                    f"{self.base_url}/assets/upload",
                    headers=headers,
                    files=files
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get("error"):
                    raise Exception(f"Upload error: {result['error']}")
                
                return result.get("data", {}).get("url")
                
            except requests.exceptions.RequestException as e:
                raise Exception(f"Failed to upload audio: {str(e)}")
    
    def get_video_status(self, video_id: str) -> Dict[str, Any]:
        """Check the status of video generation."""
        headers = {
            "X-Api-Key": self.api_key
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/video/{video_id}",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Failed to get video status: {str(e)}")
    
    def wait_for_video_completion(self, video_id: str, max_wait_time: int = 600,
                                 check_interval: int = 10) -> Dict[str, Any]:
        """
        Wait for video generation to complete.
        
        Args:
            video_id: The video ID to monitor
            max_wait_time: Maximum time to wait in seconds
            check_interval: How often to check status in seconds
        
        Returns:
            Final video status with download URL
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status = self.get_video_status(video_id)
            
            video_status = status.get("data", {}).get("status")
            
            if video_status == "completed":
                return status
            elif video_status == "failed":
                error_msg = status.get("data", {}).get("error", "Unknown error")
                raise Exception(f"Video generation failed: {error_msg}")
            
            time.sleep(check_interval)
        
        raise TimeoutError(f"Video generation timed out after {max_wait_time} seconds")
    
    def download_video(self, video_url: str, output_filename: Optional[str] = None) -> str:
        """Download the generated video."""
        if not output_filename:
            output_filename = f"chad_video_{int(time.time())}.mp4"
        
        output_path = Config.OUTPUT_DIR / output_filename
        
        try:
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return str(output_path)
            
        except Exception as e:
            raise Exception(f"Failed to download video: {str(e)}")
    
    def generate_complete_video(self, audio_path: str, output_filename: Optional[str] = None,
                               avatar_id: Optional[str] = None) -> str:
        """
        Complete workflow: create video from audio and download it.
        
        Returns:
            Path to the downloaded video file
        """
        # Create video
        video_id = self.create_video_from_audio(audio_path, output_filename, avatar_id)
        
        # Wait for completion
        final_status = self.wait_for_video_completion(video_id)
        
        # Get download URL
        video_url = final_status.get("data", {}).get("video_url")
        if not video_url:
            raise Exception("No video URL in completion status")
        
        # Download video
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
