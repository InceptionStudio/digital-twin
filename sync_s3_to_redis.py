#!/usr/bin/env python3
"""
Script to sync S3 videos to production Redis jobs.

This script:
1. Lists all videos in the S3 bucket
2. Parses filenames to extract timestamps and persona information
3. Checks if corresponding jobs exist in production Redis
4. Creates missing jobs in production Redis
"""

import os
import sys
import json
import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
import argparse

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from s3_storage import S3Storage
from job_storage import create_job_storage
from persona_manager import PersonaManager
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_video_filename(filename: str) -> Tuple[Optional[str], Optional[datetime], Optional[str]]:
    """
    Parse video filename to extract job_id, timestamp, and persona information.
    
    Expected filename patterns:
    - videos/job_{job_id}.mp4
    - videos/video_job_{job_id}.mp4
    - videos/pitch_video_{job_id}_{timestamp}.mp4
    - videos/{persona_name}_{job_id}_{timestamp}.mp4
    - videos/chad_text_response_{job_id}.mp4
    - videos/chad_roast_{job_id}.mp4
    - videos/chad_response_{job_id}.mp4
    
    Returns:
        Tuple of (job_id, timestamp, persona_id)
    """
    # Remove .mp4 extension and videos/ prefix
    base_name = filename.replace('.mp4', '').replace('videos/', '')
    
    # Pattern 1: job_{job_id}
    match = re.match(r'^job_([a-f0-9-]+)$', base_name)
    if match:
        return match.group(1), None, None
    
    # Pattern 2: video_job_{job_id}
    match = re.match(r'^video_job_([a-f0-9-]+)$', base_name)
    if match:
        return match.group(1), None, None
    
    # Pattern 3: pitch_video_{job_id}_{timestamp}
    match = re.match(r'^pitch_video_([a-f0-9-]+)_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})$', base_name)
    if match:
        job_id = match.group(1)
        timestamp_str = match.group(2).replace('_', ' ').replace('-', ':')
        try:
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            return job_id, timestamp, None
        except ValueError:
            logger.warning(f"Could not parse timestamp in filename: {filename}")
            return job_id, None, None
    
    # Pattern 4: chad_text_response_{job_id}
    match = re.match(r'^chad_text_response_([a-f0-9-]+)$', base_name)
    if match:
        return match.group(1), None, "chad_goldstein"
    
    # Pattern 5: chad_roast_{job_id}
    match = re.match(r'^chad_roast_([a-f0-9-]+)$', base_name)
    if match:
        return match.group(1), None, "chad_goldstein"
    
    # Pattern 6: chad_response_{job_id}
    match = re.match(r'^chad_response_([a-f0-9-]+)$', base_name)
    if match:
        return match.group(1), None, "chad_goldstein"
    
    # Pattern 7: job_{persona_name}_{timestamp}
    # First, get all persona names to match against
    persona_manager = PersonaManager()
    persona_names = {persona.name.lower().replace(' ', '_'): persona_id 
                    for persona_id, persona in persona_manager.personas.items()}
    
    for persona_name, persona_id in persona_names.items():
        pattern = rf'^job_{persona_name}_(\d+)$'
        match = re.match(pattern, base_name)
        if match:
            timestamp_ms = int(match.group(1))
            # Convert milliseconds to datetime with UTC timezone
            timestamp = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
            # Generate a proper GUID instead of using timestamp as job_id
            job_id = str(uuid.uuid4())
            return job_id, timestamp, persona_id
    
    # Pattern 8: {persona_name}_{job_id}_{timestamp}
    # First, get all persona names to match against
    persona_manager = PersonaManager()
    persona_names = {persona.name.lower().replace(' ', '_'): persona_id 
                    for persona_id, persona in persona_manager.personas.items()}
    
    for persona_name, persona_id in persona_names.items():
        pattern = rf'^{persona_name}_([a-f0-9-]+)_(\d{{4}}-\d{{2}}-\d{{2}}_\d{{2}}-\d{{2}}-\d{{2}})$'
        match = re.match(pattern, base_name)
        if match:
            job_id = match.group(1)
            timestamp_str = match.group(2).replace('_', ' ').replace('-', ':')
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                # Make timezone-aware (assuming UTC)
                timestamp = timestamp.replace(tzinfo=timezone.utc)
                return job_id, timestamp, persona_id
            except ValueError:
                logger.warning(f"Could not parse timestamp in filename: {filename}")
                return job_id, None, persona_id
    
    # Pattern 9: Try to extract any UUID-like job_id
    uuid_pattern = r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})'
    match = re.search(uuid_pattern, base_name)
    if match:
        job_id = match.group(1)
        logger.info(f"Extracted job_id from filename but couldn't parse timestamp/persona: {filename}")
        return job_id, None, None
    
    logger.warning(f"Could not parse filename: {filename}")
    return None, None, None


def create_job_from_s3_video(job_storage, s3_key: str, file_info: Dict, 
                           job_id: str, timestamp: Optional[datetime], 
                           persona_id: Optional[str]) -> bool:
    """
    Create a job in Redis based on S3 video information.
    
    Args:
        job_storage: Redis job storage instance
        s3_key: S3 key of the video file
        file_info: File information from S3
        job_id: Extracted job ID
        timestamp: Extracted timestamp
        persona_id: Extracted persona ID
    
    Returns:
        True if job was created successfully, False otherwise
    """
    try:
        # Determine the created_at timestamp
        # Priority: 1. Parsed timestamp from filename, 2. S3 file timestamp, 3. Current time
        created_at = None
        if timestamp:
            created_at = timestamp
        elif file_info.get('last_modified'):
            # S3 returns last_modified as a datetime object
            created_at = file_info['last_modified']
        else:
            # Fallback to current time with UTC timezone
            created_at = datetime.now(timezone.utc)
        
        # Create job data
        job_data = {
            "status": "completed",
            "progress": "Video processing completed",
            "step": "video_generation",
            "results": {
                "video_url": f"https://{Config.S3_BUCKET_NAME}.s3.amazonaws.com/{s3_key}",
                "output_video": f"https://{Config.S3_BUCKET_NAME}.s3.amazonaws.com/{s3_key}",
                "file_size": file_info.get('size', 0),
                "content_type": file_info.get('content_type', 'video/mp4'),
                "s3_key": s3_key
            },
            "created_at": created_at.isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Add persona information - default to chad_goldstein if none specified
        if persona_id is None:
            persona_id = "chad_goldstein"
        
        job_data["persona_id"] = persona_id
        persona_manager = PersonaManager()
        persona = persona_manager.get_persona(persona_id)
        if persona:
            job_data["persona_name"] = persona.name
        
        # Create the job with the correct ID directly in Redis to avoid overwriting our data
        job_data["id"] = job_id
        job_storage.redis.setex(
            f"job:{job_id}",
            timedelta(hours=24),
            json.dumps(job_data)
        )
        job_storage.redis.sadd("jobs:active", job_id)
        
        logger.info(f"Created job {job_id} for S3 video {s3_key}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create job for {s3_key}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Sync S3 videos to production Redis jobs')
    parser.add_argument('--dry-run', action='store_true', 
                       help='List videos and jobs without creating new ones')
    parser.add_argument('--redis-url', default='redis://redis:6379',
                       help='Redis URL for production Redis')
    parser.add_argument('--s3-prefix', default='videos/',
                       help='S3 prefix to list videos from')
    parser.add_argument('--max-keys', type=int, default=1000,
                       help='Maximum number of S3 keys to process')
    
    args = parser.parse_args()
    
    try:
        # Initialize S3 storage
        logger.info("Initializing S3 storage...")
        s3_storage = S3Storage()
        
        # Initialize Redis job storage
        logger.info("Initializing Redis job storage...")
        job_storage = create_job_storage("redis", args.redis_url)
        
        # List videos in S3
        logger.info(f"Listing videos in S3 with prefix '{args.s3_prefix}'...")
        video_keys = s3_storage.list_files(prefix=args.s3_prefix, max_keys=args.max_keys)
        
        logger.info(f"Found {len(video_keys)} video files in S3")
        
        # Process each video
        created_count = 0
        existing_count = 0
        failed_count = 0
        
        for s3_key in video_keys:
            try:
                # Parse filename
                job_id, timestamp, persona_id = parse_video_filename(s3_key)
                
                if not job_id:
                    logger.warning(f"Skipping {s3_key} - could not extract job_id")
                    failed_count += 1
                    continue
                
                # Check if a job already exists that references this video file
                existing_job = None
                
                # Get all active job IDs from Redis
                job_ids = job_storage.redis.smembers("jobs:active")
                
                for existing_job_id in job_ids:
                    existing_job_data = job_storage.get_job(existing_job_id)
                    if not existing_job_data:
                        continue
                    
                    # Check various video path fields in the job data
                    video_paths = []
                    
                    # Check results.video_url
                    if existing_job_data.get("results", {}).get("video_url"):
                        video_paths.append(existing_job_data["results"]["video_url"])
                    
                    # Check results.output_video
                    if existing_job_data.get("results", {}).get("output_video"):
                        video_paths.append(existing_job_data["results"]["output_video"])
                    
                    # Check results.s3_key
                    if existing_job_data.get("results", {}).get("s3_key"):
                        video_paths.append(existing_job_data["results"]["s3_key"])
                    
                    # Check if any of these paths match our current S3 key
                    for video_path in video_paths:
                        if s3_key in video_path or video_path.endswith(s3_key.split('/')[-1]):
                            existing_job = existing_job_data
                            break
                    
                    if existing_job:
                        break
                
                if existing_job:
                    logger.info(f"Job already exists in Redis for video {s3_key} (job_id: {existing_job.get('id', 'unknown')})")
                    existing_count += 1
                    continue
                
                # Get file info from S3
                file_info = s3_storage.get_file_info(s3_key)
                
                if args.dry_run:
                    logger.info(f"Would create job {job_id} for {s3_key} (persona: {persona_id}, timestamp: {timestamp})")
                    created_count += 1
                else:
                    # Create the job
                    success = create_job_from_s3_video(
                        job_storage, s3_key, file_info, job_id, timestamp, persona_id
                    )
                    if success:
                        created_count += 1
                    else:
                        failed_count += 1
                        
            except Exception as e:
                logger.error(f"Error processing {s3_key}: {e}")
                failed_count += 1
        
        # Summary
        logger.info("=" * 50)
        logger.info("SYNC SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total videos found in S3: {len(video_keys)}")
        logger.info(f"Jobs already exist in Redis: {existing_count}")
        logger.info(f"Jobs {'would be ' if args.dry_run else ''}created: {created_count}")
        logger.info(f"Failed to process: {failed_count}")
        
        if args.dry_run:
            logger.info("DRY RUN MODE - No jobs were actually created")
        else:
            logger.info("Sync completed successfully!")
            
    except Exception as e:
        logger.error(f"Failed to sync S3 to Redis: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
