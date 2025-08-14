#!/usr/bin/env python3
"""
Script to update jobs in Firestore from a JSONL file.

This script:
1. Reads jobs from a JSONL file
2. Finds corresponding jobs in Firestore by matching video_url
3. Replaces the entire job document with the data from the file
4. Provides detailed logging and summary statistics
"""

import os
import sys
import json
import logging
import argparse
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
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


def load_jobs_from_jsonl(file_path: str) -> List[Dict]:
    """
    Load jobs from a JSONL file.
    
    Args:
        file_path: Path to the JSONL file
    
    Returns:
        List of job dictionaries
    """
    jobs = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    job = json.loads(line)
                    jobs.append(job)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON on line {line_num}: {e}")
                    continue
        
        logger.info(f"Loaded {len(jobs)} jobs from {file_path}")
        return jobs
        
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return []
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        return []


def extract_filename_from_url(url: str) -> Optional[str]:
    """
    Extract filename from a URL path.
    
    Args:
        url: URL to extract filename from
    
    Returns:
        Filename if found, None otherwise
    """
    try:
        # Split by '/' and get the last part
        parts = url.split('/')
        if parts:
            filename = parts[-1]
            # Remove any query parameters
            filename = filename.split('?')[0]
            return filename
        return None
    except Exception:
        return None


def extract_persona_from_filename(filename: str) -> Optional[str]:
    """
    Extract persona ID from video filename.
    
    Args:
        filename: Video filename (e.g., "job_russ_hanneman_1755073146476.mp4")
    
    Returns:
        Persona ID if found, None otherwise
    """
    try:
        # Pattern: job_<persona_name>_<timestamp>.mp4
        match = re.match(r'job_([a-z_]+)_\d+\.mp4', filename)
        if match:
            return match.group(1)
        return None
    except Exception:
        return None


def extract_timestamp_from_filename(filename: str) -> Optional[int]:
    """
    Extract timestamp from video filename.
    
    Args:
        filename: Video filename (e.g., "job_russ_hanneman_1755073146476.mp4")
    
    Returns:
        Timestamp in seconds if found, None otherwise
    """
    try:
        # Pattern: job_<persona_name>_<timestamp>.mp4
        match = re.match(r'job_[a-z_]+_(\d+)\.mp4', filename)
        if match:
            # Convert milliseconds to seconds
            timestamp_ms = int(match.group(1))
            return timestamp_ms // 1000
        return None
    except Exception:
        return None


def get_persona_name(persona_id: str) -> str:
    """
    Get persona name from persona ID.
    
    Args:
        persona_id: Persona ID (e.g., "russ_hanneman")
    
    Returns:
        Persona name if found, persona_id as fallback
    """
    persona_names = {
        "chad_goldstein": "Chad Goldstein",
        "sarah_guo": "Sarah Guo", 
        "russ_hanneman": "Russ Hanneman"
    }
    return persona_names.get(persona_id, persona_id)


def add_missing_fields(job_data: Dict, video_url: str) -> Dict:
    """
    Add missing fields to job data if they don't exist.
    
    Args:
        job_data: Original job data
        video_url: Video URL to extract information from
    
    Returns:
        Job data with missing fields added
    """
    # Create a copy to avoid modifying the original
    updated_job = job_data.copy()
    
    # Extract filename and parse information
    filename = extract_filename_from_url(video_url)
    if not filename:
        logger.warning(f"Could not extract filename from video_url: {video_url}")
        return updated_job
    
    # Add persona_id if missing
    if "persona_id" not in updated_job:
        persona_id = extract_persona_from_filename(filename)
        if persona_id:
            updated_job["persona_id"] = persona_id
            logger.info(f"Added persona_id: {persona_id}")
        else:
            logger.warning(f"Could not extract persona_id from filename: {filename}")
    
    # Add persona_name if missing
    if "persona_name" not in updated_job and "persona_id" in updated_job:
        persona_name = get_persona_name(updated_job["persona_id"])
        updated_job["persona_name"] = persona_name
        logger.info(f"Added persona_name: {persona_name}")
    
    # Add or fix created_at
    timestamp_seconds = extract_timestamp_from_filename(filename)
    if timestamp_seconds:
        created_at = datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)
        expected_created_at = created_at.isoformat()
        
        if "created_at" not in updated_job:
            updated_job["created_at"] = expected_created_at
            logger.info(f"Added created_at: {expected_created_at}")
        else:
            # Check if existing created_at is in correct format
            existing_created_at = updated_job["created_at"]
            
            # Handle different types of existing timestamps
            if isinstance(existing_created_at, str):
                try:
                    # Try to parse as datetime to check format
                    parsed = datetime.fromisoformat(existing_created_at.replace('Z', '+00:00'))
                    if parsed.tzinfo is None:
                        # Missing timezone, replace it
                        updated_job["created_at"] = expected_created_at
                        logger.info(f"Fixed created_at (missing timezone): {expected_created_at}")
                    elif existing_created_at != expected_created_at:
                        # Different timestamp, replace it
                        updated_job["created_at"] = expected_created_at
                        logger.info(f"Fixed created_at (wrong timestamp): {expected_created_at}")
                    else:
                        # Correct format and timestamp, keep it
                        logger.info(f"created_at already correct: {existing_created_at}")
                except ValueError:
                    # Invalid format, replace it
                    updated_job["created_at"] = expected_created_at
                    logger.info(f"Fixed created_at (invalid format): {expected_created_at}")
            elif hasattr(existing_created_at, 'isoformat'):
                # It's a datetime object (like DatetimeWithNanoseconds from Firestore)
                # Convert to string and check if it matches expected
                existing_str = existing_created_at.isoformat()
                if existing_str != expected_created_at:
                    updated_job["created_at"] = expected_created_at
                    logger.info(f"Fixed created_at (datetime object): {expected_created_at}")
                else:
                    logger.info(f"created_at already correct: {existing_str}")
            else:
                # Unknown type, replace it
                updated_job["created_at"] = expected_created_at
                logger.info(f"Fixed created_at (unknown type): {expected_created_at}")
    else:
        logger.warning(f"Could not extract timestamp from filename: {filename}")
    
    # Add step if missing
    if "step" not in updated_job:
        updated_job["step"] = "video_generation"
        logger.info("Added step: video_generation")
    
    # Add or fix updated_at (always update to current time)
    current_time = datetime.now(timezone.utc)
    expected_updated_at = current_time.isoformat()
    
    if "updated_at" not in updated_job:
        updated_job["updated_at"] = expected_updated_at
        logger.info(f"Added updated_at: {expected_updated_at}")
    else:
                    # Check if existing updated_at is in correct format
            existing_updated_at = updated_job["updated_at"]
            
            # Handle different types of existing timestamps
            if isinstance(existing_updated_at, str):
                try:
                    # Try to parse as datetime to check format
                    parsed = datetime.fromisoformat(existing_updated_at.replace('Z', '+00:00'))
                    if parsed.tzinfo is None:
                        # Missing timezone, replace it
                        updated_job["updated_at"] = expected_updated_at
                        logger.info(f"Fixed updated_at (missing timezone): {expected_updated_at}")
                    else:
                        # Valid format, but always update to current time
                        updated_job["updated_at"] = expected_updated_at
                        logger.info(f"Updated updated_at: {expected_updated_at}")
                except ValueError:
                    # Invalid format, replace it
                    updated_job["updated_at"] = expected_updated_at
                    logger.info(f"Fixed updated_at (invalid format): {expected_updated_at}")
            elif hasattr(existing_updated_at, 'isoformat'):
                # It's a datetime object (like DatetimeWithNanoseconds from Firestore)
                # Always update to current time
                updated_job["updated_at"] = expected_updated_at
                logger.info(f"Updated updated_at (datetime object): {expected_updated_at}")
            else:
                # Unknown type, replace it
                updated_job["updated_at"] = expected_updated_at
                logger.info(f"Fixed updated_at (unknown type): {expected_updated_at}")
    
    return updated_job


def find_job_by_video_filename(job_storage, video_url: str) -> Optional[Dict]:
    """
    Find a job in Firestore by matching video filename extracted from URL.
    
    Args:
        job_storage: Firestore job storage instance
        video_url: Video URL to extract filename from
    
    Returns:
        Job data if found, None otherwise
    """
    try:
        # Extract filename from the input video_url
        target_filename = extract_filename_from_url(video_url)
        if not target_filename:
            logger.error(f"Could not extract filename from video_url: {video_url}")
            return None
        
        logger.info(f"Looking for jobs with filename: {target_filename}")
        
        # Get all jobs and search for matching filename
        all_jobs = job_storage.list_jobs(limit=10000)  # Large limit to search all jobs
        
        for job in all_jobs:
            job_results = job.get("results", {})
            job_video_url = job_results.get("video_url") or job_results.get("output_video")
            if job_video_url:
                job_filename = extract_filename_from_url(job_video_url)
                if job_filename == target_filename:
                    logger.info(f"Found matching job {job.get('id')} with filename: {job_filename}")
                    return job
        
        # If not found in list_jobs, try direct collection query (for jobs with missing created_at)
        logger.info(f"Job not found in list_jobs, trying direct collection query...")
        if hasattr(job_storage, 'collection'):
            for doc in job_storage.collection.stream():
                job = doc.to_dict()
                job_results = job.get("results", {})
                job_video_url = job_results.get("video_url") or job_results.get("output_video")
                if job_video_url:
                    job_filename = extract_filename_from_url(job_video_url)
                    if job_filename == target_filename:
                        logger.info(f"Found matching job {job.get('id')} with filename: {job_filename} (via direct query)")
                        return job
        
        logger.warning(f"No job found with filename: {target_filename}")
        return None
        
    except Exception as e:
        logger.error(f"Failed to search for job with video_url {video_url}: {e}")
        return None


def update_job_in_firestore(job_storage, job_id: str, new_job_data: Dict) -> bool:
    """
    Update a job in Firestore with new data.
    
    Args:
        job_storage: Firestore job storage instance
        job_id: ID of the job to update
        new_job_data: New job data to replace the existing job
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # First, check if the job exists
        existing_job = job_storage.get_job(job_id)
        if not existing_job:
            logger.error(f"Job {job_id} not found in Firestore")
            return False
        
        logger.info(f"Updating job {job_id}")
        logger.info(f"Existing job keys: {list(existing_job.keys())}")
        logger.info(f"New job data keys: {list(new_job_data.keys())}")
        
        # Ensure the job_id is set in the new data
        new_job_data["id"] = job_id
        
        # Replace the entire job document using set() with merge=False
        doc_ref = job_storage.collection.document(job_id)
        doc_ref.set(new_job_data, merge=False)
        
        # Verify the update by reading back the document
        updated_job = job_storage.get_job(job_id)
        if updated_job:
            logger.info(f"Successfully updated job {job_id}")
            logger.info(f"Updated job keys: {list(updated_job.keys())}")
            return True
        else:
            logger.error(f"Failed to verify update for job {job_id}")
            return False
        
    except Exception as e:
        logger.error(f"Failed to update job {job_id}: {e}")
        return False


def process_job_update(job_storage, job_data: Dict) -> Tuple[bool, str]:
    """
    Process a single job update.
    
    Args:
        job_storage: Firestore job storage instance
        job_data: Job data from JSONL file
    
    Returns:
        Tuple of (success, message)
    """
    try:
        # Extract video_url from the job data, fallback to output_video
        results = job_data.get("results", {})
        video_url = results.get("video_url") or results.get("output_video")
        if not video_url:
            return False, "No video_url or output_video found in job data"
        
        # Add missing fields to the job data
        enhanced_job_data = add_missing_fields(job_data, video_url)
        
        # Find the corresponding job in Firestore by filename
        existing_job = find_job_by_video_filename(job_storage, video_url)
        if not existing_job:
            return False, f"No job found with video filename from URL: {video_url}"
        
        job_id = existing_job.get("id")
        if not job_id:
            return False, f"Found job but no ID: {video_url}"
        
        # Update the job with enhanced data
        success = update_job_in_firestore(job_storage, job_id, enhanced_job_data)
        if success:
            filename = extract_filename_from_url(video_url)
            return True, f"Updated job {job_id} with video filename: {filename}"
        else:
            return False, f"Failed to update job {job_id}"
        
    except Exception as e:
        return False, f"Error processing job: {e}"


def main():
    """Main function to process job updates from JSONL file."""
    
    parser = argparse.ArgumentParser(description="Update jobs in Firestore from JSONL file")
    parser.add_argument("jsonl_file", help="Path to JSONL file containing jobs to update")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be updated without making changes")
    parser.add_argument("--project-id", help="Firestore project ID (defaults to FIRESTORE_PROJECT_ID env var)")
    parser.add_argument("--collection", default="jobs", help="Firestore collection name (default: jobs)")
    
    args = parser.parse_args()
    
    # Check if JSONL file exists
    if not os.path.exists(args.jsonl_file):
        logger.error(f"JSONL file not found: {args.jsonl_file}")
        sys.exit(1)
    
    # Initialize job storage based on environment
    storage_type = os.getenv("JOB_STORAGE", "firestore")
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    project_id = args.project_id or os.getenv("FIRESTORE_PROJECT_ID")
    firestore_collection = os.getenv("FIRESTORE_COLLECTION", "jobs")
    
    if storage_type == "firestore" and not project_id:
        logger.error("FIRESTORE_PROJECT_ID environment variable not set")
        logger.info("Set it with: export FIRESTORE_PROJECT_ID='your-project-id'")
        sys.exit(1)
    
    try:
        # Initialize storage
        logger.info(f"Using storage type: {storage_type}")
        if storage_type == "firestore":
            logger.info(f"Initializing Firestore storage with project: {project_id}")
            logger.info(f"Firestore collection: {firestore_collection}")
        elif storage_type == "redis":
            logger.info(f"Initializing Redis storage with URL: {redis_url}")
        
        job_storage = create_job_storage(
            storage_type, 
            redis_url, 
            project_id,
            firestore_collection
        )
        
        # Load jobs from JSONL file
        jobs_to_update = load_jobs_from_jsonl(args.jsonl_file)
        if not jobs_to_update:
            logger.error("No jobs found in JSONL file")
            sys.exit(1)
        
        # Process each job
        successful_updates = 0
        failed_updates = 0
        skipped_updates = 0
        
        logger.info(f"Processing {len(jobs_to_update)} jobs...")
        if args.dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
        
        for i, job_data in enumerate(jobs_to_update, 1):
            logger.info(f"Processing job {i}/{len(jobs_to_update)}")
            
            if args.dry_run:
                # In dry-run mode, check if we can find the job and show what would be added
                results = job_data.get("results", {})
                video_url = results.get("video_url") or results.get("output_video")
                if not video_url:
                    logger.warning(f"Job {i}: No video_url or output_video found")
                    skipped_updates += 1
                    continue
                
                existing_job = find_job_by_video_filename(job_storage, video_url)
                if existing_job:
                    filename = extract_filename_from_url(video_url)
                    logger.info(f"Job {i}: Would update job {existing_job.get('id')} with video filename: {filename}")
                    
                    # Show what fields would be added
                    enhanced_job_data = add_missing_fields(job_data, video_url)
                    logger.info(f"Job {i}: Current job keys: {list(existing_job.keys())}")
                    logger.info(f"Job {i}: Enhanced job keys: {list(enhanced_job_data.keys())}")
                    
                    # Show specific field additions
                    added_fields = []
                    if "persona_id" not in existing_job and "persona_id" in enhanced_job_data:
                        added_fields.append(f"persona_id: {enhanced_job_data['persona_id']}")
                    if "persona_name" not in existing_job and "persona_name" in enhanced_job_data:
                        added_fields.append(f"persona_name: {enhanced_job_data['persona_name']}")
                    if "created_at" not in existing_job and "created_at" in enhanced_job_data:
                        added_fields.append(f"created_at: {enhanced_job_data['created_at']}")
                    if "step" not in existing_job and "step" in enhanced_job_data:
                        added_fields.append(f"step: {enhanced_job_data['step']}")
                    if "updated_at" in enhanced_job_data:
                        added_fields.append(f"updated_at: {enhanced_job_data['updated_at']}")
                    
                    if added_fields:
                        logger.info(f"Job {i}: Would add fields: {', '.join(added_fields)}")
                    else:
                        logger.info(f"Job {i}: No new fields to add")
                    
                    successful_updates += 1
                else:
                    logger.warning(f"Job {i}: No matching job found for video filename from URL: {video_url}")
                    failed_updates += 1
            else:
                # Actually update the job
                success, message = process_job_update(job_storage, job_data)
                if success:
                    successful_updates += 1
                    logger.info(f"Job {i}: {message}")
                else:
                    failed_updates += 1
                    logger.error(f"Job {i}: {message}")
        
        # Summary
        logger.info("=" * 60)
        logger.info("JOB UPDATE SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total jobs in JSONL file: {len(jobs_to_update)}")
        logger.info(f"Successful updates: {successful_updates}")
        logger.info(f"Failed updates: {failed_updates}")
        logger.info(f"Skipped updates: {skipped_updates}")
        
        if args.dry_run:
            logger.info("DRY RUN COMPLETED - No changes were made")
        else:
            logger.info("Job updates completed!")
        
    except Exception as e:
        logger.error(f"Job update process failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
