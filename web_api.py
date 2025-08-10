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
