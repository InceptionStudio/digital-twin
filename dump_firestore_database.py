#!/usr/bin/env python3
"""
Utility to dump the entire Firestore database to JSON format for easy import.

This script:
1. Connects to the Firestore database
2. Dumps all collections to JSON files
3. Provides options for filtering and formatting
4. Creates a comprehensive backup of the database
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


def dump_collection_to_json(collection, output_file: str, status_filter: Optional[str] = None, 
                           limit: Optional[int] = None, pretty_print: bool = True) -> int:
    """
    Dump a Firestore collection to JSON file.
    
    Args:
        collection: Firestore collection reference
        output_file: Path to output JSON file
        status_filter: Optional status filter (e.g., "completed", "failed")
        limit: Optional limit on number of documents
        pretty_print: Whether to pretty print the JSON
    
    Returns:
        Number of documents dumped
    """
    try:
        # Build query
        query = collection
        
        if status_filter:
            query = query.where("status", "==", status_filter)
            logger.info(f"Filtering by status: {status_filter}")
        
        if limit:
            query = query.limit(limit)
            logger.info(f"Limiting to {limit} documents")
        
        # Order by created_at if available (but not when filtering to avoid index issues)
        if not status_filter:
            try:
                query = query.order_by("created_at", direction="DESCENDING")
            except Exception:
                # If created_at field doesn't exist or can't be ordered, continue without ordering
                logger.info("Could not order by created_at, using default ordering")
        else:
            logger.info("Skipping ordering due to status filter to avoid index requirements")
        
        # Collect documents
        documents = []
        doc_count = 0
        
        for doc in query.stream():
            doc_data = doc.to_dict()
            doc_count += 1
            
            # Convert datetime objects to ISO strings for JSON serialization
            doc_data = convert_datetime_to_string(doc_data)
            documents.append(doc_data)
            
            if doc_count % 100 == 0:
                logger.info(f"Processed {doc_count} documents...")
        
        # Write to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            if pretty_print:
                json.dump(documents, f, indent=2, ensure_ascii=False)
            else:
                json.dump(documents, f, ensure_ascii=False)
        
        logger.info(f"Dumped {doc_count} documents to {output_file}")
        return doc_count
        
    except Exception as e:
        logger.error(f"Failed to dump collection to {output_file}: {e}")
        return 0


def convert_datetime_to_string(obj: Any) -> Any:
    """
    Recursively convert datetime objects to ISO format strings.
    
    Args:
        obj: Object to convert (can be dict, list, or primitive type)
    
    Returns:
        Object with datetime objects converted to strings
    """
    if isinstance(obj, dict):
        return {key: convert_datetime_to_string(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime_to_string(item) for item in obj]
    elif hasattr(obj, 'isoformat'):
        # It's a datetime object
        return obj.isoformat()
    else:
        return obj


def dump_database_summary(job_storage, output_dir: str) -> Dict[str, Any]:
    """
    Create a summary of the database contents.
    
    Args:
        job_storage: Job storage instance
        output_dir: Directory to save summary
    
    Returns:
        Summary dictionary
    """
    try:
        summary = {
            "dump_timestamp": datetime.now(timezone.utc).isoformat(),
            "database_info": {
                "project_id": job_storage.db.project if hasattr(job_storage, 'db') else "unknown",
                "collection": job_storage.collection.id if hasattr(job_storage, 'collection') else "unknown"
            },
            "statistics": {}
        }
        
        # Get basic statistics
        all_jobs = job_storage.list_jobs(limit=10000)
        summary["statistics"]["total_jobs"] = len(all_jobs)
        
        # Status breakdown
        status_counts = {}
        persona_counts = {}
        step_counts = {}
        
        for job in all_jobs:
            status = job.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
            
            persona = job.get("persona_name", "unknown")
            persona_counts[persona] = persona_counts.get(persona, 0) + 1
            
            step = job.get("step", "unknown")
            step_counts[step] = step_counts.get(step, 0) + 1
        
        summary["statistics"]["status_breakdown"] = status_counts
        summary["statistics"]["persona_breakdown"] = persona_counts
        summary["statistics"]["step_breakdown"] = step_counts
        
        # Save summary
        summary_file = os.path.join(output_dir, "database_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Database summary saved to {summary_file}")
        return summary
        
    except Exception as e:
        logger.error(f"Failed to create database summary: {e}")
        return {}


def main():
    """Main function to dump the Firestore database."""
    
    parser = argparse.ArgumentParser(description="Dump Firestore database to JSON format")
    parser.add_argument("--output-dir", default="./firestore_dump", 
                       help="Output directory for dump files (default: ./firestore_dump)")
    parser.add_argument("--status", help="Filter by job status (e.g., completed, failed, pending)")
    parser.add_argument("--limit", type=int, help="Limit number of documents to dump")
    parser.add_argument("--no-pretty", action="store_true", help="Disable pretty printing (compact JSON)")
    parser.add_argument("--project-id", help="Firestore project ID (defaults to FIRESTORE_PROJECT_ID env var)")
    parser.add_argument("--collection", default="jobs", help="Firestore collection name (default: jobs)")
    parser.add_argument("--summary-only", action="store_true", help="Only generate summary, don't dump data")
    
    args = parser.parse_args()
    
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
        
        # Create output directory
        os.makedirs(args.output_dir, exist_ok=True)
        logger.info(f"Output directory: {args.output_dir}")
        
        # Generate summary
        summary = dump_database_summary(job_storage, args.output_dir)
        
        if args.summary_only:
            logger.info("Summary-only mode: skipping data dump")
            return
        
        # Dump collection data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Determine output filename
        filename_parts = ["firestore_dump"]
        if args.status:
            filename_parts.append(f"status_{args.status}")
        if args.limit:
            filename_parts.append(f"limit_{args.limit}")
        filename_parts.append(timestamp)
        
        output_file = os.path.join(args.output_dir, f"{'_'.join(filename_parts)}.json")
        
        # Dump the collection
        doc_count = dump_collection_to_json(
            job_storage.collection,
            output_file,
            status_filter=args.status,
            limit=args.limit,
            pretty_print=not args.no_pretty
        )
        
        # Create a README file with dump information
        readme_content = f"""# Firestore Database Dump

Generated on: {datetime.now(timezone.utc).isoformat()}

## Files:
- `database_summary.json`: Database statistics and summary
- `{os.path.basename(output_file)}`: Main data dump ({doc_count} documents)

## Dump Parameters:
- Project ID: {project_id}
- Collection: {firestore_collection}
- Status Filter: {args.status or 'None'}
- Document Limit: {args.limit or 'None'}
- Pretty Print: {not args.no_pretty}

## Database Statistics:
- Total Jobs: {summary.get('statistics', {}).get('total_jobs', 'Unknown')}
- Status Breakdown: {summary.get('statistics', {}).get('status_breakdown', {})}
- Persona Breakdown: {summary.get('statistics', {}).get('persona_breakdown', {})}

## Import Instructions:
To import this data back to Firestore, you can use the update_jobs_from_jsonl.py script
or write a custom import script that reads the JSON file and creates documents.
"""
        
        readme_file = os.path.join(args.output_dir, "README.md")
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        logger.info(f"Dump completed successfully!")
        logger.info(f"Files created in: {args.output_dir}")
        logger.info(f"- Main data: {os.path.basename(output_file)} ({doc_count} documents)")
        logger.info(f"- Summary: database_summary.json")
        logger.info(f"- Documentation: README.md")
        
    except Exception as e:
        logger.error(f"Database dump failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
