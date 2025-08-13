#!/usr/bin/env python3
"""
Check job data integrity in Redis.

This script checks for various data integrity issues:
1. Orphaned job IDs (in jobs:active but no job data)
2. Missing required fields
3. Invalid data types
4. Inconsistent job IDs
"""

import os
import sys
import logging
import argparse
from typing import List, Dict, Any, Tuple

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from job_storage import create_job_storage

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_job_integrity(job_storage) -> Dict[str, List]:
    """
    Check integrity of all jobs in Redis.
    
    Args:
        job_storage: Redis job storage instance
        
    Returns:
        Dictionary with different types of issues found
    """
    issues = {
        'orphaned_jobs': [],
        'missing_required_fields': [],
        'inconsistent_job_ids': [],
        'invalid_data_types': []
    }
    
    try:
        # Get all active job IDs from Redis
        job_ids = job_storage.redis.smembers("jobs:active")
        logger.info(f"Found {len(job_ids)} total job IDs in jobs:active set")
        
        for job_id in job_ids:
            # Check if job data exists
            job_data = job_storage.get_job(job_id)
            if job_data is None:
                issues['orphaned_jobs'].append(job_id)
                continue
            
            # Check required fields
            required_fields = ['id', 'status', 'created_at']
            missing_fields = [f for f in required_fields if f not in job_data]
            if missing_fields:
                issues['missing_required_fields'].append((job_id, missing_fields))
            
            # Check for inconsistent job IDs
            if 'id' in job_data and job_data['id'] != job_id:
                issues['inconsistent_job_ids'].append((job_id, job_data['id']))
            
            # Check data types
            if 'created_at' in job_data and not isinstance(job_data['created_at'], str):
                issues['invalid_data_types'].append((job_id, 'created_at', type(job_data['created_at'])))
            
            if 'status' in job_data and not isinstance(job_data['status'], str):
                issues['invalid_data_types'].append((job_id, 'status', type(job_data['status'])))
        
        return issues
        
    except Exception as e:
        logger.error(f"Error checking job integrity: {str(e)}")
        return issues


def print_integrity_report(issues: Dict[str, List]):
    """
    Print a detailed integrity report.
    
    Args:
        issues: Dictionary of issues found
    """
    logger.info("=" * 60)
    logger.info("JOB INTEGRITY REPORT")
    logger.info("=" * 60)
    
    total_issues = sum(len(issue_list) for issue_list in issues.values())
    
    if total_issues == 0:
        logger.info("✅ No integrity issues found!")
        return
    
    logger.info(f"Found {total_issues} total issues:")
    
    # Orphaned jobs
    if issues['orphaned_jobs']:
        logger.info(f"\n❌ Orphaned job IDs ({len(issues['orphaned_jobs'])}):")
        for job_id in issues['orphaned_jobs']:
            logger.info(f"  - {job_id}")
    
    # Missing required fields
    if issues['missing_required_fields']:
        logger.info(f"\n❌ Jobs with missing required fields ({len(issues['missing_required_fields'])}):")
        for job_id, missing_fields in issues['missing_required_fields']:
            logger.info(f"  - {job_id}: missing {missing_fields}")
    
    # Inconsistent job IDs
    if issues['inconsistent_job_ids']:
        logger.info(f"\n❌ Jobs with inconsistent IDs ({len(issues['inconsistent_job_ids'])}):")
        for job_id, data_id in issues['inconsistent_job_ids']:
            logger.info(f"  - Redis key: {job_id}, data id: {data_id}")
    
    # Invalid data types
    if issues['invalid_data_types']:
        logger.info(f"\n❌ Jobs with invalid data types ({len(issues['invalid_data_types'])}):")
        for job_id, field, data_type in issues['invalid_data_types']:
            logger.info(f"  - {job_id}: {field} is {data_type}, expected str")


def main():
    parser = argparse.ArgumentParser(description="Check job data integrity in Redis")
    parser.add_argument("--redis-url", required=True,
                       help="Redis connection URL")
    parser.add_argument("--fix-orphaned", action="store_true",
                       help="Automatically fix orphaned job IDs")
    
    args = parser.parse_args()
    
    try:
        # Initialize job storage
        logger.info("Initializing Redis job storage...")
        job_storage = create_job_storage("redis", args.redis_url)
        
        # Check integrity
        logger.info("Checking job data integrity...")
        issues = check_job_integrity(job_storage)
        
        # Print report
        print_integrity_report(issues)
        
        # Fix orphaned jobs if requested
        if args.fix_orphaned and issues['orphaned_jobs']:
            logger.info(f"\nFixing {len(issues['orphaned_jobs'])} orphaned job IDs...")
            for job_id in issues['orphaned_jobs']:
                result = job_storage.redis.srem("jobs:active", job_id)
                if result:
                    logger.info(f"  ✅ Removed orphaned job ID: {job_id}")
                else:
                    logger.warning(f"  ❌ Failed to remove job ID: {job_id}")
        
        return 0 if sum(len(issue_list) for issue_list in issues.values()) == 0 else 1
        
    except Exception as e:
        logger.error(f"Failed to check job integrity: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
