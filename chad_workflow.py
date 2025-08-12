import asyncio
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, Union
import logging

from config import Config
from audio_processor import AudioProcessor
from gpt_generator import HotTakeGenerator
from voice_generator import VoiceGenerator
from video_generator import VideoGenerator
from persona_manager import persona_manager
from s3_storage import S3Storage

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChadWorkflow:
    """Main workflow orchestrator for generating hot take videos with multiple personas."""
    
    def __init__(self):
        """Initialize all components."""
        try:
            Config.validate()
            
            self.audio_processor = AudioProcessor()
            self.hot_take_generator = HotTakeGenerator()
            self.voice_generator = VoiceGenerator()
            self.video_generator = VideoGenerator()
            
            # Initialize S3 storage
            self.s3_storage = S3Storage()
            
            logger.info("Digital Twin Workflow initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Digital Twin Workflow: {str(e)}")
            raise
    
    def process_audio_video_input(self, input_file: str, context: Optional[str] = None,
                                 output_filename: Optional[str] = None,
                                 avatar_id: Optional[str] = None,
                                 voice_settings: Optional[Dict] = None,
                                 persona_id: str = "chad_goldstein") -> Dict[str, str]:
        """
        Complete workflow: Audio/Video -> Transcript -> Hot Take -> Voice -> Video
        
        Args:
            input_file: Path to input audio or video file
            context: Optional context to provide with the pitch
            output_filename: Optional base filename for outputs
            avatar_id: Optional specific avatar ID to use
            voice_settings: Optional ElevenLabs voice settings
            persona_id: Persona ID to use for generation
        
        Returns:
            Dictionary with paths to generated files and metadata
        """
        start_time = time.time()
        results = {
            "input_file": input_file,
            "timestamp": int(start_time),
            "status": "processing"
        }
        
        try:
            # Step 1: Process input (audio/video -> transcript)
            logger.info("Step 1: Processing input file...")
            transcript = self.audio_processor.process_input(input_file)
            results["transcript"] = transcript
            logger.info(f"Transcript generated: {len(transcript)} characters")
            
            # Step 2: Generate hot take
            logger.info("Step 2: Generating hot take...")
            hot_take_result = self.hot_take_generator.generate_hot_take(transcript, context, persona_id)
            results["hot_take"] = hot_take_result["hot_take"]
            results["openai_latency"] = hot_take_result["latency_seconds"]
            results["openai_tokens"] = hot_take_result["total_tokens"]
            logger.info(f"Hot take generated: {len(hot_take_result['hot_take'])} characters in {hot_take_result['latency_seconds']:.2f}s")
            
            # Step 3: Generate voice
            logger.info("Step 3: Generating voice...")
            if not output_filename:
                output_filename = f"chad_response_{int(start_time)}"
            
            # Get persona's voice ID
            persona = persona_manager.get_persona(persona_id)
            voice_id = persona.elevenlabs_voice_id if persona else None
            
            audio_filename = f"{output_filename}.mp3"
            audio_path = self.voice_generator.generate_speech(
                hot_take_result["hot_take"], 
                audio_filename, 
                voice_settings,
                voice_id
            )
            results["audio_path"] = audio_path
            logger.info(f"Audio generated: {audio_path}")
            
            # Step 4: Generate video
            logger.info("Step 4: Generating video...")
            video_filename = f"{output_filename}.mp4"
            
            # Get persona details for video generation
            persona = persona_manager.get_persona(persona_id)
            persona_name = persona.name if persona else None
            talking_photo_id = avatar_id or (persona.heygen_avatar_id if persona else None)
            
            video_path = self.video_generator.generate_complete_video(
                audio_path,
                video_filename,
                talking_photo_id,
                persona_name
            )
            results["video_path"] = video_path
            logger.info(f"Video generated: {video_path}")
            
            # Step 5: Upload files to S3 with permanent public URLs
            logger.info("Step 5: Uploading files to S3 with permanent public URLs...")
            try:
                # Upload audio file to S3 with permanent URL
                audio_s3_key = f"audio/{output_filename}.mp3"
                audio_url = self.upload_file_to_s3(audio_path, audio_s3_key, "audio/mpeg")
                results["audio_url"] = audio_url
                
                # Upload video file to S3 with permanent URL
                video_s3_key = f"videos/{output_filename}.mp4"
                video_url = self.upload_file_to_s3(video_path, video_s3_key, "video/mp4")
                results["video_url"] = video_url
                
                # Keep local paths for reference but prioritize S3 URLs
                results["audio_path"] = audio_path
                results["video_path"] = video_path
                
                logger.info(f"Files uploaded to S3 with permanent URLs: audio={audio_url}, video={video_url}")
                
            except Exception as e:
                logger.error(f"Failed to upload files to S3: {e}")
                # Use local paths as fallback
                results["audio_url"] = audio_path
                results["video_url"] = video_path
            
            # Final results
            results["status"] = "completed"
            results["processing_time"] = time.time() - start_time
            
            logger.info(f"Workflow completed in {results['processing_time']:.2f} seconds")
            return results
            
        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            results["processing_time"] = time.time() - start_time
            logger.error(f"Workflow failed: {str(e)}")
            raise
    
    def process_text_input(self, text: str, context: Optional[str] = None,
                          output_filename: Optional[str] = None,
                          avatar_id: Optional[str] = None,
                          voice_settings: Optional[Dict] = None,
                          persona_id: str = "chad_goldstein") -> Dict[str, str]:
        """
        Workflow for text input: Text -> Hot Take -> Voice -> Video
        
        Args:
            text: Input text (pitch or topic)
            context: Optional context to provide
            output_filename: Optional base filename for outputs
            avatar_id: Optional specific avatar ID to use
            voice_settings: Optional ElevenLabs voice settings
            persona_id: Persona ID to use for generation
        
        Returns:
            Dictionary with paths to generated files and metadata
        """
        start_time = time.time()
        results = {
            "input_text": text,
            "timestamp": int(start_time),
            "status": "processing"
        }
        
        try:
            # Step 1: Generate hot take
            logger.info("Step 1: Generating hot take from text...")
            hot_take_result = self.hot_take_generator.generate_hot_take(text, context, persona_id)
            results["hot_take"] = hot_take_result["hot_take"]
            results["openai_latency"] = hot_take_result["latency_seconds"]
            results["openai_tokens"] = hot_take_result["total_tokens"]
            logger.info(f"Hot take generated: {len(hot_take_result['hot_take'])} characters in {hot_take_result['latency_seconds']:.2f}s")
            
            # Step 2: Generate voice
            logger.info("Step 2: Generating voice...")
            if not output_filename:
                output_filename = f"chad_text_response_{int(start_time)}"
            
            # Get persona's voice ID
            persona = persona_manager.get_persona(persona_id)
            elevenlabs_voice_id = persona.elevenlabs_voice_id if persona else None
            
            # Check if persona has ElevenLabs voice ID, if not, use HeyGen voice
            if elevenlabs_voice_id is None:
                logger.info("No ElevenLabs voice ID found for persona, using HeyGen voice instead")
                results["voice_provider"] = "heygen"
                
                # Generate video directly from text using HeyGen's voice
                video_filename = f"{output_filename}.mp4"
                
                # Get persona details for video generation
                persona_name = persona.name if persona else None
                talking_photo_id = avatar_id or (persona.heygen_avatar_id if persona else None)
                target_voice_id = persona.heygen_voice_id if persona else None
                
                video_path = self.video_generator.generate_complete_video_from_text(
                    hot_take_result["hot_take"], 
                    video_filename, 
                    talking_photo_id,
                    target_voice_id,
                    persona_name
                )
                results["video_path"] = video_path
                results["voice_id"] = target_voice_id or "default"
                logger.info(f"Video generated with HeyGen voice: {video_path}")
            else:
                # Use ElevenLabs voice
                results["voice_provider"] = "elevenlabs"
                
                audio_filename = f"{output_filename}.mp3"
                audio_path = self.voice_generator.generate_speech(
                    hot_take_result["hot_take"], 
                    audio_filename, 
                    voice_settings,
                    elevenlabs_voice_id
                )
                results["audio_path"] = audio_path
                logger.info(f"Audio generated: {audio_path}")
                
                # Step 3: Generate video
                logger.info("Step 3: Generating video...")
                video_filename = f"{output_filename}.mp4"
                
                # Get persona details for video generation
                persona_name = persona.name if persona else None
                talking_photo_id = avatar_id or (persona.heygen_avatar_id if persona else None)
                
                video_path = self.video_generator.generate_complete_video(
                    audio_path,
                    video_filename,
                    talking_photo_id,
                    persona_name
                )
                results["video_path"] = video_path
                logger.info(f"Video generated: {video_path}")
                
                # Upload files to S3
                logger.info("Uploading files to S3...")
                try:
                    # Upload audio file to S3
                    audio_s3_key = f"audio/{output_filename}.mp3"
                    audio_url = self.upload_file_to_s3(audio_path, audio_s3_key, "audio/mpeg")
                    results["audio_url"] = audio_url
                    
                    # Upload video file to S3
                    video_s3_key = f"videos/{output_filename}.mp4"
                    video_url = self.upload_file_to_s3(video_path, video_s3_key, "video/mp4")
                    results["video_url"] = video_url
                    
                    logger.info(f"Files uploaded to S3: audio={audio_url}, video={video_url}")
                    
                except Exception as e:
                    logger.error(f"Failed to upload files to S3: {e}")
                    # Continue without S3 upload if it fails
            
            # Final results
            results["status"] = "completed"
            results["processing_time"] = time.time() - start_time
            
            logger.info(f"Text workflow completed in {results['processing_time']:.2f} seconds")
            return results
            
        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            results["processing_time"] = time.time() - start_time
            logger.error(f"Text workflow failed: {str(e)}")
            raise
    
    def process_text_input_heygen_voice(self, text: str, context: Optional[str] = None,
                                       output_filename: Optional[str] = None,
                                       avatar_id: Optional[str] = None,
                                       voice_id: Optional[str] = None,
                                       persona_id: str = "chad_goldstein") -> Dict[str, str]:
        """
        Complete workflow using HeyGen's text-to-speech: Text -> Hot Take -> Video (with HeyGen voice)
        
        Args:
            text: Input text to generate hot take from
            context: Optional context to provide with the pitch
            output_filename: Optional base filename for outputs
            avatar_id: Optional specific avatar ID to use
            voice_id: Optional HeyGen voice ID to use
            persona_id: Persona ID to use for generation
        
        Returns:
            Dictionary with paths to generated files and metadata
        """
        start_time = time.time()
        results = {
            "input_text": text,
            "timestamp": int(start_time),
            "status": "processing",
            "voice_provider": "heygen"
        }
        
        try:
            # Step 1: Generate hot take
            logger.info("Step 1: Generating hot take...")
            hot_take_result = self.hot_take_generator.generate_hot_take(text, context, persona_id)
            results["hot_take"] = hot_take_result["hot_take"]
            results["openai_latency"] = hot_take_result["latency_seconds"]
            results["openai_tokens"] = hot_take_result["total_tokens"]
            logger.info(f"Hot take generated: {len(hot_take_result['hot_take'])} characters in {hot_take_result['latency_seconds']:.2f}s")
            
            # Step 2: Generate video directly from text using HeyGen's voice
            logger.info("Step 2: Generating video with HeyGen voice...")
            if not output_filename:
                output_filename = f"chad_response_{int(start_time)}"
            
            video_filename = f"{output_filename}.mp4"
            
            # Get persona details for video generation
            persona = persona_manager.get_persona(persona_id)
            persona_name = persona.name if persona else None
            talking_photo_id = avatar_id or (persona.heygen_avatar_id if persona else None)
            target_voice_id = voice_id or (persona.heygen_voice_id if persona else None)
            
            video_path = self.video_generator.generate_complete_video_from_text(
                hot_take_result["hot_take"], 
                video_filename, 
                talking_photo_id,
                target_voice_id,
                persona_name
            )
            results["video_path"] = video_path
            results["voice_id"] = voice_id or "default"
            logger.info(f"Video generated with HeyGen voice: {video_path}")
            
            # Upload video to S3 with permanent public URL
            logger.info("Uploading video to S3 with permanent public URL...")
            try:
                video_s3_key = f"videos/{output_filename}.mp4"
                video_url = self.upload_file_to_s3(video_path, video_s3_key, "video/mp4")
                results["video_url"] = video_url
                results["video_path"] = video_path
                logger.info(f"Video uploaded to S3 with permanent URL: {video_url}")
                
            except Exception as e:
                logger.error(f"Failed to upload video to S3: {e}")
                # Use local path as fallback
                results["video_url"] = video_path
            
            # Calculate total processing time
            total_time = time.time() - start_time
            results["total_processing_time"] = total_time
            results["status"] = "completed"
            
            logger.info(f"✅ Complete workflow with HeyGen voice finished in {total_time:.2f}s")
            return results
            
        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            logger.error(f"❌ Workflow failed: {str(e)}")
            raise
    
    def quick_roast(self, topic: str, output_filename: Optional[str] = None,
                   avatar_id: Optional[str] = None,
                   persona_id: str = "chad_goldstein") -> Dict[str, str]:
        """
        Quick roast workflow: Topic -> Quick Roast -> Voice -> Video
        
        Args:
            topic: Topic to roast
            output_filename: Optional base filename for outputs
            avatar_id: Optional specific avatar ID to use
            persona_id: Persona ID to use for generation
        
        Returns:
            Dictionary with paths to generated files and metadata
        """
        start_time = time.time()
        results = {
            "topic": topic,
            "timestamp": int(start_time),
            "status": "processing"
        }
        
        try:
            # Step 1: Generate quick roast
            logger.info(f"Step 1: Generating quick roast for: {topic}")
            roast_result = self.hot_take_generator.generate_quick_roast(topic, persona_id)
            results["roast"] = roast_result["roast"]
            results["openai_latency"] = roast_result["latency_seconds"]
            results["openai_tokens"] = roast_result["total_tokens"]
            logger.info(f"Quick roast generated: {len(roast_result['roast'])} characters in {roast_result['latency_seconds']:.2f}s")
            
            # Step 2: Generate voice (faster streaming version)
            logger.info("Step 2: Generating voice (streaming)...")
            if not output_filename:
                output_filename = f"chad_roast_{int(start_time)}"
            
            # Get persona's voice ID
            persona = persona_manager.get_persona(persona_id)
            elevenlabs_voice_id = persona.elevenlabs_voice_id if persona else None
            
            # Check if persona has ElevenLabs voice ID, if not, use HeyGen voice
            if elevenlabs_voice_id is None:
                logger.info("No ElevenLabs voice ID found for persona, using HeyGen voice instead")
                results["voice_provider"] = "heygen"
                
                # Generate video directly from text using HeyGen's voice
                video_filename = f"{output_filename}.mp4"
                
                # Get persona details for video generation
                persona_name = persona.name if persona else None
                talking_photo_id = avatar_id or (persona.heygen_avatar_id if persona else None)
                target_voice_id = persona.heygen_voice_id if persona else None
                
                video_path = self.video_generator.generate_complete_video_from_text(
                    roast_result["roast"], 
                    video_filename, 
                    talking_photo_id,
                    target_voice_id,
                    persona_name
                )
                results["video_path"] = video_path
                results["voice_id"] = target_voice_id or "default"
                logger.info(f"Video generated with HeyGen voice: {video_path}")
                
                # Upload video to S3
                logger.info("Uploading video to S3...")
                try:
                    video_s3_key = f"videos/{output_filename}.mp4"
                    video_url = self.upload_file_to_s3(video_path, video_s3_key, "video/mp4")
                    results["video_url"] = video_url
                    logger.info(f"Video uploaded to S3: {video_url}")
                    
                except Exception as e:
                    logger.error(f"Failed to upload video to S3: {e}")
                    # Continue without S3 upload if it fails
                    
            else:
                # Use ElevenLabs voice
                results["voice_provider"] = "elevenlabs"
                
                audio_filename = f"{output_filename}.mp3"
                audio_path = self.voice_generator.generate_speech_streaming(roast_result["roast"], audio_filename, voice_id=elevenlabs_voice_id)
                results["audio_path"] = audio_path
                logger.info(f"Audio generated: {audio_path}")
                
                # Step 3: Generate video
                logger.info("Step 3: Generating video...")
                video_filename = f"{output_filename}.mp4"
                
                # Get persona details for video generation
                persona_name = persona.name if persona else None
                talking_photo_id = avatar_id or (persona.heygen_avatar_id if persona else None)
                
                video_path = self.video_generator.generate_complete_video(
                    audio_path,
                    video_filename,
                    talking_photo_id,
                    persona_name
                )
                results["video_path"] = video_path
                logger.info(f"Video generated: {video_path}")
                
                # Upload files to S3 with permanent public URLs
                logger.info("Uploading files to S3 with permanent public URLs...")
                try:
                    # Upload audio file to S3 with permanent URL
                    audio_s3_key = f"audio/{output_filename}.mp3"
                    audio_url = self.upload_file_to_s3(audio_path, audio_s3_key, "audio/mpeg")
                    results["audio_url"] = audio_url
                    
                    # Upload video file to S3 with permanent URL
                    video_s3_key = f"videos/{output_filename}.mp4"
                    video_url = self.upload_file_to_s3(video_path, video_s3_key, "video/mp4")
                    results["video_url"] = video_url
                    
                    logger.info(f"Files uploaded to S3 with permanent URLs: audio={audio_url}, video={video_url}")
                    
                except Exception as e:
                    logger.error(f"Failed to upload files to S3: {e}")
                    # Use local paths as fallback
                    results["audio_url"] = audio_path
                    results["video_url"] = video_path
            
            # Final results
            results["status"] = "completed"
            results["processing_time"] = time.time() - start_time
            
            logger.info(f"Quick roast completed in {results['processing_time']:.2f} seconds")
            return results
            
        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            results["processing_time"] = time.time() - start_time
            logger.error(f"Quick roast failed: {str(e)}")
            raise
    
    def test_all_services(self) -> Dict[str, bool]:
        """Test all service connections."""
        results = {}
        
        logger.info("Testing service connections...")
        
        # Test OpenAI
        try:
            results["openai"] = self.hot_take_generator.test_connection()
            logger.info(f"OpenAI connection: {'✓' if results['openai'] else '✗'}")
        except Exception as e:
            results["openai"] = False
            logger.error(f"OpenAI test failed: {str(e)}")
        
        # Test ElevenLabs
        try:
            results["elevenlabs"] = self.voice_generator.test_connection()
            logger.info(f"ElevenLabs connection: {'✓' if results['elevenlabs'] else '✗'}")
        except Exception as e:
            results["elevenlabs"] = False
            logger.error(f"ElevenLabs test failed: {str(e)}")
        
        # Test HeyGen
        try:
            results["heygen"] = self.video_generator.test_connection()
            logger.info(f"HeyGen connection: {'✓' if results['heygen'] else '✗'}")
        except Exception as e:
            results["heygen"] = False
            logger.error(f"HeyGen test failed: {str(e)}")
        
        return results
    
    def upload_file_to_s3(self, local_path: str, s3_key: str, content_type: Optional[str] = None) -> str:
        """
        Upload a file to S3 and return a permanent public URL for direct access.
        
        Args:
            local_path: Local path to the file
            s3_key: S3 object key (path in bucket)
            content_type: Optional content type for the file
            
        Returns:
            Permanent S3 URL for direct file access
        """
        try:
            if not os.path.exists(local_path):
                logger.warning(f"Local file not found: {local_path}")
                return local_path
            
            # Ensure we have the correct content type for our file types
            if not content_type:
                content_type = self._get_content_type_for_file(local_path, s3_key)
            
            # Upload file to S3 with public read access and proper MIME type
            s3_url = self.s3_storage.upload_file(local_path, s3_key, content_type)
            logger.info(f"File uploaded to S3 with permanent URL and content type '{content_type}': {local_path} -> {s3_url}")
            return s3_url
            
        except Exception as e:
            logger.error(f"Failed to upload file to S3: {local_path} -> {s3_key}: {e}")
            # Return local path as fallback
            return local_path
    
    def _get_content_type_for_file(self, local_path: str, s3_key: str) -> str:
        """
        Get the appropriate content type for our specific file types.
        
        Args:
            local_path: Local file path
            s3_key: S3 object key
            
        Returns:
            MIME type string
        """
        # Determine content type based on file extension
        file_ext = os.path.splitext(s3_key.lower())[1]
        
        content_types = {
            '.mp3': 'audio/mpeg',
            '.mp4': 'video/mp4',
            '.wav': 'audio/wav',
            '.m4a': 'audio/mp4',
            '.aac': 'audio/aac',
            '.ogg': 'audio/ogg',
            '.webm': 'video/webm',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.mkv': 'video/x-matroska',
            '.flv': 'video/x-flv',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.svg': 'image/svg+xml',
            '.pdf': 'application/pdf',
            '.txt': 'text/plain',
            '.json': 'application/json'
        }
        
        return content_types.get(file_ext, 'application/octet-stream')
    
    def cleanup_files(self):
        """Clean up temporary and old output files."""
        logger.info("Cleaning up files...")
        
        # Clean up temporary audio files
        self.audio_processor.cleanup_temp_files()
        
        # Clean up old audio files
        self.voice_generator.cleanup_audio_files()
        
        # Clean up old video files
        self.video_generator.cleanup_video_files()
        
        logger.info("File cleanup completed")
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about available services and settings."""
        info = {
            "config": {
                "temp_dir": str(Config.TEMP_DIR),
                "output_dir": str(Config.OUTPUT_DIR),
                "max_file_size_mb": Config.MAX_FILE_SIZE_MB
            }
        }
        
        # Get ElevenLabs voice count instead of all voices
        try:
            all_voices = self.voice_generator.get_available_voices()
            info["elevenlabs_voices_count"] = len(all_voices) if isinstance(all_voices, list) else 0
            info["elevenlabs_voices_available"] = True
        except Exception as e:
            info["elevenlabs_error"] = str(e)
            info["elevenlabs_voices_available"] = False
        
        # Get HeyGen avatar count instead of all avatars
        try:
            all_avatars = self.video_generator.get_avatars()
            info["heygen_avatars_count"] = len(all_avatars.get("data", [])) if isinstance(all_avatars, dict) and "data" in all_avatars else 0
            info["heygen_avatars_available"] = True
        except Exception as e:
            info["heygen_error"] = str(e)
            info["heygen_avatars_available"] = False
        
        return info
