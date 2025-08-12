# ElevenLabs Model Support

This document describes the new ElevenLabs model listing functionality added to the voice_generator.

## Overview

The voice_generator now supports listing and querying available ElevenLabs models, allowing you to:
- List all available models
- Filter for text-to-speech models only
- Get detailed information about specific models
- Automatically select the best TTS model for your use case

## New Methods

### `get_available_models()`
Returns all available ElevenLabs models.

```python
from voice_generator import VoiceGenerator

vg = VoiceGenerator()
models = vg.get_available_models()
print(f"Found {len(models['models'])} models")
```

### `get_text_to_speech_models()`
Returns only models that support text-to-speech.

```python
tts_models = vg.get_text_to_speech_models()
print(f"Found {len(tts_models['models'])} TTS models")
```

### `get_model_info(model_id)`
Get detailed information about a specific model.

```python
model_info = vg.get_model_info("eleven_multilingual_v2")
model = model_info['model']
print(f"Model: {model.name}")
print(f"Description: {model.description}")
print(f"Can do TTS: {model.can_do_text_to_speech}")
```

### `get_best_tts_model()`
Automatically selects the best available text-to-speech model based on priority.

```python
best_model_id = vg.get_best_tts_model()
print(f"Best TTS model: {best_model_id}")
```

## Model Priority

The `get_best_tts_model()` method uses the following priority order:
1. `eleven_multilingual_v2` - Most life-like, emotionally rich
2. `eleven_turbo_v2` - High quality, low latency
3. `eleven_monolingual_v1` - English-only
4. `eleven_multilingual_v1` - Legacy multilingual

## Updated Speech Generation

The `generate_speech()` and `generate_speech_streaming()` methods now support:
- Automatic model selection (uses best available TTS model)
- Manual model specification via the `model_id` parameter

```python
# Use best available model
audio_path = vg.generate_speech("Hello world!")

# Use specific model
audio_path = vg.generate_speech(
    "Hello world!", 
    model_id="eleven_turbo_v2"
)
```

## Web API Endpoints

New REST endpoints are available:

### `GET /elevenlabs-models`
List all available ElevenLabs models.

### `GET /elevenlabs-tts-models`
List only text-to-speech models.

### `GET /elevenlabs-models/{model_id}`
Get detailed information about a specific model.

### `GET /elevenlabs-best-tts-model`
Get the best available TTS model ID.

## Model Properties

Each model object contains the following properties:

- `model_id`: Unique identifier
- `name`: Human-readable name
- `description`: Model description
- `can_do_text_to_speech`: Whether it supports TTS
- `can_use_style`: Whether it supports style control
- `can_use_speaker_boost`: Whether it supports speaker boost
- `maximum_text_length_per_request`: Max text length
- `token_cost_factor`: Cost factor for the model
- `languages`: Supported languages
- And more...

## Testing

Run the test script to verify functionality:

```bash
source venv/bin/activate
python test_models.py
```

## Available Models

As of the latest update, the following models are typically available:

1. **Eleven Multilingual v2** - Most life-like, 29 languages
2. **Eleven Flash v2.5** - Ultra low latency, 32 languages
3. **Eleven Turbo v2.5** - High quality, low latency, 32 languages
4. **Eleven Turbo v2** - English-only, low latency
5. **Eleven Flash v2** - Ultra low latency, English
6. **Eleven Multilingual v1** - Legacy multilingual
7. **Eleven English v1** - Legacy English-only

## Usage Examples

### CLI Usage
```python
from voice_generator import VoiceGenerator

vg = VoiceGenerator()

# List all models
models = vg.get_available_models()
for model in models['models']:
    print(f"{model.name}: {model.model_id}")

# Get best model for TTS
best_model = vg.get_best_tts_model()
print(f"Best model: {best_model}")

# Generate speech with specific model
audio = vg.generate_speech(
    "This is a test", 
    model_id="eleven_turbo_v2"
)
```

### Web API Usage
```bash
# List all models
curl http://localhost:8000/elevenlabs-models

# List TTS models only
curl http://localhost:8000/elevenlabs-tts-models

# Get specific model info
curl http://localhost:8000/elevenlabs-models/eleven_multilingual_v2

# Get best TTS model
curl http://localhost:8000/elevenlabs-best-tts-model
```
