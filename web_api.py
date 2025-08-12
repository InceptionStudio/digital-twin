"""
Digital Twin Web API
FastAPI web interface for generating hot take responses via audio and video with multiple personas.
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import tempfile
import os
import uuid
import asyncio
from pathlib import Path
import logging
from datetime import datetime, timedelta

from chad_workflow import ChadWorkflow
from config import Config
from persona_manager import persona_manager
from job_storage import create_job_storage, RedisJobStorage

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Digital Twin API",
    description="Generate hot take responses from various personas via audio and video",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global workflow instance
workflow: Optional[ChadWorkflow] = None

# Pydantic models
class TextInput(BaseModel):
    text: str
    context: Optional[str] = None
    output_filename: Optional[str] = None
    avatar_id: Optional[str] = None
    voice_settings: Optional[Dict[str, float]] = None
    persona_id: Optional[str] = "chad_goldstein"
    use_heygen_voice: Optional[bool] = False
    heygen_voice_id: Optional[str] = None

class RoastInput(BaseModel):
    topic: str
    output_filename: Optional[str] = None
    avatar_id: Optional[str] = None
    persona_id: Optional[str] = "chad_goldstein"

class GenerateTextInput(BaseModel):
    text: str
    context: Optional[str] = None
    persona_id: Optional[str] = "chad_goldstein"

class GenerateAudioInput(BaseModel):
    text: str
    output_filename: Optional[str] = None
    voice_settings: Optional[Dict[str, float]] = None
    persona_id: Optional[str] = "chad_goldstein"

class GenerateVideoInput(BaseModel):
    text: Optional[str] = None
    audio_path: Optional[str] = None
    output_filename: Optional[str] = None
    avatar_id: Optional[str] = None
    voice_id: Optional[str] = None
    persona_id: Optional[str] = "chad_goldstein"
    use_heygen_voice: Optional[bool] = False

class GeneratePitchInput(BaseModel):
    idea: str  # The pitch idea/context to respond to
    id: List[str]  # List of persona IDs (will use the first one)

class ProcessingStatus(BaseModel):
    job_id: str
    status: str
    progress: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class PersonaInfo(BaseModel):
    id: str
    name: str
    bio: str
    description: Optional[str] = None
    configurations: Dict[str, bool]

# Add new Pydantic models for history
class HistoryItem(BaseModel):
    job_id: str
    created_at: str
    status: str
    persona_id: str
    persona_name: str
    input_text: Optional[str] = None
    input_file: Optional[str] = None
    context: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    step: Optional[str] = None

class HistoryResponse(BaseModel):
    items: List[HistoryItem]
    total: int
    page: int
    per_page: int

# Job storage (shared across workers)
job_storage = None

@app.on_event("startup")
async def startup_event():
    """Initialize the workflow on startup."""
    global workflow, job_storage
    try:
        # Force reload personas to ensure fresh data
        persona_manager.reload_personas()
        
        # Initialize job storage
        storage_type = os.getenv("JOB_STORAGE", "memory")
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        
        # Get worker count from environment or default to 1
        workers = int(os.getenv("WORKERS", "1"))
        
        job_storage = create_job_storage(storage_type, redis_url, workers)
        
        workflow = ChadWorkflow()
        logger.info("Digital Twin Workflow initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Digital Twin Workflow: {str(e)}")
        raise

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Digital Twin API",
        "version": "2.0.0",
        "endpoints": {
            "POST /process-file": "Process audio/video file",
            "POST /process-text": "Process text input",
            "POST /quick-roast": "Generate quick roast",
            "POST /generate-text": "Generate text response only",
            "POST /generate-audio": "Generate audio from text",
            "POST /generate-video": "Generate video from text or audio",
            "GET /personas": "List available personas",
            "GET /personas/{persona_id}": "Get persona details",
            "GET /heygen-voices": "List HeyGen voices",
            "GET /test": "Test service connections",
            "GET /info": "Get service information",
            "GET /job/{job_id}": "Get job status",
            "GET /download/{filename}": "Download generated files",
            "GET /history": "Get history of past queries and results"
        }
    }

@app.get("/personas")
async def list_personas():
    """List all available personas."""
    try:
        personas = persona_manager.list_personas()
        return {
            "personas": personas,
            "count": len(personas)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/personas/{persona_id}")
async def get_persona(persona_id: str):
    """Get detailed information about a specific persona."""
    try:
        persona = persona_manager.get_persona(persona_id)
        if not persona:
            raise HTTPException(status_code=404, detail="Persona not found")
        
        # Validate persona
        validation = persona_manager.validate_persona(persona_id)
        
        return {
            "persona": {
                "id": persona_id,
                "name": persona.name,
                "bio": persona.bio,
                "description": persona.description,
                "files": {
                    "prompt": persona.prompt_file,
                    "image": persona.image_file
                },
                "voice_configuration": {
                    "elevenlabs_voice_id": persona.elevenlabs_voice_id,
                    "heygen_voice_id": persona.heygen_voice_id
                },
                "avatar_configuration": {
                    "heygen_avatar_id": persona.heygen_avatar_id
                },
                "validation": validation
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/heygen-voices")
async def list_heygen_voices():
    """List available HeyGen voices."""
    if not workflow:
        raise HTTPException(status_code=500, detail="Workflow not initialized")
    
    try:
        voices = workflow.video_generator.get_voices()
        return {
            "voices": voices,
            "count": len(voices.get("data", [])) if isinstance(voices, dict) else len(voices)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-text")
async def generate_text(
    background_tasks: BackgroundTasks,
    input_data: GenerateTextInput
):
    """Generate text response only (GPT step)."""
    if not workflow:
        raise HTTPException(status_code=500, detail="Workflow not initialized")
    
    # Validate persona
    persona = persona_manager.get_persona(input_data.persona_id)
    if not persona:
        raise HTTPException(status_code=400, detail=f"Persona '{input_data.persona_id}' not found")
    
    # Create job using shared storage
    job_data = {
        "status": "processing",
        "progress": f"Generating text response with {persona.name}...",
        "persona_id": input_data.persona_id,
        "step": "text_generation",
        "input_text": input_data.text,
        "context": input_data.context
    }
    job_id = job_storage.create_job(job_data)
    
    # Start background processing
    background_tasks.add_task(
        generate_text_background,
        job_id,
        input_data
    )
    
    return {
        "job_id": job_id, 
        "status": "processing", 
        "message": f"Text generation started with {persona.name}",
        "persona": persona.name
    }

async def generate_text_background(job_id: str, input_data: GenerateTextInput):
    """Background task for text generation."""
    try:
        # Run the synchronous workflow in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        
        # Generate hot take using GPT
        hot_take_result = await loop.run_in_executor(
            None,
            workflow.hot_take_generator.generate_hot_take,
            input_data.text, 
            input_data.context, 
            input_data.persona_id
        )
        
        results = {
            "input_text": input_data.text,
            "context": input_data.context,
            "hot_take": hot_take_result["hot_take"],
            "openai_latency": hot_take_result["latency_seconds"],
            "openai_tokens": hot_take_result["total_tokens"],
            "persona_id": input_data.persona_id,
            "step": "text_generation"
        }
        
        job_storage.update_job(job_id, {
            "status": "completed",
            "results": results,
            "progress": "Text generation completed successfully"
        })
        
    except Exception as e:
        job_storage.update_job(job_id, {
            "status": "failed",
            "error": str(e),
            "progress": "Text generation failed"
        })

@app.post("/generate-audio")
async def generate_audio(
    background_tasks: BackgroundTasks,
    input_data: GenerateAudioInput
):
    """Generate audio from text (ElevenLabs step)."""
    if not workflow:
        raise HTTPException(status_code=500, detail="Workflow not initialized")
    
    # Validate persona
    persona = persona_manager.get_persona(input_data.persona_id)
    if not persona:
        raise HTTPException(status_code=400, detail=f"Persona '{input_data.persona_id}' not found")
    
    # Create job using shared storage
    job_data = {
        "status": "processing",
        "progress": f"Generating audio with {persona.name}...",
        "persona_id": input_data.persona_id,
        "step": "audio_generation",
        "input_text": input_data.text
    }
    job_id = job_storage.create_job(job_data)
    
    # Start background processing
    background_tasks.add_task(
        generate_audio_background,
        job_id,
        input_data
    )
    
    return {
        "job_id": job_id, 
        "status": "processing", 
        "message": f"Audio generation started with {persona.name}",
        "persona": persona.name
    }

async def generate_audio_background(job_id: str, input_data: GenerateAudioInput):
    """Background task for audio generation."""
    try:
        # Run the synchronous workflow in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        
        # Get persona's voice ID
        persona = persona_manager.get_persona(input_data.persona_id)
        voice_id = persona.elevenlabs_voice_id if persona else None
        
        # Generate audio filename
        output_filename = input_data.output_filename or f"audio_job_{job_id}"
        audio_filename = f"{output_filename}.mp3"
        
        # Generate audio using ElevenLabs
        audio_path = await loop.run_in_executor(
            None,
            workflow.voice_generator.generate_speech,
            input_data.text,
            audio_filename,
            input_data.voice_settings,
            voice_id
        )
        
        results = {
            "input_text": input_data.text,
            "output_audio": f"/download/{Path(audio_path).name}",
            "voice_id": voice_id,
            "persona_id": input_data.persona_id,
            "step": "audio_generation"
        }
        
        job_storage.update_job(job_id, {
            "status": "completed",
            "results": results,
            "progress": "Audio generation completed successfully"
        })
        
    except Exception as e:
        job_storage.update_job(job_id, {
            "status": "failed",
            "error": str(e),
            "progress": "Audio generation failed"
        })

@app.post("/generate-video")
async def generate_video(
    background_tasks: BackgroundTasks,
    input_data: GenerateVideoInput
):
    """Generate video from text or audio (HeyGen step)."""
    if not workflow:
        raise HTTPException(status_code=500, detail="Workflow not initialized")
    
    # Validate persona
    persona = persona_manager.get_persona(input_data.persona_id)
    if not persona:
        raise HTTPException(status_code=400, detail=f"Persona '{input_data.persona_id}' not found")
    
    # Validate input
    if not input_data.text and not input_data.audio_path:
        raise HTTPException(status_code=400, detail="Either text or audio_path must be provided")
    
    # Create job using shared storage
    job_data = {
        "status": "processing",
        "progress": f"Generating video with {persona.name}...",
        "persona_id": input_data.persona_id,
        "step": "video_generation",
        "input_text": input_data.text,
        "input_audio": input_data.audio_path
    }
    job_id = job_storage.create_job(job_data)
    
    # Start background processing
    background_tasks.add_task(
        generate_video_background,
        job_id,
        input_data
    )
    
    return {
        "job_id": job_id, 
        "status": "processing", 
        "message": f"Video generation started with {persona.name}",
        "persona": persona.name
    }

async def generate_video_background(job_id: str, input_data: GenerateVideoInput):
    """Background task for video generation."""
    try:
        # Run the synchronous workflow in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        
        # Get persona's avatar ID
        persona = persona_manager.get_persona(input_data.persona_id)
        
        # Debug: Print persona details
        print(f"🔍 DEBUG - generate_video_background:")
        print(f"   requested persona_id: {input_data.persona_id}")
        print(f"   persona name: {persona.name if persona else 'None'}")
        print(f"   persona heygen_avatar_id: {persona.heygen_avatar_id if persona else 'None'}")
        print(f"   input_data.avatar_id: {input_data.avatar_id}")
        
        avatar_id = input_data.avatar_id or persona.heygen_avatar_id if persona else None
        print(f"   final avatar_id: {avatar_id}")
        
        # Generate video filename
        output_filename = input_data.output_filename or f"video_job_{job_id}"
        video_filename = f"{output_filename}.mp4"
        
        if input_data.text:
            # Generate video from text
            if input_data.use_heygen_voice:
                # Use HeyGen voice directly
                voice_id = input_data.voice_id or persona.heygen_voice_id if persona else None
                video_path = await loop.run_in_executor(
                    None,
                    workflow.video_generator.generate_complete_video_from_text,
                    input_data.text,
                    video_filename,
                    avatar_id,
                    voice_id,
                    persona.name
                )
            else:
                # Use ElevenLabs voice (need to generate audio first)
                voice_id = persona.elevenlabs_voice_id if persona else None
                audio_filename = f"{output_filename}_temp.mp3"
                
                # Generate audio in thread pool
                audio_path = await loop.run_in_executor(
                    None,
                    workflow.voice_generator.generate_speech,
                    input_data.text,
                    audio_filename,
                    None,
                    voice_id
                )
                
                # Generate video in thread pool
                video_path = await loop.run_in_executor(
                    None,
                    workflow.video_generator.generate_complete_video,
                    audio_path,
                    video_filename,
                    avatar_id,
                    persona.name
                )
        else:
            # Generate video from audio file
            if not os.path.exists(input_data.audio_path):
                raise Exception(f"Audio file not found: {input_data.audio_path}")
            
            video_path = await loop.run_in_executor(
                None,
                workflow.video_generator.generate_complete_video,
                input_data.audio_path,
                video_filename,
                avatar_id,
                persona.name
            )
        
        results = {
            "input_text": input_data.text,
            "output_video": f"/download/{Path(video_path).name}",
            "input_audio": input_data.audio_path,
            "avatar_id": avatar_id,
            "persona_id": input_data.persona_id,
            "step": "video_generation"
        }
        
        job_storage.update_job(job_id, {
            "status": "completed",
            "results": results,
            "progress": "Video generation completed successfully"
        })
        
    except Exception as e:
        job_storage.update_job(job_id, {
            "status": "failed",
            "error": str(e),
            "progress": "Video generation failed"
        })

@app.post("/process-file")
async def process_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    context: Optional[str] = Form(None),
    avatar_id: Optional[str] = Form(None),
    voice_stability: Optional[float] = Form(0.75),
    voice_similarity: Optional[float] = Form(0.75),
    voice_style: Optional[float] = Form(0.8),
    persona_id: Optional[str] = Form("chad_goldstein")
):
    """Process an uploaded audio or video file."""
    if not workflow:
        raise HTTPException(status_code=500, detail="Workflow not initialized")
    
    # Validate persona
    persona = persona_manager.get_persona(persona_id)
    if not persona:
        raise HTTPException(status_code=400, detail=f"Persona '{persona_id}' not found")
    
    # Validate file size
    file_size = 0
    content = await file.read()
    file_size = len(content) / (1024 * 1024)  # MB
    
    if file_size > Config.MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File size ({file_size:.1f}MB) exceeds maximum allowed size ({Config.MAX_FILE_SIZE_MB}MB)"
        )
    
    # Create temporary file
    temp_file = Config.TEMP_DIR / f"upload_{uuid.uuid4()}_{file.filename}"
    
    try:
        with open(temp_file, "wb") as f:
            f.write(content)
        
        # Create job using shared storage
        job_data = {
            "status": "processing",
            "progress": f"File uploaded, starting processing with {persona.name}...",
            "file_path": str(temp_file),
            "persona_id": persona_id,
            "input_file": file.filename,
            "context": context,
            "step": "file_processing"
        }
        job_id = job_storage.create_job(job_data)
        
        # Start background processing
        voice_settings = {
            "stability": voice_stability,
            "similarity_boost": voice_similarity,
            "style": voice_style
        }
        
        background_tasks.add_task(
            process_file_background,
            job_id,
            str(temp_file),
            context,
            avatar_id,
            voice_settings,
            persona_id
        )
        
        return {
            "job_id": job_id, 
            "status": "processing", 
            "message": f"File processing started with {persona.name}",
            "persona": persona.name
        }
        
    except Exception as e:
        # Clean up temp file
        if temp_file.exists():
            temp_file.unlink()
        raise HTTPException(status_code=500, detail=str(e))

async def process_file_background(job_id: str, file_path: str, context: Optional[str],
                                avatar_id: Optional[str], voice_settings: Dict[str, float],
                                persona_id: str):
    """Background task for processing files."""
    try:
        # Run the synchronous workflow in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        
        job_storage.update_job(job_id, {"progress": "Processing audio/video..."})
        
        results = await loop.run_in_executor(
            None,
            workflow.process_audio_video_input,
            file_path,
            context,
            f"job_{job_id}",
            avatar_id,
            voice_settings,
            persona_id
        )

        output_video_path = Path(results['video_path']).name
        results["output_video"] = f"/download/{output_video_path}"
        
        job_storage.update_job(job_id, {
            "status": "completed",
            "results": results,
            "progress": "Processing completed successfully"
        })
        
    except Exception as e:
        job_storage.update_job(job_id, {
            "status": "failed",
            "error": str(e),
            "progress": "Processing failed"
        })
    finally:
        # Clean up temp file
        try:
            os.unlink(file_path)
        except Exception:
            pass

@app.post("/process-text")
async def process_text(
    background_tasks: BackgroundTasks,
    input_data: TextInput
):
    """Process text input to generate hot take."""
    if not workflow:
        raise HTTPException(status_code=500, detail="Workflow not initialized")
    
    # Validate persona
    persona = persona_manager.get_persona(input_data.persona_id)
    if not persona:
        raise HTTPException(status_code=400, detail=f"Persona '{input_data.persona_id}' not found")
    
    # Create job using shared storage
    job_data = {
        "status": "processing",
        "progress": f"Generating hot take from text with {persona.name}...",
        "persona_id": input_data.persona_id,
        "input_text": input_data.text,
        "context": input_data.context,
        "step": "text_processing"
    }
    job_id = job_storage.create_job(job_data)
    
    # Start background processing
    background_tasks.add_task(
        process_text_background,
        job_id,
        input_data
    )
    
    return {
        "job_id": job_id, 
        "status": "processing", 
        "message": f"Text processing started with {persona.name}",
        "persona": persona.name
    }

async def process_text_background(job_id: str, input_data: TextInput):
    """Background task for processing text."""
    try:
        # Run the synchronous workflow in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        
        if input_data.use_heygen_voice:
            # Use HeyGen voice directly
            results = await loop.run_in_executor(
                None,
                workflow.process_text_input_heygen_voice,
                input_data.text,
                input_data.context,
                input_data.output_filename or f"text_job_{job_id}",
                input_data.avatar_id,
                input_data.heygen_voice_id,
                input_data.persona_id
            )
        else:
            # Use ElevenLabs voice
            results = await loop.run_in_executor(
                None,
                workflow.process_text_input,
                input_data.text,
                input_data.context,
                input_data.output_filename or f"text_job_{job_id}",
                input_data.avatar_id,
                input_data.voice_settings,
                input_data.persona_id
            )
        
        output_video_path = Path(results['video_path']).name
        results["output_video"] = f"/download/{output_video_path}"
        
        job_storage.update_job(job_id, {
            "status": "completed",
            "results": results,
            "progress": "Text processing completed successfully"
        })
        
    except Exception as e:
        job_storage.update_job(job_id, {
            "status": "failed",
            "error": str(e),
            "progress": "Text processing failed"
        })

@app.post("/quick-roast")
async def quick_roast(
    background_tasks: BackgroundTasks,
    input_data: RoastInput
):
    """Generate a quick roast on a topic."""
    if not workflow:
        raise HTTPException(status_code=500, detail="Workflow not initialized")
    
    # Validate persona
    persona = persona_manager.get_persona(input_data.persona_id)
    if not persona:
        raise HTTPException(status_code=400, detail=f"Persona '{input_data.persona_id}' not found")
    
    # Create job using shared storage
    job_data = {
        "status": "processing",
        "progress": f"Generating quick roast with {persona.name}...",
        "persona_id": input_data.persona_id,
        "input_text": input_data.topic,
        "step": "quick_roast"
    }
    job_id = job_storage.create_job(job_data)
    
    # Start background processing
    background_tasks.add_task(
        quick_roast_background,
        job_id,
        input_data
    )
    
    return {
        "job_id": job_id, 
        "status": "processing", 
        "message": f"Quick roast generation started with {persona.name}",
        "persona": persona.name
    }

async def quick_roast_background(job_id: str, input_data: RoastInput):
    """Background task for quick roast."""
    try:
        # Run the synchronous workflow in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        
        results = await loop.run_in_executor(
            None,
            workflow.quick_roast,
            input_data.topic,
            input_data.output_filename or f"roast_job_{job_id}",
            input_data.avatar_id,
            input_data.persona_id
        )
        
        output_video_path = Path(results['video_path']).name
        results["output_video"] = f"/download/{output_video_path}"
        
        job_storage.update_job(job_id, {
            "status": "completed",
            "results": results,
            "progress": "Quick roast completed successfully"
        })
        
    except Exception as e:
        job_storage.update_job(job_id, {
            "status": "failed",
            "error": str(e),
            "progress": "Quick roast failed"
        })

@app.post("/generate-pitch")
async def generate_pitch(input_data: GeneratePitchInput):
    """
    Generate a complete pitch response with text, audio, and video outputs.
    Returns all outputs directly without requiring job polling.
    
    Request format:
    {
        "idea": "AI pitch description",
        "id": ["sarah"]  // List of persona IDs, uses first one
    }
    
    Returns:
        Complete response with output_text, output_audio, and output_video
    """
    if not workflow:
        raise HTTPException(status_code=500, detail="Workflow not initialized")
    
    # Get the first persona ID from the list
    if not input_data.id or len(input_data.id) == 0:
        raise HTTPException(status_code=400, detail="No persona ID provided in 'id' field")
    
    persona_id = input_data.id[0]  # Use the first ID from the list
    
    # Validate persona exists and has required configurations
    persona = persona_manager.get_persona(persona_id)
    if not persona:
        raise HTTPException(status_code=400, detail=f"Persona '{persona_id}' not found")
    
    # Validate persona has necessary IDs configured
    if not persona.elevenlabs_voice_id and not persona.heygen_voice_id:
        raise HTTPException(
            status_code=400, 
            detail=f"Persona '{persona_id}' has no voice configuration"
        )
    
    try:
        import time
        start_time = time.time()
        
        # Use job_id internally for file naming
        job_id = str(uuid.uuid4())
        
        logger.info(f"Starting pitch generation for idea: {input_data.idea[:50]}... with persona: {persona_id}")
        
        # Step 1: Generate text (hot take) using the idea as context
        hot_take_result = workflow.hot_take_generator.generate_hot_take(
            input_data.idea,  # The pitch idea to respond to
            context=None,
            persona_id=persona_id
        )
        output_text = hot_take_result["hot_take"]
        
        # Step 2: Generate audio using persona's voice configuration
        timestamp = int(time.time())
        audio_filename = f"pitch_audio_{job_id}_{timestamp}.mp3"
        
        output_audio = workflow.voice_generator.generate_speech(
            output_text,
            audio_filename,
            voice_settings=None,  # Use default settings
            voice_id=persona.elevenlabs_voice_id
        )
        
        # Step 3: Generate video using persona's avatar
        video_filename = f"pitch_video_{job_id}_{timestamp}.mp4"
        
        output_video = workflow.video_generator.generate_complete_video(
            output_audio,
            video_filename,
            talking_photo_id=persona.heygen_avatar_id,
            persona_name=persona.name
        )
        
        # Calculate total time
        total_time = time.time() - start_time
        
        logger.info(f"Pitch generation completed in {total_time:.2f}s")
        
        # Return all outputs directly
        return {
            "output_text": output_text,
            "output_audio": f"/download/{Path(output_audio).name}",
            "output_video": f"/download/{Path(output_video).name}",
            "persona_used": {
                "id": persona_id,
                "name": persona.name
            },
            "processing_details": {
                "text_generation": {
                    "tokens": hot_take_result.get("total_tokens", 0),
                    "latency": hot_take_result.get("latency_seconds", 0)
                },
                "total_processing_time": total_time
            }
        }
        
    except Exception as e:
        logger.error(f"Pitch generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pitch generation failed: {str(e)}")

@app.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of a processing job."""
    if not job_storage:
        raise HTTPException(status_code=500, detail="Job storage not initialized")
    
    job = job_storage.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job

@app.get("/test")
async def test_services():
    """Test all service connections."""
    if not workflow:
        raise HTTPException(status_code=500, detail="Workflow not initialized")
    
    try:
        results = workflow.test_all_services()
        return {
            "status": "success" if all(results.values()) else "partial_failure",
            "services": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/info")
async def get_service_info():
    """Get information about available services."""
    if not workflow:
        raise HTTPException(status_code=500, detail="Workflow not initialized")
    
    try:
        return workflow.get_service_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download a generated file."""
    file_path = Config.OUTPUT_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine media type
    if filename.endswith('.mp4'):
        media_type = "video/mp4"
    elif filename.endswith('.mp3'):
        media_type = "audio/mpeg"
    else:
        media_type = "application/octet-stream"
    
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename
    )

@app.get("/stream/{filename}")
async def stream_file(filename: str):
    """Stream a video/audio file for playback."""
    file_path = Config.OUTPUT_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine media type
    if filename.endswith('.mp4'):
        media_type = "video/mp4"
    elif filename.endswith('.mp3'):
        media_type = "audio/mpeg"
    else:
        media_type = "application/octet-stream"
    
    return FileResponse(
        path=str(file_path),
        media_type=media_type
        # No filename parameter = no download, browser will play it
    )

@app.post("/cleanup")
async def cleanup_files():
    """Clean up temporary and old files."""
    if not workflow:
        raise HTTPException(status_code=500, detail="Workflow not initialized")
    
    try:
        workflow.cleanup_files()
        return {"message": "Cleanup completed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "workflow_initialized": workflow is not None,
        "available_personas": len(persona_manager.list_personas())
    }

@app.get("/healthz")
async def healthz():
    """Simple health check endpoint for container orchestration."""
    return {"status": "ok"}

@app.get("/history", response_model=HistoryResponse)
async def get_history(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    persona_id: Optional[str] = Query(None, description="Filter by persona ID"),
    status: Optional[str] = Query(None, description="Filter by status (completed, failed, pending)"),
    days: Optional[int] = Query(7, ge=1, le=365, description="Number of days to look back")
):
    """Get history of past queries and results."""
    try:
        # Get all jobs from storage
        all_jobs = []
        
        if isinstance(job_storage, RedisJobStorage):
            # For Redis, we need to get all job IDs first
            job_ids = job_storage.redis.smembers("jobs:active")
            for job_id in job_ids:
                job_data = job_storage.get_job(job_id)
                if job_data:
                    all_jobs.append(job_data)
        else:
            # For in-memory storage, get all jobs
            all_jobs = list(job_storage.jobs.values())
        
        # Filter jobs based on criteria
        filtered_jobs = []
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        for job in all_jobs:
            # Filter by date
            created_at = datetime.fromisoformat(job.get("created_at", "1970-01-01T00:00:00"))
            if created_at < cutoff_date:
                continue
                
            # Filter by persona
            if persona_id and job.get("persona_id") != persona_id:
                continue
                
            # Filter by status
            if status and job.get("status") != status:
                continue
                
            filtered_jobs.append(job)
        
        # Sort by creation date (newest first)
        filtered_jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # Paginate
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_jobs = filtered_jobs[start_idx:end_idx]
        
        # Convert to HistoryItem format
        history_items = []
        for job in paginated_jobs:
            # Get persona name
            persona = persona_manager.get_persona(job.get("persona_id", ""))
            persona_name = persona.name if persona else "Unknown"
            
            # Extract input text from results or job data
            input_text = None
            if job.get("results", {}).get("input_text"):
                input_text = job["results"]["input_text"]
            elif job.get("input_text"):
                input_text = job["input_text"]
            
            history_item = HistoryItem(
                job_id=job.get("id", ""),
                created_at=job.get("created_at", ""),
                status=job.get("status", ""),
                persona_id=job.get("persona_id", ""),
                persona_name=persona_name,
                input_text=input_text,
                input_file=job.get("input_file"),
                context=job.get("context"),
                results=job.get("results"),
                error=job.get("error"),
                step=job.get("step")
            )
            history_items.append(history_item)
        
        return HistoryResponse(
            items=history_items,
            total=len(filtered_jobs),
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Error retrieving history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=4)
