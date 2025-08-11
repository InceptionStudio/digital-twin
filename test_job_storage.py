#!/usr/bin/env python3
"""
Test script to verify job storage behavior
"""

import os
import sys
from job_storage import create_job_storage

def test_job_storage():
    """Test job storage with different configurations"""
    
    print("🧪 Testing Job Storage Configuration")
    print("=" * 50)
    
    # Test 1: Single worker with in-memory (should work)
    print("\n1️⃣ Testing single worker with in-memory storage:")
    try:
        storage = create_job_storage("memory", workers=1)
        print("✅ Success: Single worker with in-memory storage works")
        
        # Test basic operations
        job_id = storage.create_job({"test": "data"})
        job = storage.get_job(job_id)
        print(f"✅ Job created and retrieved: {job_id}")
        
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 2: Multiple workers with in-memory (should fail)
    print("\n2️⃣ Testing multiple workers with in-memory storage:")
    try:
        storage = create_job_storage("memory", workers=4)
        print("❌ Should have failed!")
    except ValueError as e:
        print(f"✅ Correctly failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    # Test 3: Multiple workers with Redis (should work if Redis available)
    print("\n3️⃣ Testing multiple workers with Redis storage:")
    try:
        storage = create_job_storage("redis", "redis://localhost:6379", workers=4)
        print("✅ Success: Multiple workers with Redis storage works")
        
        # Test basic operations
        job_id = storage.create_job({"test": "data"})
        job = storage.get_job(job_id)
        print(f"✅ Job created and retrieved: {job_id}")
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        print("   (This is expected if Redis is not running)")
    
    # Test 4: Environment variable detection
    print("\n4️⃣ Testing environment variable detection:")
    os.environ["WORKERS"] = "4"
    os.environ["JOB_STORAGE"] = "memory"
    
    try:
        storage = create_job_storage(
            os.getenv("JOB_STORAGE", "memory"),
            os.getenv("REDIS_URL", "redis://localhost:6379"),
            int(os.getenv("WORKERS", "1"))
        )
        print("❌ Should have failed with 4 workers and memory storage!")
    except ValueError as e:
        print(f"✅ Correctly failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test Summary:")
    print("- Single worker + in-memory: ✅ Allowed")
    print("- Multiple workers + in-memory: ❌ Blocked")
    print("- Multiple workers + Redis: ✅ Allowed (if Redis available)")

if __name__ == "__main__":
    test_job_storage()
