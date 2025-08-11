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
    
    # Safety check: Ensure Redis is used when workers > 1
    if workers > 1:
        job_storage = os.getenv("JOB_STORAGE", "memory")
        if job_storage == "memory":
            print("❌ ERROR: Cannot use in-memory job storage with multiple workers!")
            print("   Set JOB_STORAGE=redis and ensure Redis is running.")
            print("   Example: JOB_STORAGE=redis REDIS_URL=redis://localhost:6379 python start_server.py")
            exit(1)
        
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        print(f"🔗 Using Redis for job storage: {redis_url}")
    
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
