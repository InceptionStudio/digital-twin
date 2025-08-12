#!/usr/bin/env python3
"""
Comprehensive test script for S3 storage functionality
"""

import os
import sys
import tempfile
import shutil
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_config():
    """Test configuration loading and environment variables"""
    logger.info("Testing configuration...")
    try:
        from config import Config
        
        # Check environment variables
        required_vars = [
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY', 
            'AWS_REGION',
            'S3_BUCKET_NAME'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            logger.info("Please set these in your .env file or environment")
            return False
        
        logger.info("✅ Environment variables configured")
        
        # Test S3 configuration
        logger.info(f"S3 Bucket: {Config.S3_BUCKET_NAME}")
        logger.info(f"AWS Region: {Config.AWS_REGION}")
        
        # Validate configuration
        Config.validate()
        logger.info("✅ Configuration validation passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {e}")
        return False

def test_s3_connection():
    """Simple test to check S3 connection"""
    logger.info("Testing S3 connection...")
    try:
        from s3_storage import S3Storage
        
        s3_storage = S3Storage()
        logger.info("✅ S3 connection successful")
        logger.info(f"   Bucket: {s3_storage.bucket_name}")
        
        # Try to list files (this will test the connection)
        files = s3_storage.list_files(prefix="", max_keys=5)
        logger.info(f"✅ S3 connection verified. Found {len(files)} files in bucket")
        return True
        
    except Exception as e:
        logger.error(f"❌ S3 connection failed: {e}")
        return False

def test_basic_operations():
    """Test basic S3 operations (upload, download, delete)"""
    logger.info("Testing basic S3 operations...")
    try:
        from s3_storage import S3Storage
        
        s3_storage = S3Storage()
        
        # Create a test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            test_content = "This is a test file for S3 storage verification"
            f.write(test_content)
            test_file_path = f.name
        
        # Upload the test file
        test_s3_key = "test/verification.txt"
        s3_url = s3_storage.upload_file(test_file_path, test_s3_key, "text/plain")
        logger.info(f"✅ File uploaded successfully: {s3_url}")
        
        # Test file existence
        if s3_storage.file_exists(test_s3_key):
            logger.info("✅ File existence check passed")
        else:
            logger.error("❌ File existence check failed")
            return False
        
        # Test file download
        download_path = tempfile.mktemp(suffix='.txt')
        s3_storage.download_file(test_s3_key, download_path)
        
        with open(download_path, 'r') as f:
            downloaded_content = f.read()
        
        if downloaded_content == test_content:
            logger.info("✅ File download and content verification passed")
        else:
            logger.error("❌ File content verification failed")
            return False
        
        # Test file info
        file_info = s3_storage.get_file_info(test_s3_key)
        logger.info(f"✅ File info retrieved: {file_info.get('size', 'unknown')} bytes")
        
        # Clean up test files
        os.unlink(test_file_path)
        os.unlink(download_path)
        
        # Test file deletion
        s3_storage.delete_file(test_s3_key)
        if not s3_storage.file_exists(test_s3_key):
            logger.info("✅ File deletion successful")
        else:
            logger.error("❌ File deletion failed")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Basic operations test failed: {e}")
        return False

def test_advanced_operations():
    """Test advanced S3 operations"""
    logger.info("Testing advanced S3 operations...")
    try:
        from s3_storage import S3Storage
        
        s3_storage = S3Storage()
        temp_dir = tempfile.mkdtemp()
        test_files = {}
        
        # Create test files
        try:
            # Create a text file
            text_file = os.path.join(temp_dir, "test.txt")
            with open(text_file, 'w') as f:
                f.write("This is a test file for S3 storage")
            test_files['text'] = text_file
            
            # Create a JSON file
            json_file = os.path.join(temp_dir, "test.json")
            with open(json_file, 'w') as f:
                f.write('{"test": "data", "number": 42}')
            test_files['json'] = json_file
            
            logger.info("✅ Test files created successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to create test files: {e}")
            return False
        
        # Test multiple file uploads
        uploaded_urls = {}
        try:
            # Upload text file
            text_url = s3_storage.upload_file(test_files['text'], "test/test.txt")
            uploaded_urls['text'] = text_url
            logger.info(f"✅ Text file uploaded: {text_url}")
            
            # Upload JSON file
            json_url = s3_storage.upload_file(test_files['json'], "test/test.json")
            uploaded_urls['json'] = json_url
            logger.info(f"✅ JSON file uploaded: {json_url}")
            
        except Exception as e:
            logger.error(f"❌ Failed to upload files: {e}")
            return False
        
        # Test file listing
        try:
            all_files = s3_storage.list_files()
            test_files_list = s3_storage.list_files(prefix="test/")
            
            logger.info(f"✅ Total files in bucket: {len(all_files)}")
            logger.info(f"✅ Test files: {test_files_list}")
            
        except Exception as e:
            logger.error(f"❌ Failed to list files: {e}")
            return False
        
        # Test file copying
        try:
            copied_url = s3_storage.copy_file("test/test.txt", "test/test_copy.txt")
            logger.info(f"✅ File copied: {copied_url}")
            
            # Verify copy exists
            copy_exists = s3_storage.file_exists("test/test_copy.txt")
            if copy_exists:
                logger.info("✅ Copy exists verification passed")
            else:
                logger.error("❌ Copy exists verification failed")
                return False
            
        except Exception as e:
            logger.error(f"❌ Failed to copy file: {e}")
            return False
        
        # Test content type detection
        try:
            # Test with explicit content type
            custom_url = s3_storage.upload_file(
                test_files['text'],
                "test/custom_content.txt",
                content_type="text/plain; charset=utf-8"
            )
            logger.info(f"✅ Custom content type upload: {custom_url}")
            
            # Test auto-detection
            auto_url = s3_storage.upload_file(
                test_files['json'],
                "test/auto_detect.json"
            )
            logger.info(f"✅ Auto-detected content type upload: {auto_url}")
            
        except Exception as e:
            logger.error(f"❌ Failed to test content type detection: {e}")
            return False
        
        # Test bucket info
        try:
            bucket_info = s3_storage.get_bucket_info()
            logger.info(f"✅ Bucket info: {bucket_info.get('name', 'unknown')} in {bucket_info.get('region', 'unknown')}")
        except Exception as e:
            logger.error(f"❌ Bucket info test failed: {e}")
            return False
        
        # Cleanup test files
        try:
            files_to_delete = [
                "test/test.txt",
                "test/test.json", 
                "test/test_copy.txt",
                "test/custom_content.txt",
                "test/auto_detect.json"
            ]
            
            deleted_count = 0
            for file_key in files_to_delete:
                if s3_storage.file_exists(file_key):
                    s3_storage.delete_file(file_key)
                    deleted_count += 1
                    logger.info(f"✅ Deleted: {file_key}")
            
            logger.info(f"✅ Cleanup complete: {deleted_count} files deleted")
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup files: {e}")
            return False
        
        # Cleanup local files
        try:
            shutil.rmtree(temp_dir)
            logger.info(f"✅ Local temp directory cleaned up: {temp_dir}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to cleanup local temp directory: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Advanced operations test failed: {e}")
        return False

def test_s3_storage():
    """Comprehensive S3 storage test suite"""
    logger.info("🧪 Starting comprehensive S3 storage test suite...")
    
    # Test configuration first
    if not test_config():
        logger.error("❌ Configuration test failed")
        return False
    
    # Test connection
    if not test_s3_connection():
        logger.error("❌ Connection test failed")
        return False
    
    # Test basic operations
    if not test_basic_operations():
        logger.error("❌ Basic operations test failed")
        return False
    
    # Test advanced operations
    if not test_advanced_operations():
        logger.error("❌ Advanced operations test failed")
        return False
    
    logger.info("🎉 All S3 tests passed successfully!")
    return True

if __name__ == "__main__":
    print("🧪 Comprehensive S3 Storage Test Suite")
    print("=" * 60)
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--connection-only":
            print("🔗 Running connection test only...")
            if test_config() and test_s3_connection():
                print("\n✅ Connection test passed!")
            else:
                print("\n❌ Connection test failed!")
                exit(1)
        elif sys.argv[1] == "--basic":
            print("🔧 Running basic operations test...")
            if test_config() and test_s3_connection() and test_basic_operations():
                print("\n✅ Basic operations test passed!")
            else:
                print("\n❌ Basic operations test failed!")
                exit(1)
        elif sys.argv[1] == "--help":
            print("Usage:")
            print("  python test_s3.py                    # Run all tests")
            print("  python test_s3.py --connection-only  # Test connection only")
            print("  python test_s3.py --basic           # Test basic operations")
            print("  python test_s3.py --help            # Show this help")
            exit(0)
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Use --help for usage information")
            exit(1)
    else:
        # Run comprehensive test suite
        if test_s3_storage():
            print("\n🎉 All tests passed! S3 storage is working correctly.")
        else:
            print("\n❌ S3 tests failed. Please check your configuration and credentials.")
            exit(1)
