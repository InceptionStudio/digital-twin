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
from pathlib import Path
import logging

from chad_workflow import ChadWorkflow
from config import Config
from persona_manager import persona_manager

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

# In-memory job storage (use Redis or database in production)
jobs: Dict[str, Dict[str, Any]] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize the workflow on startup."""
    global workflow
    try:
        # Force reload personas to ensure fresh data
        persona_manager.reload_personas()
        
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
            "GET /download/{filename}": "Download generated files"
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
    
    job_id = str(uuid.uuid4())
    
    # Initialize job
    jobs[job_id] = {
        "status": "processing",
        "progress": f"Generating text response with {persona.name}...",
        "persona_id": input_data.persona_id,
        "step": "text_generation"
    }
    
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
        # Generate hot take using GPT
        hot_take_result = workflow.hot_take_generator.generate_hot_take(
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
        
        jobs[job_id].update({
            "status": "completed",
            "results": results,
            "progress": "Text generation completed successfully"
        })
        
    except Exception as e:
        jobs[job_id].update({
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
    
    job_id = str(uuid.uuid4())
    
    # Initialize job
    jobs[job_id] = {
        "status": "processing",
        "progress": f"Generating audio with {persona.name}...",
        "persona_id": input_data.persona_id,
        "step": "audio_generation"
    }
    
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
        # Get persona's voice ID
        persona = persona_manager.get_persona(input_data.persona_id)
        voice_id = persona.elevenlabs_voice_id if persona else None
        
        # Generate audio filename
        output_filename = input_data.output_filename or f"audio_job_{job_id}"
        audio_filename = f"{output_filename}.mp3"
        
        # Generate audio using ElevenLabs
        audio_path = workflow.voice_generator.generate_speech(
            input_data.text,
            audio_filename,
            input_data.voice_settings,
            voice_id
        )
        
        results = {
            "input_text": input_data.text,
            "audio_path": audio_path,
            "voice_id": voice_id,
            "persona_id": input_data.persona_id,
            "step": "audio_generation"
        }
        
        jobs[job_id].update({
            "status": "completed",
            "results": results,
            "progress": "Audio generation completed successfully"
        })
        
    except Exception as e:
        jobs[job_id].update({
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
    
    job_id = str(uuid.uuid4())
    
    # Initialize job
    jobs[job_id] = {
        "status": "processing",
        "progress": f"Generating video with {persona.name}...",
        "persona_id": input_data.persona_id,
        "step": "video_generation"
    }
    
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
                video_path = workflow.video_generator.generate_complete_video_from_text(
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
                audio_path = workflow.voice_generator.generate_speech(
                    input_data.text,
                    audio_filename,
                    None,
                    voice_id
                )
                video_path = workflow.video_generator.generate_complete_video(
                    audio_path,
                    video_filename,
                    avatar_id,
                    persona.name
                )
        else:
            # Generate video from audio file
            if not os.path.exists(input_data.audio_path):
                raise Exception(f"Audio file not found: {input_data.audio_path}")
            
            video_path = workflow.video_generator.generate_complete_video(
                input_data.audio_path,
                video_filename,
                avatar_id,
                persona.name
            )
        
        results = {
            "input_text": input_data.text,
            "input_audio": input_data.audio_path,
            "video_path": video_path,
            "avatar_id": avatar_id,
            "persona_id": input_data.persona_id,
            "step": "video_generation"
        }
        
        jobs[job_id].update({
            "status": "completed",
            "results": results,
            "progress": "Video generation completed successfully"
        })
        
    except Exception as e:
        jobs[job_id].update({
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
    job_id = str(uuid.uuid4())
    temp_file = Config.TEMP_DIR / f"upload_{job_id}_{file.filename}"
    
    try:
        with open(temp_file, "wb") as f:
            f.write(content)
        
        # Initialize job
        jobs[job_id] = {
            "status": "processing",
            "progress": f"File uploaded, starting processing with {persona.name}...",
            "file_path": str(temp_file),
            "persona_id": persona_id
        }
        
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
        jobs[job_id]["progress"] = "Processing audio/video..."
        
        results = workflow.process_audio_video_input(
            file_path,
            context=context,
            output_filename=f"job_{job_id}",
            avatar_id=avatar_id,
            voice_settings=voice_settings,
            persona_id=persona_id
        )
        
        jobs[job_id].update({
            "status": "completed",
            "results": results,
            "progress": "Processing completed successfully"
        })
        
    except Exception as e:
        jobs[job_id].update({
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
    
    job_id = str(uuid.uuid4())
    
    # Initialize job
    jobs[job_id] = {
        "status": "processing",
        "progress": f"Generating hot take from text with {persona.name}...",
        "persona_id": input_data.persona_id
    }
    
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
        if input_data.use_heygen_voice:
            # Use HeyGen voice directly
            results = workflow.process_text_input_heygen_voice(
                input_data.text,
                context=input_data.context,
                output_filename=input_data.output_filename or f"text_job_{job_id}",
                avatar_id=input_data.avatar_id,
                voice_id=input_data.heygen_voice_id,
                persona_id=input_data.persona_id
            )
        else:
            # Use ElevenLabs voice
            results = workflow.process_text_input(
                input_data.text,
                context=input_data.context,
                output_filename=input_data.output_filename or f"text_job_{job_id}",
                avatar_id=input_data.avatar_id,
                voice_settings=input_data.voice_settings,
                persona_id=input_data.persona_id
            )
        
        jobs[job_id].update({
            "status": "completed",
            "results": results,
            "progress": "Text processing completed successfully"
        })
        
    except Exception as e:
        jobs[job_id].update({
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
    
    job_id = str(uuid.uuid4())
    
    # Initialize job
    jobs[job_id] = {
        "status": "processing",
        "progress": f"Generating quick roast with {persona.name}...",
        "persona_id": input_data.persona_id
    }
    
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
        results = workflow.quick_roast(
            input_data.topic,
            output_filename=input_data.output_filename or f"roast_job_{job_id}",
            avatar_id=input_data.avatar_id,
            persona_id=input_data.persona_id
        )
        
        jobs[job_id].update({
            "status": "completed",
            "results": results,
            "progress": "Quick roast completed successfully"
        })
        
    except Exception as e:
        jobs[job_id].update({
            "status": "failed",
            "error": str(e),
            "progress": "Quick roast failed"
        })

@app.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of a processing job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs[job_id]

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
