#!/usr/bin/env python3
"""
Setup script for Chad Goldstein Digital Twin
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"📋 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed")
            return True
        else:
            print(f"❌ {description} failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} failed: {str(e)}")
        return False

def main():
    """Main setup function."""
    print("🚀 Chad Goldstein Digital Twin Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return 1
    
    print(f"✅ Python {sys.version.split()[0]} detected")
    
    # Install requirements
    print("\n📦 Installing Python packages...")
    if not run_command("pip install -r requirements.txt", "Package installation"):
        print("⚠️  Package installation failed. You may need to install manually.")
    
    # Create directories
    print("\n📁 Creating directories...")
    directories = ["temp", "output"]
    for dir_name in directories:
        dir_path = Path(dir_name)
        dir_path.mkdir(exist_ok=True)
        print(f"✅ Created {dir_name}/ directory")
    
    # Check for .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("\n🔧 Creating sample .env file...")
        sample_env = """# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# ElevenLabs API Configuration
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM

# HeyGen API Configuration
HEYGEN_API_KEY=your_heygen_api_key_here
HEYGEN_AVATAR_ID=your_avatar_id_here

# Application Configuration (optional)
MAX_FILE_SIZE_MB=50
TEMP_DIR=./temp
OUTPUT_DIR=./output"""
        
        with open(".env", "w") as f:
            f.write(sample_env)
        print("✅ Created .env file with sample configuration")
        print("⚠️  Please edit .env file with your actual API keys")
    else:
        print("✅ .env file already exists")
    
    # Make CLI executable
    cli_path = Path("cli.py")
    if cli_path.exists():
        os.chmod(cli_path, 0o755)
        print("✅ Made cli.py executable")
    
    # Test basic imports
    print("\n🧪 Testing imports...")
    test_imports = [
        ("openai", "OpenAI API client"),
        ("elevenlabs", "ElevenLabs client"),
        ("requests", "HTTP requests"),
        ("pydub", "Audio processing"),
        ("fastapi", "Web API framework")
    ]
    
    all_imports_ok = True
    for module, description in test_imports:
        try:
            __import__(module)
            print(f"✅ {description}")
        except ImportError:
            print(f"❌ {description} - not installed")
            all_imports_ok = False
    
    if not all_imports_ok:
        print("\n⚠️  Some packages are missing. Run: pip install -r requirements.txt")
    
    # Final instructions
    print("\n" + "=" * 50)
    print("🎉 Setup completed!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your API keys:")
    print("   - Get OpenAI API key from: https://platform.openai.com/api-keys")
    print("   - Get ElevenLabs API key from: https://elevenlabs.io/")
    print("   - Get HeyGen API key from: https://www.heygen.com/")
    print("\n2. Test the setup:")
    print("   python cli.py --test")
    print("\n3. Try a quick demo:")
    print("   python cli.py --text 'Your startup pitch here'")
    print("\n4. Start the web API:")
    print("   python web_api.py")
    print("\n5. Run examples:")
    print("   python example_usage.py")
    
    return 0 if all_imports_ok else 1

if __name__ == "__main__":
    sys.exit(main())
