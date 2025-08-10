# Docker Setup for Digital Twin Application

## Prerequisites
- Docker and Docker Compose installed on your system
- API keys for OpenAI, ElevenLabs, and HeyGen services

## Quick Start

1. **Copy and configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your API keys.

2. **Build and run the application:**
   ```bash
   docker-compose up --build
   ```
   The web API will be available at http://localhost:8000

3. **Access the API documentation:**
   Visit http://localhost:8000/docs for the Swagger UI

## Available Services

### Web API Service (Default)
Runs the FastAPI web server:
```bash
docker-compose up
```

### CLI Service
Run the CLI interface in Docker:
```bash
docker-compose --profile cli run --rm digital-twin-cli
```

Or for specific CLI commands:
```bash
# Generate content
docker-compose run --rm digital-twin-cli python cli.py generate --topic "Your topic"

# Manage personas
docker-compose run --rm digital-twin-cli python persona_cli.py list

# Run Chad workflow
docker-compose run --rm digital-twin-cli python chad_workflow.py --input-file audio.mp3
```

## Volume Mounts

The following directories are mounted as volumes:
- `./temp` - Temporary files during processing
- `./output` - Generated output files
- `./personas` - Persona configurations and prompts

## Common Commands

```bash
# Start services in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose build

# Clean up volumes and containers
docker-compose down -v
```

## Troubleshooting

- If you encounter permission issues with volumes, ensure the `temp` and `output` directories exist and have proper permissions
- For GPU support (PyTorch), you may need to modify the Dockerfile to use CUDA base image
- Check logs with `docker-compose logs` if services fail to start