# Digital Twin API

A complete workflow system that generates personalized hot take responses from various personas using AI-powered audio and video processing.

## Features

🎬 **Audio/Video Processing**: Convert speech to text using OpenAI Whisper
💬 **AI Hot Takes**: Generate responses using GPT-5 with customizable personas
🎵 **Voice Synthesis**: Convert text to speech using ElevenLabs or HeyGen
🎥 **Avatar Videos**: Create talking avatar videos using HeyGen
👥 **Multi-Persona Support**: Switch between different character personalities
🔧 **Modular Workflow**: Process each step independently or as complete workflows

## Available Personas

- **Chad Goldstein**: Flamboyant venture capitalist with tech-bro energy
- **Sarah Guo**: Analytical VC from Conviction with sharp insights
- **Sarah Chen**: Tech journalist with industry expertise
- **Custom Personas**: Create your own with unique prompts and voices

## Workflow

```
Audio/Video Input → Transcript → Hot Take → Voice → Avatar Video
```

**Or process steps independently:**
- `POST /generate-text` - GPT text generation only
- `POST /generate-audio` - ElevenLabs audio generation from text
- `POST /generate-video` - HeyGen video generation from text or audio

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

# HuggingFace Token (for audio diarization)
HUGGINGFACE_TOKEN=your_huggingface_token_here

# Application Configuration (optional)
MAX_FILE_SIZE_MB=50
TEMP_DIR=./temp
OUTPUT_DIR=./output
```

## Usage

### Command Line Interface

**Process audio/video file with specific persona**:
```bash
python cli.py --file "pitch_recording.mp4" --context "Series A startup pitch" --persona sarah_guo
```

**Process text input with persona**:
```bash
python cli.py --text "We're building an AI-powered dog walking app" --context "Pet tech startup" --persona chad_goldstein
```

**Generate quick roast with persona**:
```bash
python cli.py --roast "NFT marketplace for pets" --persona sarah_guo
```

**Use HeyGen voice directly**:
```bash
python cli.py --persona sarah_guo --heygen-voice --text "Your startup pitch here"
```

**List available personas**:
```bash
python cli.py --list-personas
```

**Show persona details**:
```bash
python cli.py --show-persona chad_goldstein
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

**Complete Workflows:**
- `POST /process-file` - Upload audio/video file
- `POST /process-text` - Process text input  
- `POST /quick-roast` - Generate quick roast

**Individual Steps:**
- `POST /generate-text` - Generate text response only
- `POST /generate-audio` - Generate audio from text
- `POST /generate-video` - Generate video from text or audio

**Persona Management:**
- `GET /personas` - List available personas
- `GET /personas/{persona_id}` - Get persona details
- `GET /heygen-voices` - List HeyGen voices

**System:**
- `GET /job/{job_id}` - Check processing status
- `GET /download/{filename}` - Download generated files
- `GET /test` - Test service connections
- `GET /info` - Get service information

**Example API usage**:
```bash
# Process text with specific persona
curl -X POST "http://localhost:8000/process-text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "We are building an AI startup",
    "context": "Demo day pitch",
    "persona_id": "sarah_guo"
  }'

# Generate text only
curl -X POST "http://localhost:8000/generate-text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "We are building an AI startup",
    "persona_id": "chad_goldstein"
  }'

# Generate video with HeyGen voice
curl -X POST "http://localhost:8000/generate-video" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world",
    "persona_id": "sarah_guo",
    "use_heygen_voice": true
  }'

# List personas
curl "http://localhost:8000/personas"

# Check job status
curl "http://localhost:8000/job/{job_id}"
```

### Python Library

```python
from chad_workflow import ChadWorkflow

# Initialize
workflow = ChadWorkflow()

# Process audio/video file with persona
results = workflow.process_audio_video_input(
    "pitch_recording.mp4",
    context="Series A startup pitch",
    persona_id="sarah_guo"
)

# Process text with persona
results = workflow.process_text_input(
    "We're building an AI-powered dog walking app",
    context="Pet tech startup",
    persona_id="chad_goldstein"
)

# Quick roast with persona
results = workflow.quick_roast(
    "NFT marketplace for pets",
    persona_id="sarah_guo"
)

print(f"Generated video: {results['video_path']}")
print(f"Generated audio: {results['audio_path']}")
print(f"Hot take: {results['hot_take']}")
```

## Persona Management

### List Personas
```bash
python persona_cli.py list
```

### Add New Persona
```bash
python persona_cli.py add
```

### Show Persona Details
```bash
python persona_cli.py show chad_goldstein
```

### Update Persona
```bash
python persona_cli.py update chad_goldstein
```

### Delete Persona
```bash
python persona_cli.py delete chad_goldstein
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

### HuggingFace (for audio diarization)
1. Go to [HuggingFace](https://huggingface.co/settings/tokens)
2. Create a new token
3. Add to `.env` as `HUGGINGFACE_TOKEN`

## Default Personas

### Chad Goldstein
A flamboyant, self-congratulatory venture capitalist who delivers pitch critiques with:
- **Ruthless candor** mixed with **tech-bro energy**
- **Misguided self-comparisons** to Warren Buffett
- **Colorful analogies** and **venture bro catchphrases**

### Sarah Guo
Founder of Conviction, early-stage AI investor with:
- **Deep technical expertise** and **thoughtful analysis**
- **Strategic insights** in the technology sector
- **Sharp, incisive commentary** with **dry wit**

### Sarah Chen
Tech journalist with:
- **Industry expertise** and **analytical perspective**
- **Professional insights** on technology trends
- **Balanced commentary** on startup pitches

## File Structure

```
digital-twin/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.py                # Configuration management
├── audio_processor.py       # Audio/video → transcript
├── gpt_generator.py         # GPT hot take generation
├── voice_generator.py       # ElevenLabs TTS
├── video_generator.py       # HeyGen avatar videos
├── chad_workflow.py         # Main workflow orchestrator
├── cli.py                   # Command-line interface
├── web_api.py              # FastAPI web interface
├── persona_manager.py       # Persona management system
├── persona_cli.py          # Persona CLI interface
├── audio_diarizer.py       # Audio speaker separation
├── personas/               # Persona configurations
│   ├── personas.json       # Persona database
│   └── prompts/           # Persona prompt files
│       ├── chad_goldstein.txt
│       └── sarah_guo.txt
├── temp/                   # Temporary files
└── output/                 # Generated files
```

## Audio Diarization

Separate multiple speakers in audio files:

```bash
python audio_diarizer.py --file "meeting_recording.mp3" --diarizer pyannote
python audio_diarizer.py --file "meeting_recording.mp3" --diarizer simple --num-speakers 3
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
- Use HeyGen voices for direct text-to-video

**Video Generation Slow**:
- HeyGen processing can take 2-10 minutes
- Use the API's job status endpoint to monitor progress

**Persona Issues**:
```bash
python persona_cli.py validate chad_goldstein
```

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

**Add example personas**:
```bash
python example_personas.py
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request
