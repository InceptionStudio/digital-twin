#!/usr/bin/env python3
"""
Script to migrate jobs from Redis to Firestore.

This script:
1. Connects to both Redis and Firestore
2. Reads all jobs from Redis
3. Creates corresponding jobs in Firestore
4. Optionally deletes jobs from Redis after successful migration
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timezone
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


def migrate_jobs(redis_storage, firestore_storage, dry_run: bool = False, delete_after: bool = False) -> Dict[str, int]:
    """
    Migrate jobs from Redis to Firestore.
    
    Args:
        redis_storage: Redis job storage instance
        firestore_storage: Firestore job storage instance
        dry_run: If True, don't actually migrate, just show what would be done
        delete_after: If True, delete jobs from Redis after successful migration
    
    Returns:
        Dictionary with migration statistics
    """
    stats = {
        "total_jobs": 0,
        "migrated": 0,
        "skipped": 0,
        "failed": 0,
        "deleted": 0
    }
    
    try:
        # Get all active job IDs from Redis
        if not hasattr(redis_storage, 'redis') or not redis_storage.redis:
            logger.error("Redis storage is not properly configured")
            return stats
        
        job_ids = redis_storage.redis.smembers("jobs:active")
        stats["total_jobs"] = len(job_ids)
        
        logger.info(f"Found {stats['total_jobs']} jobs in Redis to migrate")
        
        for job_id in job_ids:
            try:
                # Get job data from Redis
                job_data = redis_storage.get_job(job_id)
                if not job_data:
                    logger.warning(f"Job {job_id} not found in Redis, skipping")
                    stats["skipped"] += 1
                    continue
                
                # Check if job already exists in Firestore
                existing_job = firestore_storage.get_job(job_id)
                if existing_job:
                    logger.info(f"Job {job_id} already exists in Firestore, skipping")
                    stats["skipped"] += 1
                    continue
                
                if dry_run:
                    logger.info(f"Would migrate job {job_id} to Firestore")
                    stats["migrated"] += 1
                    continue
                
                # Create job in Firestore
                # Note: We need to handle the ID manually since create_job generates a new one
                job_data["id"] = job_id  # Ensure the ID is preserved
                
                # Use Firestore's document reference to set with specific ID
                doc_ref = firestore_storage.collection.document(job_id)
                doc_ref.set(job_data)
                
                logger.info(f"Successfully migrated job {job_id} to Firestore")
                stats["migrated"] += 1
                
                # Delete from Redis if requested
                if delete_after:
                    redis_storage.delete_job(job_id)
                    logger.info(f"Deleted job {job_id} from Redis")
                    stats["deleted"] += 1
                    
            except Exception as e:
                logger.error(f"Failed to migrate job {job_id}: {e}")
                stats["failed"] += 1
        
        return stats
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return stats


def main():
    parser = argparse.ArgumentParser(description='Migrate jobs from Redis to Firestore')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be migrated without actually doing it')
    parser.add_argument('--delete-after', action='store_true',
                       help='Delete jobs from Redis after successful migration')
    parser.add_argument('--redis-url', default='redis://redis:6379',
                       help='Redis URL')
    parser.add_argument('--firestore-project-id', required=True,
                       help='Firestore project ID')
    parser.add_argument('--firestore-collection', default='jobs',
                       help='Firestore collection name')
    
    args = parser.parse_args()
    
    try:
        # Initialize Redis storage
        logger.info("Initializing Redis storage...")
        redis_storage = create_job_storage("redis", args.redis_url)
        
        # Initialize Firestore storage
        logger.info("Initializing Firestore storage...")
        firestore_storage = create_job_storage(
            "firestore", 
            firestore_project_id=args.firestore_project_id,
            firestore_collection=args.firestore_collection
        )
        
        # Perform migration
        logger.info("Starting migration...")
        stats = migrate_jobs(
            redis_storage, 
            firestore_storage, 
            dry_run=args.dry_run,
            delete_after=args.delete_after
        )
        
        # Print summary
        logger.info("=" * 50)
        logger.info("MIGRATION SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total jobs in Redis: {stats['total_jobs']}")
        logger.info(f"Jobs {'would be ' if args.dry_run else ''}migrated: {stats['migrated']}")
        logger.info(f"Jobs skipped: {stats['skipped']}")
        logger.info(f"Jobs failed: {stats['failed']}")
        if args.delete_after:
            logger.info(f"Jobs deleted from Redis: {stats['deleted']}")
        
        if args.dry_run:
            logger.info("DRY RUN MODE - No jobs were actually migrated")
        else:
            logger.info("Migration completed successfully!")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
