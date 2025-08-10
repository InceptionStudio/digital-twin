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
            
            audio_filename = f"{output_filename}.mp3"
            audio_path = self.voice_generator.generate_speech(
                hot_take_result["hot_take"], 
                audio_filename, 
                voice_settings
            )
            results["audio_path"] = audio_path
            logger.info(f"Audio generated: {audio_path}")
            
            # Step 4: Generate video
            logger.info("Step 4: Generating video...")
            video_filename = f"{output_filename}.mp4"
            video_path = self.video_generator.generate_complete_video(
                audio_path,
                video_filename,
                avatar_id
            )
            results["video_path"] = video_path
            logger.info(f"Video generated: {video_path}")
            
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
            
            audio_filename = f"{output_filename}.mp3"
            audio_path = self.voice_generator.generate_speech(
                hot_take_result["hot_take"], 
                audio_filename, 
                voice_settings
            )
            results["audio_path"] = audio_path
            logger.info(f"Audio generated: {audio_path}")
            
            # Step 3: Generate video
            logger.info("Step 3: Generating video...")
            video_filename = f"{output_filename}.mp4"
            video_path = self.video_generator.generate_complete_video(
                audio_path,
                video_filename,
                avatar_id
            )
            results["video_path"] = video_path
            logger.info(f"Video generated: {video_path}")
            
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
            video_path = self.video_generator.generate_complete_video_from_text(
                hot_take_result["hot_take"], 
                video_filename, 
                avatar_id,
                voice_id
            )
            results["video_path"] = video_path
            results["voice_id"] = voice_id or "default"
            logger.info(f"Video generated with HeyGen voice: {video_path}")
            
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
            
            audio_filename = f"{output_filename}.mp3"
            audio_path = self.voice_generator.generate_speech_streaming(roast_result["roast"], audio_filename)
            results["audio_path"] = audio_path
            logger.info(f"Audio generated: {audio_path}")
            
            # Step 3: Generate video
            logger.info("Step 3: Generating video...")
            video_filename = f"{output_filename}.mp4"
            video_path = self.video_generator.generate_complete_video(
                audio_path,
                video_filename,
                avatar_id
            )
            results["video_path"] = video_path
            logger.info(f"Video generated: {video_path}")
            
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
        
        # Get ElevenLabs voices
        try:
            info["elevenlabs_voices"] = self.voice_generator.get_available_voices()
        except Exception as e:
            info["elevenlabs_error"] = str(e)
        
        # Get HeyGen avatars
        try:
            info["heygen_avatars"] = self.video_generator.get_avatars()
        except Exception as e:
            info["heygen_error"] = str(e)
        
        return info
