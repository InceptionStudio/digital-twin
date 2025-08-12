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

    
    # Default Voice IDs
    DEFAULT_ELEVENLABS_VOICE_ID = "zqjPlH84bFLbo8q9PPo7" # Sarah Guo
    DEFAULT_HEYGEN_VOICE_ID = "cb8c232f08a9466c870ad2c037fcf77a" # Sarah Guo
    
    # Default Avatar IDs
    DEFAULT_HEYGEN_AVATAR_ID = "129fa3d48fad41e4975c4e9471d953fb" # Sarah Guo
    
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
