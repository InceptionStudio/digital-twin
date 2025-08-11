# Web API Workflow Documentation

## Overview

The Digital Twin Web API provides a RESTful interface for generating AI-powered hot take videos through multiple personas. The API is built with FastAPI and orchestrates a complex workflow involving speech-to-text, AI text generation, text-to-speech, and video generation.

## Architecture Flow

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│   Client    │────▶│   Web API    │────▶│ Chad Workflow │────▶│   Services   │
│  (Request)  │     │  (FastAPI)   │     │ (Orchestrator)│     │ (AI/Video)   │
└─────────────┘     └──────────────┘     └───────────────┘     └──────────────┘
                            │                      │                     │
                            ▼                      ▼                     ▼
                    ┌──────────────┐     ┌───────────────┐    ┌──────────────┐
                    │ Job Manager  │     │    Persona    │    │   OpenAI     │
                    │   (Async)    │     │   Manager     │    │  ElevenLabs  │
                    └──────────────┘     └───────────────┘    │   HeyGen     │
                                                                └──────────────┘
```

## Core Components

### 1. Web API Layer (`web_api.py`)
- **Purpose**: HTTP interface for client requests
- **Responsibilities**:
  - Request validation
  - File upload handling
  - Job management (async processing)
  - Response formatting
  - Error handling

### 2. Chad Workflow Layer (`chad_workflow.py`)
- **Purpose**: Orchestrates the complete processing pipeline
- **Responsibilities**:
  - Step coordination
  - Service integration
  - Result aggregation
  - Error propagation

### 3. Service Layers
- **AudioProcessor**: Transcribes audio/video to text
- **HotTakeGenerator**: Generates AI responses using GPT
- **VoiceGenerator**: Creates audio using ElevenLabs
- **VideoGenerator**: Produces videos using HeyGen

## Endpoint Workflows

### Complete Workflows

#### 1. `/process-file` - Audio/Video File Processing

**Flow:**
```
1. Client uploads audio/video file
2. API validates file and creates async job
3. Background task starts:
   a. AudioProcessor transcribes audio → text
   b. HotTakeGenerator creates hot take from transcript
   c. VoiceGenerator synthesizes speech (ElevenLabs)
   d. VideoGenerator creates avatar video (HeyGen)
4. Results stored with job ID
5. Client polls /job/{job_id} for status
6. Downloads final video from /download/{filename}
```

**Request:**
```python
POST /process-file
Content-Type: multipart/form-data
{
    "file": <binary>,
    "context": "optional context",
    "persona_id": "chad_goldstein"
}
```

**Internal Workflow:**
```python
# In web_api.py
@app.post("/process-file")
async def process_file_endpoint():
    # 1. Save uploaded file
    file_path = save_upload(file)
    
    # 2. Create background job
    job_id = create_job()
    background_tasks.add_task(
        process_file_job,
        job_id, file_path, context, persona_id
    )
    
    # 3. Return job ID immediately
    return {"job_id": job_id}

# Background job execution
def process_file_job(job_id, file_path, context, persona_id):
    workflow = ChadWorkflow()
    results = workflow.process_audio_video_input(
        file_path, 
        context=context,
        persona_id=persona_id
    )
    # Store results in shared job storage
    job_storage.update_job(job_id, {
        "status": "completed",
        "results": results,
        "progress": "Processing completed successfully"
    })
```

#### 2. `/process-text` - Text Input Processing

**Flow:**
```
1. Client sends text input
2. API creates async job
3. Background task:
   a. HotTakeGenerator creates response
   b. VoiceGenerator synthesizes speech
   c. VideoGenerator creates avatar video
4. Results available via job ID
```

**Request:**
```python
POST /process-text
{
    "text": "Startup pitch text",
    "context": "Series A pitch",
    "persona_id": "sarah_guo"
}
```

**Internal Workflow:**
```python
def process_text_job(job_id, text, context, persona_id):
    workflow = ChadWorkflow()
    
    # Step 1: Generate hot take
    hot_take = workflow.hot_take_generator.generate_hot_take(
        text, context, persona_id
    )
    
    # Step 2: Generate voice
    audio_path = workflow.voice_generator.generate_speech(
        hot_take["hot_take"],
        voice_id=persona.elevenlabs_voice_id
    )
    
    # Step 3: Generate video
    video_path = workflow.video_generator.generate_complete_video(
        audio_path,
        avatar_id=persona.heygen_avatar_id
    )
```

### Individual Step Endpoints

#### 3. `/generate-text` - Text Generation Only

**Flow:**
```
1. Receive text input
2. Load persona prompt
3. Call GPT API with persona context
4. Return generated text immediately
```

**Synchronous Processing:**
```python
@app.post("/generate-text")
async def generate_text_endpoint(request: GenerateTextRequest):
    # Direct processing - no background job
    generator = HotTakeGenerator()
    result = generator.generate_hot_take(
        request.text,
        request.context,
        request.persona_id
    )
    return {
        "hot_take": result["hot_take"],
        "tokens": result["total_tokens"],
        "latency": result["latency_seconds"]
    }
```

#### 4. `/generate-audio` - Audio Generation

**Flow:**
```
1. Receive text input
2. Get persona voice settings
3. Call ElevenLabs API
4. Stream audio generation
5. Save and return audio file
```

**Processing:**
```python
@app.post("/generate-audio")
async def generate_audio_endpoint(request: GenerateAudioRequest):
    voice_gen = VoiceGenerator()
    
    # Get persona voice configuration
    persona = persona_manager.get_persona(request.persona_id)
    voice_id = persona.elevenlabs_voice_id
    
    # Generate audio
    audio_path = voice_gen.generate_speech_streaming(
        request.text,
        voice_id=voice_id,
        voice_settings=request.voice_settings
    )
    
    return FileResponse(audio_path)
```

#### 5. `/generate-video` - Video Generation

**Flow:**
```
Two modes of operation:

**Mode A: From Audio File**
1. Receive audio file
2. Upload to HeyGen
3. Generate avatar video
4. Poll for completion
5. Download and return

**Mode B: From Text (HeyGen Voice)**
1. Receive text input
2. Use HeyGen's text-to-speech
3. Generate avatar video with voice
4. Return completed video
```

**Processing:**
```python
@app.post("/generate-video")
async def generate_video_endpoint(request: GenerateVideoRequest):
    video_gen = VideoGenerator()
    
    if request.use_heygen_voice:
        # Direct text-to-video with HeyGen voice
        video_path = video_gen.generate_complete_video_from_text(
            request.text,
            avatar_id=persona.heygen_avatar_id,
            voice_id=persona.heygen_voice_id
        )
    else:
        # From audio file
        video_path = video_gen.generate_complete_video(
            request.audio_path,
            avatar_id=persona.heygen_avatar_id
        )
    
    return FileResponse(video_path)
```

## Persona Integration

### Persona Loading Flow

```python
# On API startup
persona_manager = PersonaManager()  # Loads from personas/personas.json

# When processing request
def process_with_persona(text, persona_id):
    # 1. Get persona configuration
    persona = persona_manager.get_persona(persona_id)
    
    # 2. Load persona prompt
    prompt_content = persona_manager.get_prompt_content(persona_id)
    
    # 3. Use persona settings
    voice_id = persona.elevenlabs_voice_id
    avatar_id = persona.heygen_avatar_id
    
    # 4. Generate with persona context
    return generate_response(text, prompt_content, voice_id, avatar_id)
```

### Persona Configuration Structure

```json
{
  "chad_goldstein": {
    "name": "Chad Goldstein",
    "bio": "Flamboyant VC...",
    "prompt_file": "personas/prompts/chad_goldstein.txt",
    "elevenlabs_voice_id": "voice_id_here",
    "heygen_avatar_id": "avatar_id_here",
    "heygen_voice_id": "heygen_voice_id"
  }
}
```

## Async Job Management

### Job Lifecycle

```
Created → Processing → Completed/Failed
   │           │            │
   └───────────┴────────────┴──→ Cleanup (after TTL)
```

### Job Status Tracking

```python
# Shared job storage (Redis for production, in-memory for development)
from job_storage import create_job_storage

# Initialize job storage based on configuration
job_storage = create_job_storage(
    storage_type=os.getenv("JOB_STORAGE", "memory"),
    redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
    workers=int(os.getenv("WORKERS", "1"))
)

def create_job(job_data):
    """Create a new job and return its ID"""
    return job_storage.create_job(job_data)

def update_job(job_id, updates):
    """Update job with new data"""
    return job_storage.update_job(job_id, updates)

def get_job(job_id):
    """Retrieve job by ID"""
    return job_storage.get_job(job_id)
```

**Job Storage Types:**
- **In-memory**: Single worker development
- **Redis**: Multi-worker production (required for workers > 1)

## Error Handling

### Error Propagation Chain

```
Service Error → Workflow Exception → API Error Response → Client
```

### Common Error Scenarios

1. **File Upload Errors**
   - File too large → 413 Payload Too Large
   - Invalid format → 400 Bad Request

2. **Processing Errors**
   - API key invalid → 401 Unauthorized
   - Service timeout → 504 Gateway Timeout
   - Generation failed → 500 Internal Server Error

3. **Resource Errors**
   - Job not found → 404 Not Found
   - File not found → 404 Not Found
   - Job storage not initialized → 500 Internal Server Error

4. **Job Storage Errors**
   - Redis connection failed → 500 Internal Server Error
   - In-memory storage with multiple workers → 500 Internal Server Error
   - Job storage not available → 500 Internal Server Error

## Performance Optimizations

### 1. Streaming Audio Generation
```python
# Instead of waiting for complete audio
voice_gen.generate_speech_streaming(text)  # Streams chunks
```

### 2. Parallel Processing
```python
# When possible, run independent tasks concurrently
async def parallel_generation():
    audio_task = asyncio.create_task(generate_audio())
    metadata_task = asyncio.create_task(prepare_metadata())
    
    audio, metadata = await asyncio.gather(audio_task, metadata_task)
```

### 3. File Caching
```python
# Temporary files are cached for quick access
TEMP_DIR = "./temp"
OUTPUT_DIR = "./output"

# Files are cleaned up periodically
cleanup_old_files(max_age_hours=24)
```

### 4. Shared Job Storage
```python
# Redis-based job storage enables:
# - Multiple worker processes
# - Job persistence across restarts
# - Distributed job tracking
# - Automatic cleanup of old jobs

job_storage.cleanup_old_jobs(max_age_hours=24)
```

## Application Startup

### Startup Sequence
```python
@app.on_event("startup")
async def startup_event():
    """Initialize the workflow on startup."""
    global workflow, job_storage
    
    # 1. Reload personas
    persona_manager.reload_personas()
    
    # 2. Initialize job storage
    storage_type = os.getenv("JOB_STORAGE", "memory")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    workers = int(os.getenv("WORKERS", "1"))
    
    job_storage = create_job_storage(storage_type, redis_url, workers)
    
    # 3. Initialize workflow
    workflow = ChadWorkflow()
```

### Startup Validation
- Persona configuration loading
- Job storage connection test
- Workflow component initialization
- Service API key validation

## Service Integration Details

### OpenAI Integration
- **Endpoint**: GPT-4/GPT-5 API
- **Purpose**: Generate hot takes with persona context
- **Timeout**: 30 seconds
- **Retry**: 3 attempts with exponential backoff

### ElevenLabs Integration
- **Endpoint**: Text-to-Speech API
- **Purpose**: Generate natural voice audio
- **Streaming**: Supported for faster response
- **Voice Cloning**: Available with specific voice IDs

### HeyGen Integration
- **Endpoint**: Avatar API v2
- **Purpose**: Generate talking avatar videos
- **Processing**: Async with polling (2-10 minutes)
- **Formats**: MP4 output, various avatar styles

## Job Storage Configuration

### Environment Variables
```bash
# Job storage type (memory or redis)
JOB_STORAGE=redis

# Redis connection URL (required when JOB_STORAGE=redis)
REDIS_URL=redis://localhost:6379

# Number of workers (affects storage requirements)
WORKERS=4
```

### Storage Requirements
- **Single Worker**: In-memory storage is sufficient
- **Multiple Workers**: Redis is required for shared job state
- **Production**: Always use Redis for reliability and scalability

### Redis Setup
```bash
# Option 1: Docker
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Option 2: Homebrew (macOS)
brew install redis
redis-server

# Option 3: Docker Compose (includes Redis)
docker-compose up
```

### Job Storage Safety
The system includes safety checks to prevent in-memory storage with multiple workers:
```python
# This will raise an error if workers > 1 and storage_type = "memory"
job_storage = create_job_storage("memory", workers=4)
# ValueError: Cannot use in-memory job storage with 4 workers
```

## Docker Deployment

### Hot Reload Configuration
```yaml
# compose.yaml
services:
  web-api:
    volumes:
      - .:/app  # Mount source for hot reload
    command: ["uvicorn", "web_api:app", "--reload"]
```

### Environment Variables
```bash
OPENAI_API_KEY=xxx
ELEVENLABS_API_KEY=xxx
HEYGEN_API_KEY=xxx
HUGGINGFACE_TOKEN=xxx
```

## Testing Workflows

### Test Service Connections
```bash
curl http://localhost:8000/test
```

### Test Complete Workflow
```bash
# 1. Submit job
JOB_ID=$(curl -X POST http://localhost:8000/process-text \
  -H "Content-Type: application/json" \
  -d '{"text": "test pitch"}' | jq -r '.job_id')

# 2. Check status
curl http://localhost:8000/job/$JOB_ID

# 3. Download result
curl http://localhost:8000/download/output.mp4 -o result.mp4
```

## Monitoring and Debugging

### Health Check Endpoint
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "openai": test_openai_connection(),
            "elevenlabs": test_elevenlabs_connection(),
            "heygen": test_heygen_connection()
        }
    }
```

### Debug Logging
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Throughout workflow
logger.info(f"Starting video generation for persona: {persona_id}")
logger.error(f"Failed to generate audio: {str(e)}")
```

## Best Practices

1. **Always use personas** - Ensures consistent character voice
2. **Handle async properly** - Use job IDs for long operations
3. **Validate inputs early** - Check file sizes, formats before processing
4. **Clean up resources** - Remove temporary files after processing
5. **Monitor API limits** - Track usage for external services
6. **Cache when possible** - Reuse generated content when appropriate
7. **Log extensively** - Track all steps for debugging
8. **Fail gracefully** - Return meaningful error messages

## Common Integration Patterns

### Pattern 1: Full Pipeline
```
Input → Transcribe → Generate → Voice → Video → Output
```

### Pattern 2: Text-Only Quick Response
```
Input → Generate → Output (JSON)
```

### Pattern 3: Voice-First Generation
```
Text → Voice → Video → Output
```

### Pattern 4: Direct Video Generation
```
Text → HeyGen (Voice + Video) → Output
```

## Future Enhancements

1. **WebSocket Support** - Real-time status updates
2. **Batch Processing** - Multiple inputs in single job
3. **Caching Layer** - Redis for job management
4. **Queue System** - Celery for distributed processing
5. **Metrics Collection** - Prometheus integration
6. **Rate Limiting** - Per-user/API key limits
7. **Webhook Callbacks** - Notify on job completion