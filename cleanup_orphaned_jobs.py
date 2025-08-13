#!/usr/bin/env python3
"""
Clean up orphaned job IDs in Redis.

This script finds and removes job IDs that exist in the jobs:active set
but don't have corresponding job data in Redis.
"""

import os
import sys
import logging
import argparse
from typing import List

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from job_storage import create_job_storage

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_orphaned_jobs(job_storage) -> List[str]:
    """
    Find job IDs that exist in jobs:active but don't have job data.
    
    Args:
        job_storage: Redis job storage instance
        
    Returns:
        List of orphaned job IDs
    """
    orphaned_jobs = []
    
    try:
        # Get all active job IDs from Redis
        job_ids = job_storage.redis.smembers("jobs:active")
        logger.info(f"Found {len(job_ids)} total job IDs in jobs:active set")
        
        for job_id in job_ids:
            # Check if job data exists
            job_data = job_storage.get_job(job_id)
            if job_data is None:
                orphaned_jobs.append(job_id)
                logger.warning(f"Found orphaned job ID: {job_id}")
        
        logger.info(f"Found {len(orphaned_jobs)} orphaned job IDs")
        return orphaned_jobs
        
    except Exception as e:
        logger.error(f"Error finding orphaned jobs: {str(e)}")
        return []


def cleanup_orphaned_jobs(job_storage, orphaned_jobs: List[str], dry_run: bool = False) -> int:
    """
    Remove orphaned job IDs from the jobs:active set.
    
    Args:
        job_storage: Redis job storage instance
        orphaned_jobs: List of orphaned job IDs to remove
        dry_run: If True, only show what would be removed
        
    Returns:
        Number of jobs actually removed
    """
    removed_count = 0
    
    try:
        for job_id in orphaned_jobs:
            if dry_run:
                logger.info(f"DRY RUN: Would remove orphaned job ID: {job_id}")
            else:
                # Remove from jobs:active set
                result = job_storage.redis.srem("jobs:active", job_id)
                if result:
                    logger.info(f"Removed orphaned job ID: {job_id}")
                    removed_count += 1
                else:
                    logger.warning(f"Failed to remove job ID: {job_id}")
        
        return removed_count
        
    except Exception as e:
        logger.error(f"Error cleaning up orphaned jobs: {str(e)}")
        return 0


def main():
    parser = argparse.ArgumentParser(description="Clean up orphaned job IDs in Redis")
    parser.add_argument("--redis-url", required=True,
                       help="Redis connection URL")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be removed without making changes")
    parser.add_argument("--verbose", action="store_true",
                       help="Show detailed information about each job")
    
    args = parser.parse_args()
    
    try:
        # Initialize job storage
        logger.info("Initializing Redis job storage...")
        job_storage = create_job_storage("redis", args.redis_url)
        
        # Find orphaned jobs
        logger.info("Scanning for orphaned job IDs...")
        orphaned_jobs = find_orphaned_jobs(job_storage)
        
        if not orphaned_jobs:
            logger.info("No orphaned job IDs found")
            return 0
        
        # Show details if verbose
        if args.verbose:
            logger.info("Orphaned job IDs:")
            for job_id in orphaned_jobs:
                logger.info(f"  {job_id}")
        
        # Clean up orphaned jobs
        logger.info(f"Cleaning up {len(orphaned_jobs)} orphaned job IDs...")
        removed_count = cleanup_orphaned_jobs(job_storage, orphaned_jobs, args.dry_run)
        
        # Summary
        logger.info("=" * 50)
        logger.info("CLEANUP SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Orphaned job IDs found: {len(orphaned_jobs)}")
        if not args.dry_run:
            logger.info(f"Job IDs removed: {removed_count}")
        else:
            logger.info("DRY RUN MODE - No job IDs were actually removed")
        
    except Exception as e:
        logger.error(f"Failed to cleanup orphaned jobs: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
