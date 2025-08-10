import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY")
    HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
    
    # Voice and Avatar Settings
    ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Default voice
    HEYGEN_AVATAR_ID = os.getenv("HEYGEN_AVATAR_ID")
    HEYGEN_VOICE_ID = os.getenv("HEYGEN_VOICE_ID", "82025eb9625b4c09aec78f89528cc33a")  # Default HeyGen voice
    
    # File Settings
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    TEMP_DIR = Path(os.getenv("TEMP_DIR", "./temp"))
    OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./output"))
    
    # Create directories if they don't exist
    TEMP_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Validation
    @classmethod
    def validate(cls):
        missing = []
        if not cls.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")
        if not cls.ELEVENLABS_API_KEY:
            missing.append("ELEVENLABS_API_KEY")
        if not cls.HEYGEN_API_KEY:
            missing.append("HEYGEN_API_KEY")
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return True
