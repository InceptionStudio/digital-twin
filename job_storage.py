"""
Job storage system for Digital Twin API
Supports both in-memory (development) and Redis (production) storage
"""

import json
import uuid
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

class JobStorage:
    """Abstract job storage interface"""
    
    def create_job(self, job_data: Dict[str, Any]) -> str:
        """Create a new job and return its ID"""
        raise NotImplementedError
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID"""
        raise NotImplementedError
    
    def update_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """Update job data"""
        raise NotImplementedError
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job"""
        raise NotImplementedError
    
    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """Clean up old completed/failed jobs"""
        raise NotImplementedError

class InMemoryJobStorage(JobStorage):
    """In-memory job storage (for development/single worker)"""
    
    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}
    
    def create_job(self, job_data: Dict[str, Any]) -> str:
        job_id = str(uuid.uuid4())
        job_data.update({
            "id": job_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending"
        })
        self.jobs[job_id] = job_data
        logger.info(f"Created job {job_id}")
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self.jobs.get(job_id)
    
    def update_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        if job_id not in self.jobs:
            return False
        
        self.jobs[job_id].update(updates)
        self.jobs[job_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
        logger.info(f"Updated job {job_id}: {updates}")
        return True
    
    def delete_job(self, job_id: str) -> bool:
        if job_id in self.jobs:
            del self.jobs[job_id]
            logger.info(f"Deleted job {job_id}")
            return True
        return False
    
    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        deleted_count = 0
        
        for job_id, job_data in list(self.jobs.items()):
            created_at_str = job_data.get("created_at", "1970-01-01T00:00:00+00:00")
            # Handle both timezone-aware and timezone-naive timestamps
            try:
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            except ValueError:
                # Fallback for timezone-naive timestamps
                created_at = datetime.fromisoformat(created_at_str).replace(tzinfo=timezone.utc)
            
            status = job_data.get("status", "unknown")
            
            if created_at < cutoff and status in ["completed", "failed", "cancelled"]:
                del self.jobs[job_id]
                deleted_count += 1
        
        logger.info(f"Cleaned up {deleted_count} old jobs")
        return deleted_count

class RedisJobStorage(JobStorage):
    """Redis-based job storage (for production/multiple workers)"""
    
    def __init__(self, redis_url: str = "redis://redis:6379"):
        try:
            import redis
            self.redis = redis.from_url(redis_url, decode_responses=True)
            self.redis.ping()  # Test connection
            logger.info("Connected to Redis for job storage")
        except ImportError:
            raise ImportError("Redis not installed. Run: pip install redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def create_job(self, job_data: Dict[str, Any]) -> str:
        job_id = str(uuid.uuid4())
        job_data.update({
            "id": job_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending"
        })
        
        # Store job data
        self.redis.set(
            f"job:{job_id}",
            json.dumps(job_data)
        )
        
        # Add to job list for cleanup
        self.redis.sadd("jobs:active", job_id)
        
        logger.info(f"Created job {job_id} in Redis")
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        job_data = self.redis.get(f"job:{job_id}")
        if job_data:
            return json.loads(job_data)
        return None
    
    def update_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        job_data = self.get_job(job_id)
        if not job_data:
            return False
        
        job_data.update(updates)
        job_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Update in Redis
        self.redis.set(
            f"job:{job_id}",
            json.dumps(job_data)
        )
        
        logger.info(f"Updated job {job_id} in Redis: {updates}")
        return True
    
    def delete_job(self, job_id: str) -> bool:
        deleted = self.redis.delete(f"job:{job_id}")
        self.redis.srem("jobs:active", job_id)
        
        if deleted:
            logger.info(f"Deleted job {job_id} from Redis")
            return True
        return False
    
    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        deleted_count = 0
        
        # Get all active job IDs
        job_ids = self.redis.smembers("jobs:active")
        
        for job_id in job_ids:
            job_data = self.get_job(job_id)
            if not job_data:
                continue
            
            created_at_str = job_data.get("created_at", "1970-01-01T00:00:00+00:00")
            # Handle both timezone-aware and timezone-naive timestamps
            try:
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            except ValueError:
                # Fallback for timezone-naive timestamps
                created_at = datetime.fromisoformat(created_at_str).replace(tzinfo=timezone.utc)
            
            status = job_data.get("status", "unknown")
            
            if created_at < cutoff and status in ["completed", "failed", "cancelled"]:
                self.delete_job(job_id)
                deleted_count += 1
        
        logger.info(f"Cleaned up {deleted_count} old jobs from Redis")
        return deleted_count

# Factory function to create appropriate storage
def create_job_storage(storage_type: str = "memory", redis_url: str = "redis://redis:6379", workers: int = 1) -> JobStorage:
    """Create job storage based on configuration"""
    
    # Safety check: Never allow in-memory storage with multiple workers
    if workers > 1 and storage_type == "memory":
        raise ValueError(
            f"Cannot use in-memory job storage with {workers} workers. "
            "Set JOB_STORAGE=redis and ensure Redis is running."
        )
    
    if storage_type == "redis":
        try:
            return RedisJobStorage(redis_url)
        except Exception as e:
            # Fail if Redis is not available
            raise RuntimeError(
                f"Failed to initialize Redis storage: {e}. "
                "Redis is required when JOB_STORAGE=redis. "
                "Ensure Redis is running via docker-compose."
            )
    else:
        if workers > 1:
            raise ValueError(
                f"In-memory storage not allowed with {workers} workers. "
                "Set JOB_STORAGE=redis and ensure Redis is running."
            )
        return InMemoryJobStorage()
