#!/usr/bin/env python3
"""
Redis setup helper for Digital Twin API
"""

import subprocess
import sys
import os

def check_redis_installed():
    """Check if Redis is installed and running"""
    try:
        # Check if redis-server is available
        result = subprocess.run(['which', 'redis-server'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Redis server found")
            return True
        else:
            print("❌ Redis server not found")
            return False
    except Exception as e:
        print(f"❌ Error checking Redis: {e}")
        return False

def check_redis_running():
    """Check if Redis is running on localhost:6379"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis is running on localhost:6379")
        return True
    except Exception as e:
        print(f"❌ Redis not running: {e}")
        return False

def install_redis_homebrew():
    """Install Redis using Homebrew"""
    print("🍺 Installing Redis via Homebrew...")
    try:
        # Fix permissions first
        subprocess.run(['sudo', 'chown', '-R', '$(whoami)', '/usr/local/var/log', '/usr/local/var/db'], check=True)
        subprocess.run(['brew', 'install', 'redis'], check=True)
        print("✅ Redis installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Redis: {e}")
        return False

def start_redis_server():
    """Start Redis server"""
    print("🚀 Starting Redis server...")
    try:
        subprocess.run(['redis-server', '--daemonize', 'yes'], check=True)
        print("✅ Redis server started")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Redis server: {e}")
        return False

def setup_redis():
    """Main setup function"""
    print("🔧 Redis Setup for Digital Twin API")
    print("=" * 40)
    
    # Check if Redis is already running
    if check_redis_running():
        print("\n🎉 Redis is already set up and running!")
        return True
    
    # Check if Redis is installed
    if not check_redis_installed():
        print("\n📦 Redis not installed. Installing...")
        if not install_redis_homebrew():
            print("\n❌ Failed to install Redis via Homebrew.")
            print("Please install Redis manually:")
            print("  brew install redis")
            print("  OR")
            print("  docker run -d --name redis -p 6379:6379 redis:7-alpine")
            return False
    
    # Start Redis server
    if not start_redis_server():
        print("\n❌ Failed to start Redis server.")
        print("Please start Redis manually:")
        print("  redis-server")
        return False
    
    # Verify Redis is running
    if check_redis_running():
        print("\n🎉 Redis setup completed successfully!")
        print("\nYou can now run the Digital Twin API with multiple workers:")
        print("  JOB_STORAGE=redis REDIS_URL=redis://localhost:6379 python start_server.py")
        return True
    else:
        print("\n❌ Redis setup failed.")
        return False

if __name__ == "__main__":
    success = setup_redis()
    sys.exit(0 if success else 1)
