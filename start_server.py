#!/usr/bin/env python3
"""
Production server startup script for Digital Twin API
Handles multiple concurrent requests with proper worker configuration
"""

import uvicorn
import multiprocessing
import os

def start_server():
    """Start the server with optimal settings for production"""
    
    # Calculate optimal number of workers
    # Generally (2 x num_cores) + 1, but cap at 8 for this application
    cpu_count = multiprocessing.cpu_count()
    workers = min((2 * cpu_count) + 1, 8)
    
    # Environment variables for configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    workers = int(os.getenv("WORKERS", str(workers)))
    
    print(f"🚀 Starting Digital Twin API Server")
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"👥 Workers: {workers}")
    print(f"💻 CPU Cores: {cpu_count}")
    
    # Safety check: Ensure Redis or Firestore is used when workers > 1
    if workers > 1:
        job_storage = os.getenv("JOB_STORAGE", "memory")
        if job_storage == "memory":
            print("❌ ERROR: Cannot use in-memory job storage with multiple workers!")
            print("   Set JOB_STORAGE=redis or JOB_STORAGE=firestore and ensure the service is running.")
            print("   Example: docker-compose up (for Redis)")
            print("   Example: Set FIRESTORE_PROJECT_ID for Firestore")
            exit(1)
        
        if job_storage == "redis":
            redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
            print(f"🔗 Using Redis for job storage: {redis_url}")
            print("   Ensure Redis is running via docker-compose: docker-compose up")
        elif job_storage == "firestore":
            firestore_project_id = os.getenv("FIRESTORE_PROJECT_ID")
            firestore_collection = os.getenv("FIRESTORE_COLLECTION", "jobs")
            print(f"🔥 Using Firestore for job storage: {firestore_project_id}/{firestore_collection}")
            print("   Ensure Google Cloud credentials are properly configured")
        else:
            print(f"❌ ERROR: Unknown job storage type: {job_storage}")
            print("   Supported types: memory, redis, firestore")
            exit(1)
    
    # Start uvicorn with production settings
    uvicorn.run(
        "web_api:app",
        host=host,
        port=port,
        workers=workers,
        loop="uvloop",  # Faster event loop
        http="httptools",  # Faster HTTP parser
        access_log=True,
        log_level="info"
    )

if __name__ == "__main__":
    start_server()
