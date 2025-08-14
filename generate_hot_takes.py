#!/usr/bin/env python3
"""
Script to generate hot_take transcripts for jobs missing them.

This script:
1. Finds all jobs in Firestore that are missing results.hot_take
2. Downloads the video from the video_url
3. Runs Whisper to generate a transcript
4. Updates the job with the transcript in results.hot_take
"""

import os
import sys
import logging
import tempfile
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from job_storage import create_job_storage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def download_video(video_url: str, temp_dir: str) -> Optional[str]:
    """
    Download video from URL to temporary file.
    
    Args:
        video_url: URL of the video to download
        temp_dir: Directory to save the video
    
    Returns:
        Path to downloaded video file, or None if failed
    """
    try:
        logger.info(f"Downloading video from: {video_url}")
        
        # Create a temporary file with .mp4 extension
        temp_file = tempfile.NamedTemporaryFile(
            suffix='.mp4', 
            delete=False, 
            dir=temp_dir
        )
        temp_path = temp_file.name
        temp_file.close()
        
        # Download the video
        response = requests.get(video_url, stream=True)
        response.raise_for_status()
        
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = os.path.getsize(temp_path)
        logger.info(f"Downloaded video: {temp_path} ({file_size} bytes)")
        return temp_path
        
    except Exception as e:
        logger.error(f"Failed to download video from {video_url}: {e}")
        return None


def transcribe_video(video_path: str) -> Optional[str]:
    """
    Transcribe video using Whisper.
    
    Args:
        video_path: Path to the video file
    
    Returns:
        Transcript text, or None if failed
    """
    try:
        logger.info(f"Transcribing video: {video_path}")
        
        # Import whisper here to avoid dependency issues
        import whisper
        
        # Load the model (use base model for speed, can be changed to larger models)
        model = whisper.load_model("base")
        
        # Transcribe the video
        result = model.transcribe(video_path)
        
        transcript = result["text"].strip()
        logger.info(f"Generated transcript ({len(transcript)} characters)")
        
        return transcript
        
    except ImportError:
        logger.error("Whisper not installed. Install with: pip install openai-whisper")
        return None
    except Exception as e:
        logger.error(f"Failed to transcribe video {video_path}: {e}")
        return None


def find_jobs_missing_hot_take(job_storage) -> List[Dict]:
    """
    Find all jobs that are missing results.hot_take.
    
    Args:
        job_storage: Firestore job storage instance
    
    Returns:
        List of job data dictionaries
    """
    try:
        logger.info("Finding jobs missing hot_take...")
        
        # Get all jobs from Firestore
        all_jobs = job_storage.list_jobs(limit=1000)
        
        missing_hot_take = []
        for job in all_jobs:
            # Check if job has results and video_url but no hot_take
            results = job.get("results", {})
            video_url = results.get("video_url")
            hot_take = results.get("hot_take")
            
            if video_url and not hot_take:
                missing_hot_take.append(job)
        
        logger.info(f"Found {len(missing_hot_take)} jobs missing hot_take")
        return missing_hot_take
        
    except Exception as e:
        logger.error(f"Failed to find jobs missing hot_take: {e}")
        return []


def update_job_with_hot_take(job_storage, job_id: str, hot_take: str) -> bool:
    """
    Update job with hot_take transcript.
    
    Args:
        job_storage: Firestore job storage instance
        job_id: Job ID to update
        hot_take: Transcript text
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get current job data
        job_data = job_storage.get_job(job_id)
        if not job_data:
            logger.error(f"Job {job_id} not found")
            return False
        
        # Update the results.hot_take field
        if "results" not in job_data:
            job_data["results"] = {}
        
        job_data["results"]["hot_take"] = hot_take
        
        # Update the job
        success = job_storage.update_job(job_id, {
            "results": job_data["results"]
        })
        
        if success:
            logger.info(f"Updated job {job_id} with hot_take")
        else:
            logger.error(f"Failed to update job {job_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to update job {job_id} with hot_take: {e}")
        return False


def main():
    """Main function to process jobs missing hot_take."""
    
    # Check if Firestore credentials are configured
    project_id = os.getenv("FIRESTORE_PROJECT_ID")
    if not project_id:
        logger.error("FIRESTORE_PROJECT_ID environment variable not set")
        return
    
    try:
        # Initialize Firestore storage
        logger.info(f"Initializing Firestore storage with project: {project_id}")
        job_storage = create_job_storage("firestore", firestore_project_id=project_id)
        
        # Find jobs missing hot_take
        jobs_missing_hot_take = find_jobs_missing_hot_take(job_storage)
        
        if not jobs_missing_hot_take:
            logger.info("No jobs found missing hot_take")
            return
        
        # Create temporary directory for video downloads
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"Using temporary directory: {temp_dir}")
            
            processed_count = 0
            failed_count = 0
            
            for job in jobs_missing_hot_take:
                job_id = job.get("id")
                video_url = job.get("results", {}).get("video_url")
                
                if not job_id or not video_url:
                    logger.warning(f"Job {job_id} missing required fields")
                    failed_count += 1
                    continue
                
                logger.info(f"Processing job {job_id}")
                
                try:
                    # Download the video
                    video_path = download_video(video_url, temp_dir)
                    if not video_path:
                        logger.error(f"Failed to download video for job {job_id}")
                        failed_count += 1
                        continue
                    
                    # Generate transcript
                    transcript = transcribe_video(video_path)
                    if not transcript:
                        logger.error(f"Failed to transcribe video for job {job_id}")
                        failed_count += 1
                        continue
                    
                    # Update job with hot_take
                    success = update_job_with_hot_take(job_storage, job_id, transcript)
                    if success:
                        processed_count += 1
                    else:
                        failed_count += 1
                    
                    # Clean up downloaded video
                    try:
                        os.unlink(video_path)
                    except:
                        pass
                    
                except Exception as e:
                    logger.error(f"Failed to process job {job_id}: {e}")
                    failed_count += 1
                    continue
        
        # Summary
        logger.info("=" * 50)
        logger.info("HOT_TAKE GENERATION SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total jobs missing hot_take: {len(jobs_missing_hot_take)}")
        logger.info(f"Successfully processed: {processed_count}")
        logger.info(f"Failed to process: {failed_count}")
        logger.info("Hot take generation completed!")
        
    except Exception as e:
        logger.error(f"Hot take generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
