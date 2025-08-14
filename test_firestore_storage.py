#!/usr/bin/env python3
"""
Test script for Firestore job storage implementation.
"""

import os
import sys
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from job_storage import create_job_storage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_firestore_storage():
    """Test Firestore job storage functionality."""
    
    # Check if Firestore credentials are configured
    project_id = os.getenv("FIRESTORE_PROJECT_ID")
    if not project_id:
        logger.error("FIRESTORE_PROJECT_ID environment variable not set")
        logger.info("Set it with: export FIRESTORE_PROJECT_ID='your-project-id'")
        return False
    
    try:
        # Initialize Firestore storage
        logger.info(f"Initializing Firestore storage with project: {project_id}")
        storage = create_job_storage("firestore", firestore_project_id=project_id)
        
        # Test 1: Create a job
        logger.info("Test 1: Creating a job...")
        job_data = {
            "input_text": "Test job for Firestore",
            "persona_id": "chad_goldstein",
            "test": True
        }
        
        job_id = storage.create_job(job_data)
        logger.info(f"Created job with ID: {job_id}")
        
        # Test 2: Get the job
        logger.info("Test 2: Retrieving the job...")
        retrieved_job = storage.get_job(job_id)
        if retrieved_job:
            logger.info(f"Retrieved job: {retrieved_job.get('input_text')}")
        else:
            logger.error("Failed to retrieve job")
            return False
        
        # Test 3: Update the job
        logger.info("Test 3: Updating the job...")
        updates = {
            "status": "completed",
            "progress": "Test completed successfully"
        }
        success = storage.update_job(job_id, updates)
        if success:
            logger.info("Job updated successfully")
        else:
            logger.error("Failed to update job")
            return False
        
        # Test 4: Get updated job
        logger.info("Test 4: Retrieving updated job...")
        updated_job = storage.get_job(job_id)
        if updated_job and updated_job.get("status") == "completed":
            logger.info("Updated job retrieved successfully")
        else:
            logger.error("Failed to retrieve updated job")
            return False
        
        # Test 5: List jobs
        logger.info("Test 5: Listing jobs...")
        jobs = storage.list_jobs(limit=10)
        logger.info(f"Found {len(jobs)} jobs in storage")
        
        # Test 6: Cleanup - delete the test job
        logger.info("Test 6: Cleaning up test job...")
        deleted = storage.delete_job(job_id)
        if deleted:
            logger.info("Test job deleted successfully")
        else:
            logger.error("Failed to delete test job")
            return False
        
        # Test 7: Verify deletion
        logger.info("Test 7: Verifying deletion...")
        deleted_job = storage.get_job(job_id)
        if deleted_job is None:
            logger.info("Job deletion verified successfully")
        else:
            logger.error("Job still exists after deletion")
            return False
        
        logger.info("✅ All Firestore storage tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Firestore storage test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_firestore_storage()
    sys.exit(0 if success else 1)
