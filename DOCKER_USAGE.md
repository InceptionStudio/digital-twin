# Docker Setup for Digital Twin Web API

## Prerequisites
- Docker and Docker Compose installed
- API keys for OpenAI, ElevenLabs, and HeyGen services

## Quick Start

1. **Setup environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your API keys.

2. **Start the web API:**
   ```bash
   docker compose up --build
   ```
   The API will be available at http://localhost:8000

3. **View API documentation:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Docker Commands

```bash
# Start the service
docker compose up

# Start in background
docker compose up -d

# View logs
docker compose logs -f

# Stop the service
docker compose down

# Rebuild after code changes
docker compose build

# Restart the service
docker compose restart
```

## API Endpoints

The web API provides the following endpoints:
- `POST /generate` - Generate content from a topic
- `POST /process_audio` - Process audio file
- `POST /chad_workflow` - Run the complete Chad workflow
- Various workflow step endpoints

## Volume Mounts

The following directories are mounted:
- `./temp` - Temporary files during processing
- `./output` - Generated output files  
- `./personas` - Persona configurations

## Health Check

The service includes a health check endpoint at `/health` that Docker uses to monitor the container status.

## Troubleshooting

- Ensure all required API keys are set in `.env`
- Check logs with `docker compose logs` if the service fails
- Verify ports are not already in use (default: 8000)