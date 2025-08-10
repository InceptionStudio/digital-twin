#!/usr/bin/env python3
"""
Digital Twin CLI
Command-line interface for generating hot take responses via audio and video with multiple personas.
"""

import argparse
import sys
import json
from pathlib import Path
from chad_workflow import ChadWorkflow
from persona_manager import persona_manager

def main():
    parser = argparse.ArgumentParser(
        description="Generate hot take responses from audio/video input with multiple personas"
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=False)
    input_group.add_argument(
        "--file", "-f", 
        type=str, 
        help="Path to input audio or video file"
    )
    input_group.add_argument(
        "--text", "-t", 
        type=str, 
        help="Text input for hot take generation"
    )
    input_group.add_argument(
        "--roast", "-r", 
        type=str, 
        help="Topic to generate a quick roast about"
    )
    
    # Persona selection
    parser.add_argument(
        "--persona", "-p",
        type=str,
        default="chad_goldstein",
        help="Persona ID to use (default: chad_goldstein)"
    )
    
    # Voice provider options
    parser.add_argument(
        "--heygen-voice",
        action="store_true",
        help="Use HeyGen's text-to-speech instead of ElevenLabs"
    )
    parser.add_argument(
        "--heygen-voice-id",
        type=str,
        help="Specific HeyGen voice ID to use (overrides persona's default)"
    )
    
    # Optional parameters
    parser.add_argument(
        "--context", "-c",
        type=str,
        help="Additional context for the hot take"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Base filename for output files (without extension)"
    )
    parser.add_argument(
        "--avatar-id",
        type=str,
        help="Specific HeyGen avatar ID to use"
    )
    parser.add_argument(
        "--voice-stability",
        type=float,
        default=0.75,
        help="ElevenLabs voice stability (0.0-1.0)"
    )
    parser.add_argument(
        "--voice-similarity",
        type=float,
        default=0.75,
        help="ElevenLabs voice similarity boost (0.0-1.0)"
    )
    parser.add_argument(
        "--voice-style",
        type=float,
        default=0.8,
        help="ElevenLabs voice style (0.0-1.0)"
    )
    
    # Utility commands
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test all service connections"
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show service information (available voices, avatars)"
    )
    parser.add_argument(
        "--list-heygen-voices",
        action="store_true",
        help="List available HeyGen voices"
    )
    parser.add_argument(
        "--list-personas",
        action="store_true",
        help="List available personas"
    )
    parser.add_argument(
        "--show-persona",
        type=str,
        help="Show detailed information about a specific persona"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up temporary and old files"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Validate arguments - if no utility commands, require input
    if not any([args.test, args.info, args.cleanup, args.list_heygen_voices, args.list_personas, args.show_persona]):
        if not any([args.file, args.text, args.roast]):
            parser.error("Must specify one of: --file, --text, --roast, --test, --info, --list-heygen-voices, --list-personas, --show-persona, or --cleanup")
    
    # Set up logging level
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Handle persona-related commands first
        if args.list_personas:
            personas = persona_manager.list_personas()
            if not personas:
                print("No personas found.")
                return 0
            
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
            return 0
        
        if args.show_persona:
            persona = persona_manager.get_persona(args.show_persona)
            if not persona:
                print(f"❌ Persona '{args.show_persona}' not found.")
                return 1
            
            validation = persona_manager.validate_persona(args.show_persona)
            
            print(f"\n🎭 {persona.name} (ID: {args.show_persona})")
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
            return 0
        
        # Get selected persona
        selected_persona = persona_manager.get_persona(args.persona)
        if not selected_persona:
            print(f"❌ Persona '{args.persona}' not found.")
            print("Available personas:")
            for persona_info in persona_manager.list_personas():
                print(f"  - {persona_info['id']}: {persona_info['name']}")
            return 1
        
        # Initialize workflow
        print(f"🚀 Initializing {selected_persona.name} Digital Twin...")
        workflow = ChadWorkflow()
        
        # Check for persona's prompt file
        if not Path(selected_persona.prompt_file).exists():
            print(f"⚠️  WARNING: {selected_persona.prompt_file} file not found! {selected_persona.name} will use fallback personality.")
        elif Path(selected_persona.prompt_file).stat().st_size == 0:
            print(f"⚠️  WARNING: {selected_persona.prompt_file} file is empty! {selected_persona.name} may not be as distinctive as usual.")
        
        # Handle utility commands
        if args.test:
            print("\n🔧 Testing service connections...")
            results = workflow.test_all_services()
            for service, status in results.items():
                status_icon = "✅" if status else "❌"
                print(f"{status_icon} {service.title()}: {'Connected' if status else 'Failed'}")
            return 0 if all(results.values()) else 1
        
        if args.info:
            print("\n📋 Service Information:")
            info = workflow.get_service_info()
            print(json.dumps(info, indent=2))
            return 0
        
        if args.cleanup:
            print("\n🧹 Cleaning up files...")
            workflow.cleanup_files()
            print("✅ Cleanup completed")
            return 0
        
        if args.list_heygen_voices:
            print("\n🎤 Available HeyGen Voices:")
            try:
                voices = workflow.video_generator.get_voices()
                
                if isinstance(voices, dict) and "data" in voices and isinstance(voices["data"], list):
                    voice_list = voices["data"]
                else:
                    print(f"  Unexpected response structure")
                    return 0
                
                # Sort voices by language and name for better organization
                voice_list.sort(key=lambda x: (x.get("language", ""), x.get("name", "")))
                
                current_language = None
                for voice in voice_list:
                    voice_id = voice.get("voice_id", "N/A")
                    name = voice.get("name", "Unnamed")
                    language = voice.get("language", "Unknown")
                    gender = voice.get("gender", "Unknown")
                    
                    # Print language header when it changes
                    if language != current_language:
                        print(f"\n📁 {language}:")
                        current_language = language
                    
                    print(f"  • {name} ({gender}) - ID: {voice_id}")
                
                print(f"\n✅ Found {len(voice_list)} voices")
                
            except Exception as e:
                print(f"❌ Error fetching voices: {str(e)}")
            return 0
        
        # Prepare voice settings
        voice_settings = {
            "stability": args.voice_stability,
            "similarity_boost": args.voice_similarity,
            "style": args.voice_style
        }
        
        # Use persona's voice/avatar IDs if not overridden
        avatar_id = args.avatar_id or selected_persona.heygen_avatar_id
        voice_id = args.heygen_voice_id or selected_persona.heygen_voice_id
        
        # Process input based on type
        if args.file:
            print(f"\n🎬 Processing file: {args.file}")
            if not Path(args.file).exists():
                print(f"❌ Error: File not found: {args.file}")
                return 1
            
            results = workflow.process_audio_video_input(
                args.file,
                context=args.context,
                output_filename=args.output,
                avatar_id=avatar_id,
                voice_settings=voice_settings,
                persona_id=args.persona
            )
        
        elif args.text:
            if args.heygen_voice:
                print(f"\n📝 Processing text input with HeyGen voice...")
                results = workflow.process_text_input_heygen_voice(
                    args.text,
                    context=args.context,
                    output_filename=args.output,
                    avatar_id=avatar_id,
                    voice_id=voice_id,
                    persona_id=args.persona
                )
            else:
                print(f"\n📝 Processing text input with ElevenLabs voice...")
                results = workflow.process_text_input(
                    args.text,
                    context=args.context,
                    output_filename=args.output,
                    avatar_id=avatar_id,
                    voice_settings=voice_settings,
                    persona_id=args.persona
                )
        
        elif args.roast:
            print(f"\n🔥 Generating quick roast for: {args.roast}")
            results = workflow.quick_roast(
                args.roast,
                output_filename=args.output,
                avatar_id=avatar_id,
                persona_id=args.persona
            )
        
        # Display results
        if results["status"] == "completed":
            print("\n🎉 Success! Generated files:")
            if "transcript" in results:
                print(f"📄 Transcript: {len(results['transcript'])} characters")
            print(f"💬 Hot Take: {len(results.get('hot_take', results.get('roast', '')))} characters")
            if 'openai_latency' in results:
                print(f"⏱️  OpenAI API: {results['openai_latency']:.2f}s ({results.get('openai_tokens', 'N/A')} tokens)")
            
            # Handle different voice providers
            if results.get("voice_provider") == "heygen":
                print(f"🎤 Voice: HeyGen (ID: {results.get('voice_id', 'default')})")
                print(f"🎥 Video: {results['video_path']}")
                print(f"⏱️  Total processing time: {results['total_processing_time']:.2f} seconds")
            else:
                print(f"🎵 Audio: {results['audio_path']}")
                print(f"🎥 Video: {results['video_path']}")
                print(f"⏱️  Total processing time: {results['processing_time']:.2f} seconds")
            
            # Show hot take preview
            hot_take_text = results.get('hot_take', results.get('roast', ''))
            if hot_take_text:
                print(f"\n💭 {selected_persona.name}'s Hot Take Preview:")
                print("─" * 60)
                preview = hot_take_text[:200] + "..." if len(hot_take_text) > 200 else hot_take_text
                print(preview)
                print("─" * 60)
        
        else:
            print(f"\n❌ Error: {results.get('error', 'Unknown error')}")
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
