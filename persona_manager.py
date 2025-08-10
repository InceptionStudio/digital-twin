"""
Persona Management System for Digital Twin

This module manages different personas with their configurations including:
- Name and bio
- Custom prompts
- Voice IDs (ElevenLabs and HeyGen)
- Avatar IDs (HeyGen)
- Profile images
"""

import os
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class Persona:
    """Represents a persona configuration"""
    name: str
    bio: str
    prompt_file: str
    image_file: Optional[str] = None
    elevenlabs_voice_id: Optional[str] = None
    heygen_voice_id: Optional[str] = None
    heygen_avatar_id: Optional[str] = None
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert persona to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Persona':
        """Create persona from dictionary"""
        return cls(**data)


class PersonaManager:
    """Manages multiple personas and their configurations"""
    
    def __init__(self, personas_dir: str = "personas"):
        self.personas_dir = Path(personas_dir)
        self.personas_dir.mkdir(exist_ok=True)
        self.config_file = self.personas_dir / "personas.json"
        self.personas: Dict[str, Persona] = {}
        self.load_personas()
    
    def load_personas(self) -> None:
        """Load all personas from configuration file"""
        if not self.config_file.exists():
            logger.info("No personas configuration found. Creating default Chad Goldstein persona.")
            self.create_default_personas()
            return
        
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            print(f"🔍 DEBUG - Loaded JSON {self.config_file}: {data}")
            self.personas = {}
            for persona_id, persona_data in data.items():
                self.personas[persona_id] = Persona.from_dict(persona_data)
                # Debug: Print loaded persona details
                print(f"🔍 DEBUG - Loaded persona {persona_id}:")
                print(f"   name: {persona_data.get('name')}")
                print(f"   heygen_avatar_id: {persona_data.get('heygen_avatar_id')}")
                print(f"   heygen_voice_id: {persona_data.get('heygen_voice_id')}")
            
            logger.info(f"Loaded {len(self.personas)} personas")
            
        except Exception as e:
            logger.error(f"Error loading personas: {e}")
            self.create_default_personas()
    
    def save_personas(self) -> None:
        """Save all personas to configuration file"""
        try:
            data = {persona_id: persona.to_dict() for persona_id, persona in self.personas.items()}
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.personas)} personas")
        except Exception as e:
            logger.error(f"Error saving personas: {e}")
    
    def create_default_personas(self) -> None:
        """Create default personas including Chad Goldstein"""
        # Chad Goldstein persona
        chad_persona = Persona(
            name="Chad Goldstein",
            bio="A flamboyant, self-congratulatory venture capitalist and General Partner at Bling Capital Partners who delivers pitch critiques with ruthless candor, misguided self-comparisons to Warren Buffett, and unfiltered tech-bro energy",
            prompt_file="personas/prompts/chad_goldstein.txt",
            image_file="ChadGoldstein.jpg",
            elevenlabs_voice_id=None,  # Can be set later
            heygen_voice_id="82025eb9625b4c09aec78f89528cc33a",
            heygen_avatar_id="0ccb7cd7f5fe49f09ae90df50f2e9140",
            description="The original hot take commentator with a distinctive voice and style - like Kevin O'Leary from Shark Tank, but with one exit, three podcasts, and a six-figure LinkedIn following"
        )
        
        self.personas["chad_goldstein"] = chad_persona
        
        # Save the default personas
        self.save_personas()
    
    def add_persona(self, persona_id: str, persona: Persona) -> None:
        """Add a new persona"""
        self.personas[persona_id] = persona
        self.save_personas()
        logger.info(f"Added persona: {persona.name} (ID: {persona_id})")
    
    def get_persona(self, persona_id: str) -> Optional[Persona]:
        """Get a persona by ID"""
        persona = self.personas.get(persona_id)
        if persona:
            print(f"🔍 DEBUG - get_persona({persona_id}):")
            print(f"   name: {persona.name}")
            print(f"   heygen_avatar_id: {persona.heygen_avatar_id}")
            print(f"   heygen_voice_id: {persona.heygen_voice_id}")
        else:
            print(f"🔍 DEBUG - get_persona({persona_id}): Persona not found")
        return persona
    
    def list_personas(self) -> List[Dict[str, Any]]:
        """List all available personas"""
        return [
            {
                "id": persona_id,
                "name": persona.name,
                "bio": persona.bio,
                "description": persona.description,
                "has_image": persona.image_file is not None,
                "has_elevenlabs": persona.elevenlabs_voice_id is not None,
                "has_heygen_voice": persona.heygen_voice_id is not None,
                "has_heygen_avatar": persona.heygen_avatar_id is not None
            }
            for persona_id, persona in self.personas.items()
        ]
    
    def update_persona(self, persona_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing persona"""
        if persona_id not in self.personas:
            logger.error(f"Persona {persona_id} not found")
            return False
        
        persona = self.personas[persona_id]
        for key, value in updates.items():
            if hasattr(persona, key):
                setattr(persona, key, value)
        
        self.save_personas()
        logger.info(f"Updated persona: {persona.name} (ID: {persona_id})")
        return True
    
    def delete_persona(self, persona_id: str) -> bool:
        """Delete a persona"""
        if persona_id not in self.personas:
            logger.error(f"Persona {persona_id} not found")
            return False
        
        persona_name = self.personas[persona_id].name
        del self.personas[persona_id]
        self.save_personas()
        logger.info(f"Deleted persona: {persona_name} (ID: {persona_id})")
        return True
    
    def get_prompt_content(self, persona_id: str) -> Optional[str]:
        """Get the prompt content for a persona"""
        persona = self.get_persona(persona_id)
        if not persona:
            return None
        
        prompt_path = Path(persona.prompt_file)
        if not prompt_path.exists():
            logger.warning(f"Prompt file not found: {prompt_path}")
            return None
        
        try:
            with open(prompt_path, 'r') as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Error reading prompt file {prompt_path}: {e}")
            return None
    
    def validate_persona(self, persona_id: str) -> Dict[str, Any]:
        """Validate a persona's configuration"""
        persona = self.get_persona(persona_id)
        if not persona:
            return {"valid": False, "errors": ["Persona not found"]}
        
        errors = []
        warnings = []
        
        # Check prompt file
        if not Path(persona.prompt_file).exists():
            errors.append(f"Prompt file not found: {persona.prompt_file}")
        
        # Check image file
        if persona.image_file and not Path(persona.image_file).exists():
            warnings.append(f"Image file not found: {persona.image_file}")
        
        # Check voice configurations
        if not persona.elevenlabs_voice_id and not persona.heygen_voice_id:
            warnings.append("No voice ID configured (ElevenLabs or HeyGen)")
        
        # Check avatar configuration
        if not persona.heygen_avatar_id:
            warnings.append("No HeyGen avatar ID configured")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "persona": persona
        }
    
    def reload_personas(self) -> None:
        """Force reload personas from the configuration file"""
        print("🔄 Reloading personas from configuration file...")
        self.load_personas()


# Global persona manager instance
persona_manager = PersonaManager()
