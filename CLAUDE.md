# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Running the Application

**Start Web API (Development with hot reload):**
```bash
python web_api.py
# or
uvicorn web_api:app --reload --host 0.0.0.0 --port 8000
```

**Docker with hot reload:**
```bash
docker-compose up --build
```

**CLI Usage:**
```bash
# Process file with persona
python cli.py --file "pitch.mp4" --context "Demo day" --persona sarah_guo

# Quick roast
python cli.py --roast "NFT for pets" --persona chad_goldstein

# Test services
python cli.py --test
```

### Testing & Validation

```bash
# Test API connections
python cli.py --test

# Validate persona configuration
python persona_cli.py validate chad_goldstein

# Check API health
curl http://localhost:8000/health
```

## Architecture Overview

### Core Workflow Pipeline

The application follows a modular pipeline architecture:

```
Input (Audio/Video/Text) → Transcription → AI Generation → Voice Synthesis → Video Generation
```

**Key Components:**
- `chad_workflow.py` - Main orchestrator that coordinates all services
- `web_api.py` - FastAPI interface with async job management
- `persona_manager.py` - Manages multiple AI personas with unique voices/avatars
- Service modules: `audio_processor.py`, `gpt_generator.py`, `voice_generator.py`, `video_generator.py`

### Persona System

Personas are stored in `personas/personas.json` with prompts in `personas/prompts/`. Each persona has:
- Custom prompt file for personality
- ElevenLabs voice ID for TTS
- HeyGen avatar and voice IDs for video generation
- Bio and description metadata

When modifying personas:
1. Update `personas/personas.json` for configuration
2. Place prompt files in `personas/prompts/`
3. Use `persona_manager.reload_personas()` if needed

### Service Integration

**External APIs Used:**
- OpenAI GPT-4/5 for text generation
- ElevenLabs for voice synthesis
- HeyGen for avatar video generation

All API keys are configured in `.env` file.

### Async Job Processing

The web API uses background tasks for long-running operations:
1. Client submits request → receives job_id
2. Background task processes workflow
3. Client polls `/job/{job_id}` for status
4. Downloads results from `/download/{filename}`

Jobs are stored in-memory (consider Redis for production).

## Important Implementation Notes

### Error Handling
- All workflow methods include try/catch with detailed logging
- Service failures propagate up with meaningful error messages
- API returns appropriate HTTP status codes

### File Management
- Temporary files in `./temp` directory
- Output files in `./output` directory
- Automatic cleanup of old files available

### Hot Reloading
- Docker setup includes volume mounts for code changes
- Uvicorn runs with `--reload` flag in development
- Changes to Python files automatically restart the server

### Debugging
- Debugpy available on port 5678 when using Docker
- Extensive logging throughout the workflow
- Service test endpoints available at `/test`

## Key Files to Understand

1. **chad_workflow.py**: Contains `ChadWorkflow` class with methods:
   - `process_audio_video_input()` - Full pipeline from audio/video
   - `process_text_input()` - Pipeline from text input
   - `process_text_input_heygen_voice()` - Uses HeyGen's voice instead of ElevenLabs
   - `quick_roast()` - Shortened workflow for quick responses

2. **web_api.py**: FastAPI routes including:
   - Complete workflows: `/process-file`, `/process-text`, `/quick-roast`
   - Individual steps: `/generate-text`, `/generate-audio`, `/generate-video`
   - Persona management: `/personas`, `/personas/{persona_id}`

3. **persona_manager.py**: PersonaManager class handles:
   - Loading/saving persona configurations
   - Validating persona settings
   - Getting prompt content for generation

## Common Tasks

### Adding a New Persona
```python
python persona_cli.py add
# or programmatically:
from persona_manager import Persona, persona_manager
new_persona = Persona(name="...", bio="...", prompt_file="...")
persona_manager.add_persona("persona_id", new_persona)
```

### Modifying Workflow Steps
Each step in the workflow can be run independently through the API:
- Text generation only: POST `/generate-text`
- Audio generation only: POST `/generate-audio`
- Video generation only: POST `/generate-video`

### Switching Between Voices
- For ElevenLabs: Set `elevenlabs_voice_id` in persona config
- For HeyGen: Set `heygen_voice_id` and use `use_heygen_voice=true` in API calls