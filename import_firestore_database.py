#!/usr/bin/env python3
"""
Utility to import data from JSON files back into Firestore.

This script:
1. Reads JSON files created by dump_firestore_database.py
2. Imports documents back into Firestore
3. Provides options for dry-run and conflict handling
4. Supports batch operations for efficiency
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
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


def import_json_to_firestore(job_storage, json_file: str, dry_run: bool = False, 
                            conflict_action: str = "skip") -> Dict[str, int]:
    """
    Import documents from JSON file to Firestore.
    
    Args:
        job_storage: Job storage instance
        json_file: Path to JSON file to import
        dry_run: If True, don't actually import, just show what would be imported
        conflict_action: How to handle conflicts ("skip", "overwrite", "error")
    
    Returns:
        Dictionary with import statistics
    """
    try:
        # Read JSON file
        with open(json_file, 'r', encoding='utf-8') as f:
            documents = json.load(f)
        
        logger.info(f"Loaded {len(documents)} documents from {json_file}")
        
        stats = {
            "total": len(documents),
            "imported": 0,
            "skipped": 0,
            "errors": 0,
            "overwritten": 0
        }
        
        if dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
        
        # Process each document
        for i, doc_data in enumerate(documents, 1):
            doc_id = doc_data.get("id")
            if not doc_id:
                logger.warning(f"Document {i} has no ID, skipping")
                stats["errors"] += 1
                continue
            
            try:
                # Check if document already exists
                existing_doc = job_storage.get_job(doc_id)
                
                if existing_doc:
                    if conflict_action == "skip":
                        logger.info(f"Document {doc_id} already exists, skipping")
                        stats["skipped"] += 1
                        continue
                    elif conflict_action == "error":
                        logger.error(f"Document {doc_id} already exists, aborting")
                        stats["errors"] += 1
                        if not dry_run:
                            return stats
                    elif conflict_action == "overwrite":
                        logger.info(f"Document {doc_id} already exists, overwriting")
                        stats["overwritten"] += 1
                
                if not dry_run:
                    # Import the document
                    doc_ref = job_storage.collection.document(doc_id)
                    doc_ref.set(doc_data, merge=False)
                    logger.info(f"Imported document {doc_id}")
                
                stats["imported"] += 1
                
                if i % 10 == 0:
                    logger.info(f"Processed {i}/{len(documents)} documents...")
                
            except Exception as e:
                logger.error(f"Failed to import document {doc_id}: {e}")
                stats["errors"] += 1
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to import from {json_file}: {e}")
        return {"total": 0, "imported": 0, "skipped": 0, "errors": 1, "overwritten": 0}


def validate_json_file(json_file: str) -> bool:
    """
    Validate that a JSON file is properly formatted and contains documents.
    
    Args:
        json_file: Path to JSON file to validate
    
    Returns:
        True if valid, False otherwise
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            documents = json.load(f)
        
        if not isinstance(documents, list):
            logger.error(f"JSON file must contain a list of documents, got {type(documents)}")
            return False
        
        if len(documents) == 0:
            logger.warning("JSON file contains no documents")
            return False
        
        # Check that documents have required fields
        for i, doc in enumerate(documents):
            if not isinstance(doc, dict):
                logger.error(f"Document {i} is not a dictionary")
                return False
            
            if "id" not in doc:
                logger.error(f"Document {i} is missing 'id' field")
                return False
        
        logger.info(f"JSON file validation passed: {len(documents)} documents")
        return True
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON file: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to validate JSON file: {e}")
        return False


def main():
    """Main function to import data to Firestore."""
    
    parser = argparse.ArgumentParser(description="Import data from JSON files to Firestore")
    parser.add_argument("json_file", help="Path to JSON file to import")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be imported without making changes")
    parser.add_argument("--conflict", choices=["skip", "overwrite", "error"], default="skip",
                       help="How to handle conflicts (default: skip)")
    parser.add_argument("--project-id", help="Firestore project ID (defaults to FIRESTORE_PROJECT_ID env var)")
    parser.add_argument("--collection", default="jobs", help="Firestore collection name (default: jobs)")
    parser.add_argument("--validate-only", action="store_true", help="Only validate JSON file, don't import")
    
    args = parser.parse_args()
    
    # Check if JSON file exists
    if not os.path.exists(args.json_file):
        logger.error(f"JSON file not found: {args.json_file}")
        sys.exit(1)
    
    # Validate JSON file
    if not validate_json_file(args.json_file):
        logger.error("JSON file validation failed")
        sys.exit(1)
    
    if args.validate_only:
        logger.info("Validation-only mode: JSON file is valid")
        return
    
    # Initialize job storage
    storage_type = os.getenv("JOB_STORAGE", "firestore")
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    project_id = args.project_id or os.getenv("FIRESTORE_PROJECT_ID")
    firestore_collection = os.getenv("FIRESTORE_COLLECTION", "jobs")
    
    if storage_type != "firestore" or not project_id:
        logger.error("This utility requires Firestore storage and FIRESTORE_PROJECT_ID")
        sys.exit(1)
    
    try:
        # Initialize storage
        logger.info(f"Connecting to Firestore project: {project_id}")
        job_storage = create_job_storage(
            storage_type, 
            redis_url, 
            project_id,
            firestore_collection
        )
        
        # Import data
        stats = import_json_to_firestore(
            job_storage,
            args.json_file,
            dry_run=args.dry_run,
            conflict_action=args.conflict
        )
        
        # Print summary
        logger.info("=" * 60)
        logger.info("IMPORT SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total documents: {stats['total']}")
        logger.info(f"Imported: {stats['imported']}")
        logger.info(f"Skipped: {stats['skipped']}")
        logger.info(f"Overwritten: {stats['overwritten']}")
        logger.info(f"Errors: {stats['errors']}")
        
        if args.dry_run:
            logger.info("DRY RUN COMPLETED - No changes were made")
        else:
            logger.info("Import completed!")
        
    except Exception as e:
        logger.error(f"Import failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
