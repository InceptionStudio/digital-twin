"""
Persona Management CLI

Command-line interface for managing personas in the Digital Twin system.
"""

import argparse
import sys
from pathlib import Path
from persona_manager import persona_manager, Persona


def list_personas():
    """List all available personas"""
    personas = persona_manager.list_personas()
    
    if not personas:
        print("No personas found.")
        return
    
    print(f"\n📋 Available Personas ({len(personas)}):")
    print("=" * 80)
    
    for persona_info in personas:
        print(f"\n🎭 {persona_info['name']} (ID: {persona_info['id']})")
        print(f"   Bio: {persona_info['bio']}")
        if persona_info['description']:
            print(f"   Description: {persona_info['description']}")
        
        # Show configuration status
        configs = []
        if persona_info['has_image']:
            configs.append("📷 Image")
        if persona_info['has_elevenlabs']:
            configs.append("🎤 ElevenLabs Voice")
        if persona_info['has_heygen_voice']:
            configs.append("🎵 HeyGen Voice")
        if persona_info['has_heygen_avatar']:
            configs.append("👤 HeyGen Avatar")
        
        if configs:
            print(f"   Configurations: {', '.join(configs)}")
        else:
            print("   ⚠️  No configurations set")


def show_persona(persona_id: str):
    """Show detailed information about a specific persona"""
    persona = persona_manager.get_persona(persona_id)
    if not persona:
        print(f"❌ Persona '{persona_id}' not found.")
        return
    
    validation = persona_manager.validate_persona(persona_id)
    
    print(f"\n🎭 {persona.name} (ID: {persona_id})")
    print("=" * 60)
    print(f"Bio: {persona.bio}")
    if persona.description:
        print(f"Description: {persona.description}")
    
    print(f"\n📁 Files:")
    print(f"  Prompt: {persona.prompt_file}")
    if persona.image_file:
        print(f"  Image: {persona.image_file}")
    
    print(f"\n🎤 Voice Configuration:")
    if persona.elevenlabs_voice_id:
        print(f"  ElevenLabs Voice ID: {persona.elevenlabs_voice_id}")
    if persona.heygen_voice_id:
        print(f"  HeyGen Voice ID: {persona.heygen_voice_id}")
    
    print(f"\n👤 Avatar Configuration:")
    if persona.heygen_avatar_id:
        print(f"  HeyGen Avatar ID: {persona.heygen_avatar_id}")
    
    print(f"\n✅ Validation:")
    if validation['valid']:
        print("  Status: ✅ Valid")
    else:
        print("  Status: ❌ Invalid")
        for error in validation['errors']:
            print(f"    Error: {error}")
    
    if validation['warnings']:
        print("  Warnings:")
        for warning in validation['warnings']:
            print(f"    ⚠️  {warning}")


def add_persona():
    """Add a new persona interactively"""
    print("\n🎭 Adding New Persona")
    print("=" * 40)
    
    # Get basic information
    persona_id = input("Persona ID (e.g., 'chad_goldstein'): ").strip()
    if not persona_id:
        print("❌ Persona ID is required.")
        return
    
    if persona_manager.get_persona(persona_id):
        print(f"❌ Persona '{persona_id}' already exists.")
        return
    
    name = input("Name: ").strip()
    if not name:
        print("❌ Name is required.")
        return
    
    bio = input("Bio: ").strip()
    if not bio:
        print("❌ Bio is required.")
        return
    
    prompt_file = input("Prompt file path (e.g., 'personas/prompts/chad_goldstein.txt'): ").strip()
    if not prompt_file:
        print("❌ Prompt file is required.")
        return
    
    # Optional fields
    description = input("Description (optional): ").strip() or None
    image_file = input("Image file path (optional): ").strip() or None
    elevenlabs_voice_id = input("ElevenLabs Voice ID (optional): ").strip() or None
    heygen_voice_id = input("HeyGen Voice ID (optional): ").strip() or None
    heygen_avatar_id = input("HeyGen Avatar ID (optional): ").strip() or None
    
    # Create persona
    persona = Persona(
        name=name,
        bio=bio,
        prompt_file=prompt_file,
        image_file=image_file,
        elevenlabs_voice_id=elevenlabs_voice_id,
        heygen_voice_id=heygen_voice_id,
        heygen_avatar_id=heygen_avatar_id,
        description=description
    )
    
    persona_manager.add_persona(persona_id, persona)
    print(f"✅ Added persona: {name} (ID: {persona_id})")


def update_persona(persona_id: str):
    """Update an existing persona"""
    persona = persona_manager.get_persona(persona_id)
    if not persona:
        print(f"❌ Persona '{persona_id}' not found.")
        return
    
    print(f"\n🔄 Updating Persona: {persona.name}")
    print("=" * 50)
    print("Press Enter to keep current value, or type new value:")
    
    updates = {}
    
    # Update fields
    new_name = input(f"Name [{persona.name}]: ").strip()
    if new_name:
        updates['name'] = new_name
    
    new_bio = input(f"Bio [{persona.bio}]: ").strip()
    if new_bio:
        updates['bio'] = new_bio
    
    new_prompt_file = input(f"Prompt file [{persona.prompt_file}]: ").strip()
    if new_prompt_file:
        updates['prompt_file'] = new_prompt_file
    
    new_description = input(f"Description [{persona.description or ''}]: ").strip()
    if new_description:
        updates['description'] = new_description
    
    new_image_file = input(f"Image file [{persona.image_file or ''}]: ").strip()
    if new_image_file:
        updates['image_file'] = new_image_file
    
    new_elevenlabs_voice_id = input(f"ElevenLabs Voice ID [{persona.elevenlabs_voice_id or ''}]: ").strip()
    if new_elevenlabs_voice_id:
        updates['elevenlabs_voice_id'] = new_elevenlabs_voice_id
    
    new_heygen_voice_id = input(f"HeyGen Voice ID [{persona.heygen_voice_id or ''}]: ").strip()
    if new_heygen_voice_id:
        updates['heygen_voice_id'] = new_heygen_voice_id
    
    new_heygen_avatar_id = input(f"HeyGen Avatar ID [{persona.heygen_avatar_id or ''}]: ").strip()
    if new_heygen_avatar_id:
        updates['heygen_avatar_id'] = new_heygen_avatar_id
    
    if updates:
        persona_manager.update_persona(persona_id, updates)
        print(f"✅ Updated persona: {persona.name}")
    else:
        print("No changes made.")


def delete_persona(persona_id: str):
    """Delete a persona"""
    persona = persona_manager.get_persona(persona_id)
    if not persona:
        print(f"❌ Persona '{persona_id}' not found.")
        return
    
    confirm = input(f"Are you sure you want to delete '{persona.name}' (ID: {persona_id})? (y/N): ").strip().lower()
    if confirm in ['y', 'yes']:
        if persona_manager.delete_persona(persona_id):
            print(f"✅ Deleted persona: {persona.name}")
        else:
            print("❌ Failed to delete persona.")
    else:
        print("Deletion cancelled.")


def validate_persona(persona_id: str):
    """Validate a persona's configuration"""
    validation = persona_manager.validate_persona(persona_id)
    
    if validation['valid']:
        print(f"✅ Persona '{persona_id}' is valid!")
    else:
        print(f"❌ Persona '{persona_id}' has errors:")
        for error in validation['errors']:
            print(f"  - {error}")
    
    if validation['warnings']:
        print(f"\n⚠️  Warnings for '{persona_id}':")
        for warning in validation['warnings']:
            print(f"  - {warning}")


def main():
    parser = argparse.ArgumentParser(description="Persona Management CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List personas
    subparsers.add_parser('list', help='List all personas')
    
    # Show persona
    show_parser = subparsers.add_parser('show', help='Show detailed information about a persona')
    show_parser.add_argument('persona_id', help='Persona ID to show')
    
    # Add persona
    subparsers.add_parser('add', help='Add a new persona interactively')
    
    # Update persona
    update_parser = subparsers.add_parser('update', help='Update an existing persona')
    update_parser.add_argument('persona_id', help='Persona ID to update')
    
    # Delete persona
    delete_parser = subparsers.add_parser('delete', help='Delete a persona')
    delete_parser.add_argument('persona_id', help='Persona ID to delete')
    
    # Validate persona
    validate_parser = subparsers.add_parser('validate', help='Validate a persona configuration')
    validate_parser.add_argument('persona_id', help='Persona ID to validate')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'list':
            list_personas()
        elif args.command == 'show':
            show_persona(args.persona_id)
        elif args.command == 'add':
            add_persona()
        elif args.command == 'update':
            update_persona(args.persona_id)
        elif args.command == 'delete':
            delete_persona(args.persona_id)
        elif args.command == 'validate':
            validate_persona(args.persona_id)
    
    except KeyboardInterrupt:
        print("\n\nOperation cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
