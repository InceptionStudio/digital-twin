#!/usr/bin/env python3
"""
Process video transcripts for Redis jobs.

This script finds all jobs in Redis that have a video_url but no results.hot_take,
downloads the video, extracts audio, transcribes it using Whisper, and sets the
transcript as the hot_take result.
"""

import os
import sys
import json
import logging
import argparse
import tempfile
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
from datetime import datetime, timezone

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from job_storage import create_job_storage
from audio_processor import AudioProcessor
from config import Config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def download_video(video_url: str, temp_dir: Path) -> str:
    """
    Download video from URL to temporary file.
    
    Args:
        video_url: URL of the video to download
        temp_dir: Directory to save the video in
        
    Returns:
        Path to the downloaded video file
        
    Raises:
        Exception: If download fails
    """
    try:
        logger.info(f"Downloading video from: {video_url}")
        
        # Create a temporary file with appropriate extension
        parsed_url = urlparse(video_url)
        filename = os.path.basename(parsed_url.path)
        if not filename or '.' not in filename:
            filename = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        
        video_path = temp_dir / filename
        
        # Download the video
        response = requests.get(video_url, stream=True, timeout=300)
        response.raise_for_status()
        
        with open(video_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Downloaded video to: {video_path}")
        return str(video_path)
        
    except Exception as e:
        raise Exception(f"Failed to download video from {video_url}: {str(e)}")


def process_job_video(job_storage, job_id: str, job_data: Dict[str, Any], 
                     audio_processor: AudioProcessor, temp_dir: Path) -> bool:
    """
    Process a single job's video to extract transcript.
    
    Args:
        job_storage: Redis job storage instance
        job_id: Job ID
        job_data: Job data from Redis
        audio_processor: AudioProcessor instance for transcription
        temp_dir: Temporary directory for downloads
        
    Returns:
        True if processing was successful, False otherwise
    """
    try:
        # Get video URL from various possible locations
        video_url = None
        results = job_data.get("results", {})
        
        if results.get("video_url"):
            video_url = results["video_url"]
        elif results.get("video_s3_url"):
            video_url = results["video_s3_url"]
        elif results.get("output_video") and results["output_video"].startswith("http"):
            video_url = results["output_video"]
        
        if not video_url:
            logger.warning(f"Job {job_id} has no video URL found")
            return False
        
        # Check if hot_take already exists
        if results.get("hot_take"):
            logger.info(f"Job {job_id} already has hot_take, skipping")
            return False
        
        logger.info(f"Processing video for job {job_id}")
        
        # Download the video
        video_path = download_video(video_url, temp_dir)
        
        try:
            # Extract audio and transcribe
            logger.info(f"Transcribing video for job {job_id}")
            transcript = audio_processor.process_input(video_path)
            
            # Update the job with the transcript
            # Create a copy of results without the id field to avoid overwriting job ID
            results_copy = {k: v for k, v in results.items() if k != 'id'}
            update_data = {
                "results": {
                    **results_copy,
                    "hot_take": transcript,
                    "transcript_source": "whisper",
                    "transcript_timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
            
            success = job_storage.update_job(job_id, update_data)
            if success:
                logger.info(f"Successfully updated job {job_id} with transcript ({len(transcript)} characters)")
                return True
            else:
                logger.error(f"Failed to update job {job_id} with transcript")
                return False
                
        finally:
            # Clean up downloaded video
            try:
                os.unlink(video_path)
                logger.debug(f"Cleaned up video file: {video_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up video file {video_path}: {e}")
        
    except Exception as e:
        logger.error(f"Error processing video for job {job_id}: {str(e)}")
        return False


def find_jobs_needing_transcripts(job_storage) -> List[tuple]:
    """
    Find all jobs that have video_url but no results.hot_take.
    
    Args:
        job_storage: Redis job storage instance
        
    Returns:
        List of (job_id, job_data) tuples for jobs needing transcripts
    """
    jobs_needing_transcripts = []
    
    try:
        # Get all active job IDs from Redis
        job_ids = job_storage.redis.smembers("jobs:active")
        logger.info(f"Found {len(job_ids)} total jobs in Redis")
        
        for job_id in job_ids:
            job_data = job_storage.get_job(job_id)
            if not job_data:
                logger.warning(f"Could not retrieve job data for {job_id}")
                continue
            
            # Check if job has video URL
            results = job_data.get("results", {})
            has_video_url = (
                results.get("video_url") or 
                results.get("video_s3_url") or
                (results.get("output_video") and results["output_video"].startswith("http"))
            )
            
            # Check if job doesn't have hot_take
            has_hot_take = bool(results.get("hot_take"))
            
            if has_video_url and not has_hot_take:
                jobs_needing_transcripts.append((job_id, job_data))
                logger.info(f"Job {job_id} needs transcript processing")
        
        logger.info(f"Found {len(jobs_needing_transcripts)} jobs needing transcript processing")
        return jobs_needing_transcripts
        
    except Exception as e:
        logger.error(f"Error finding jobs needing transcripts: {str(e)}")
        return []


def main():
    parser = argparse.ArgumentParser(description="Process video transcripts for Redis jobs")
    parser.add_argument("--redis-url", default="redis://redis:6379",
                       help="Redis connection URL")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be processed without making changes")
    parser.add_argument("--job-id", type=str,
                       help="Process only a specific job ID")
    parser.add_argument("--max-jobs", type=int, default=100,
                       help="Maximum number of jobs to process")
    
    args = parser.parse_args()
    
    try:
        # Initialize job storage
        logger.info("Initializing Redis job storage...")
        job_storage = create_job_storage("redis", args.redis_url)
        
        # Initialize audio processor
        logger.info("Initializing audio processor...")
        audio_processor = AudioProcessor()
        
        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp(prefix="video_transcripts_"))
        logger.info(f"Using temporary directory: {temp_dir}")
        
        try:
            if args.job_id:
                # Process specific job
                logger.info(f"Processing specific job: {args.job_id}")
                job_data = job_storage.get_job(args.job_id)
                if not job_data:
                    logger.error(f"Job {args.job_id} not found")
                    return 1
                
                jobs_to_process = [(args.job_id, job_data)]
            else:
                # Find all jobs needing transcripts
                jobs_to_process = find_jobs_needing_transcripts(job_storage)
                jobs_to_process = jobs_to_process[:args.max_jobs]
            
            if not jobs_to_process:
                logger.info("No jobs found needing transcript processing")
                return 0
            
            # Process jobs
            processed_count = 0
            failed_count = 0
            
            for job_id, job_data in jobs_to_process:
                if args.dry_run:
                    logger.info(f"DRY RUN: Would process job {job_id}")
                    continue
                
                success = process_job_video(job_storage, job_id, job_data, audio_processor, temp_dir)
                if success:
                    processed_count += 1
                else:
                    failed_count += 1
            
            # Summary
            logger.info("=" * 50)
            logger.info("TRANSCRIPT PROCESSING SUMMARY")
            logger.info("=" * 50)
            logger.info(f"Jobs found needing transcripts: {len(jobs_to_process)}")
            if not args.dry_run:
                logger.info(f"Jobs successfully processed: {processed_count}")
                logger.info(f"Jobs failed: {failed_count}")
            else:
                logger.info("DRY RUN MODE - No jobs were actually processed")
            
        finally:
            # Clean up temporary directory
            try:
                import shutil
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary directory {temp_dir}: {e}")
        
    except Exception as e:
        logger.error(f"Failed to process video transcripts: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
