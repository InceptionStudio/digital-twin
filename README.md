# Chad Goldstein Digital Twin

A complete workflow system that generates hot take responses in the style of Chad Goldstein, a flamboyant venture capitalist, from audio and video inputs.

## Features

🎬 **Audio/Video Processing**: Convert speech to text using OpenAI Whisper
💬 **AI Hot Takes**: Generate responses using GPT-4/GPT-5 with Chad's personality
🎵 **Voice Synthesis**: Convert text to speech using ElevenLabs
🎥 **Avatar Videos**: Create talking avatar videos using HeyGen Avatar IV

## Workflow

```
Audio/Video Input → Transcript → Hot Take → Voice → Avatar Video
```

## Installation

1. **Clone and setup**:
```bash
git clone <repository>
cd digital-twin
pip install -r requirements.txt
```

2. **Configure environment variables**:
Create a `.env` file with your API keys:
```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# ElevenLabs API Configuration
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# HeyGen API Configuration
HEYGEN_API_KEY=your_heygen_api_key_here

# Application Configuration (optional)
MAX_FILE_SIZE_MB=50
TEMP_DIR=./temp
OUTPUT_DIR=./output
```

## Usage

### Command Line Interface

**Process audio/video file**:
```bash
python cli.py --file "pitch_recording.mp4" --context "Series A startup pitch"
```

**Process text input**:
```bash
python cli.py --text "We're building an AI-powered dog walking app" --context "Pet tech startup"
```

**Generate quick roast**:
```bash
python cli.py --roast "NFT marketplace for pets"
```

**Test connections**:
```bash
python cli.py --test
```

**Get service info**:
```bash
python cli.py --info
```

### Web API

**Start the API server**:
```bash
python web_api.py
# or
uvicorn web_api:app --host 0.0.0.0 --port 8000
```

**API Endpoints**:

- `POST /process-file` - Upload audio/video file
- `POST /process-text` - Process text input  
- `POST /quick-roast` - Generate quick roast
- `GET /job/{job_id}` - Check processing status
- `GET /download/{filename}` - Download generated files
- `GET /test` - Test service connections
- `GET /info` - Get service information

**Example API usage**:
```bash
# Upload file
curl -X POST "http://localhost:8000/process-file" \
  -F "file=@pitch.mp4" \
  -F "context=Series A pitch"

# Check status
curl "http://localhost:8000/job/{job_id}"

# Download video
curl "http://localhost:8000/download/chad_response_123.mp4" -o output.mp4
```

### Python Library

```python
from chad_workflow import ChadWorkflow

# Initialize
workflow = ChadWorkflow()

# Process audio/video file
results = workflow.process_audio_video_input(
    "pitch_recording.mp4",
    context="Series A startup pitch"
)

# Process text
results = workflow.process_text_input(
    "We're building an AI-powered dog walking app",
    context="Pet tech startup"
)

# Quick roast
results = workflow.quick_roast("NFT marketplace for pets")

print(f"Generated video: {results['video_path']}")
print(f"Generated audio: {results['audio_path']}")
print(f"Hot take: {results['hot_take']}")
```

## Configuration Options

### Voice Settings (ElevenLabs)
- `stability` (0.0-1.0): Voice consistency
- `similarity_boost` (0.0-1.0): Voice similarity to original
- `style` (0.0-1.0): Expressiveness and emotion

### File Settings
- `MAX_FILE_SIZE_MB`: Maximum upload file size
- `TEMP_DIR`: Temporary files directory
- `OUTPUT_DIR`: Generated files directory

## API Keys Setup

### OpenAI
1. Go to [OpenAI API](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add to `.env` as `OPENAI_API_KEY`

### ElevenLabs
1. Go to [ElevenLabs](https://elevenlabs.io/)
2. Sign up and get API key from Profile → API Keys
3. Choose a voice ID from the voice library
4. Add both to `.env`

### HeyGen
1. Go to [HeyGen](https://www.heygen.com/)
2. Sign up for API access
3. Get API key and avatar ID
4. Add both to `.env`

## Chad Goldstein Character

Chad is a flamboyant, self-congratulatory venture capitalist who delivers pitch critiques with:

- **Ruthless candor** mixed with **tech-bro energy**
- **Misguided self-comparisons** to Warren Buffett
- **Colorful analogies** and **venture bro catchphrases**
- **Format**: Opening quip → Highlights → Roast → Verdict

Example catchphrases:
- "Let's deploy some capital, baby!"
- "This smells like pre-seed with a side of froth"
- "Your moat? More like a kiddie pool"
- "I've seen more traction on a stationary bike at Equinox"

## File Structure

```
digital-twin/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.py                # Configuration management
├── chadprompt.txt           # Chad's personality prompt
├── audio_processor.py       # Audio/video → transcript
├── gpt_generator.py         # GPT hot take generation
├── voice_generator.py       # ElevenLabs TTS
├── video_generator.py       # HeyGen avatar videos
├── chad_workflow.py         # Main workflow orchestrator
├── cli.py                   # Command-line interface
├── web_api.py              # FastAPI web interface
├── temp/                   # Temporary files
└── output/                 # Generated files
```

## Troubleshooting

**API Connection Issues**:
```bash
python cli.py --test
```

**File Size Issues**:
- Increase `MAX_FILE_SIZE_MB` in config
- Use compressed audio/video formats

**Voice Quality**:
- Adjust `voice_stability`, `voice_similarity`, `voice_style`
- Try different ElevenLabs voice IDs

**Video Generation Slow**:
- HeyGen processing can take 2-10 minutes
- Use the API's job status endpoint to monitor progress

**Cleanup Old Files**:
```bash
python cli.py --cleanup
```

## Development

**Run tests**:
```bash
python -m pytest
```

**Start development API**:
```bash
uvicorn web_api:app --reload --host 0.0.0.0 --port 8000
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request
