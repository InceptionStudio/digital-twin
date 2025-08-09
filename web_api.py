"""
Chad Goldstein Digital Twin Web API
FastAPI web interface for generating hot take responses via audio and video.
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import tempfile
import os
import uuid
from pathlib import Path
import logging

from chad_workflow import ChadWorkflow
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Chad Goldstein Digital Twin API",
    description="Generate hot take responses from Chad Goldstein via audio and video",
    version="1.0.0"
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

class RoastInput(BaseModel):
    topic: str
    output_filename: Optional[str] = None
    avatar_id: Optional[str] = None

class ProcessingStatus(BaseModel):
    job_id: str
    status: str
    progress: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# In-memory job storage (use Redis or database in production)
jobs: Dict[str, Dict[str, Any]] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize the workflow on startup."""
    global workflow
    try:
        workflow = ChadWorkflow()
        logger.info("Chad Workflow initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Chad Workflow: {str(e)}")
        raise

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Chad Goldstein Digital Twin API",
        "version": "1.0.0",
        "endpoints": {
            "POST /process-file": "Process audio/video file",
            "POST /process-text": "Process text input",
            "POST /quick-roast": "Generate quick roast",
            "GET /test": "Test service connections",
            "GET /info": "Get service information",
            "GET /job/{job_id}": "Get job status",
            "GET /download/{filename}": "Download generated files"
        }
    }

@app.post("/process-file")
async def process_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    context: Optional[str] = Form(None),
    avatar_id: Optional[str] = Form(None),
    voice_stability: Optional[float] = Form(0.75),
    voice_similarity: Optional[float] = Form(0.75),
    voice_style: Optional[float] = Form(0.8)
):
    """Process an uploaded audio or video file."""
    if not workflow:
        raise HTTPException(status_code=500, detail="Workflow not initialized")
    
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
            "progress": "File uploaded, starting processing...",
            "file_path": str(temp_file)
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
            voice_settings
        )
        
        return {"job_id": job_id, "status": "processing", "message": "File processing started"}
        
    except Exception as e:
        # Clean up temp file
        if temp_file.exists():
            temp_file.unlink()
        raise HTTPException(status_code=500, detail=str(e))

async def process_file_background(job_id: str, file_path: str, context: Optional[str],
                                avatar_id: Optional[str], voice_settings: Dict[str, float]):
    """Background task for processing files."""
    try:
        jobs[job_id]["progress"] = "Processing audio/video..."
        
        results = workflow.process_audio_video_input(
            file_path,
            context=context,
            output_filename=f"job_{job_id}",
            avatar_id=avatar_id,
            voice_settings=voice_settings
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
    
    job_id = str(uuid.uuid4())
    
    # Initialize job
    jobs[job_id] = {
        "status": "processing",
        "progress": "Generating hot take from text..."
    }
    
    # Start background processing
    background_tasks.add_task(
        process_text_background,
        job_id,
        input_data
    )
    
    return {"job_id": job_id, "status": "processing", "message": "Text processing started"}

async def process_text_background(job_id: str, input_data: TextInput):
    """Background task for processing text."""
    try:
        results = workflow.process_text_input(
            input_data.text,
            context=input_data.context,
            output_filename=input_data.output_filename or f"text_job_{job_id}",
            avatar_id=input_data.avatar_id,
            voice_settings=input_data.voice_settings
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
    
    job_id = str(uuid.uuid4())
    
    # Initialize job
    jobs[job_id] = {
        "status": "processing",
        "progress": "Generating quick roast..."
    }
    
    # Start background processing
    background_tasks.add_task(
        quick_roast_background,
        job_id,
        input_data
    )
    
    return {"job_id": job_id, "status": "processing", "message": "Quick roast generation started"}

async def quick_roast_background(job_id: str, input_data: RoastInput):
    """Background task for quick roast."""
    try:
        results = workflow.quick_roast(
            input_data.topic,
            output_filename=input_data.output_filename or f"roast_job_{job_id}",
            avatar_id=input_data.avatar_id
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
        "workflow_initialized": workflow is not None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
