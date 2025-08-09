#!/usr/bin/env python3
"""
Chad Goldstein Digital Twin CLI
Command-line interface for generating hot take responses via audio and video.
"""

import argparse
import sys
import json
from pathlib import Path
from chad_workflow import ChadWorkflow

def main():
    parser = argparse.ArgumentParser(
        description="Generate Chad Goldstein hot take responses from audio/video input"
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
    if not any([args.test, args.info, args.cleanup]):
        if not any([args.file, args.text, args.roast]):
            parser.error("Must specify one of: --file, --text, --roast, --test, --info, or --cleanup")
    
    # Set up logging level
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize workflow
        print("🚀 Initializing Chad Goldstein Digital Twin...")
        workflow = ChadWorkflow()
        
        # Check for Chad's prompt file
        if not Path("chadprompt.txt").exists():
            print("⚠️  WARNING: chadprompt.txt file not found! Chad will use fallback personality.")
        elif Path("chadprompt.txt").stat().st_size == 0:
            print("⚠️  WARNING: chadprompt.txt file is empty! Chad may not be as flamboyant as usual.")
        
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
        
        # Prepare voice settings
        voice_settings = {
            "stability": args.voice_stability,
            "similarity_boost": args.voice_similarity,
            "style": args.voice_style
        }
        
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
                avatar_id=args.avatar_id,
                voice_settings=voice_settings
            )
        
        elif args.text:
            print(f"\n📝 Processing text input...")
            results = workflow.process_text_input(
                args.text,
                context=args.context,
                output_filename=args.output,
                avatar_id=args.avatar_id,
                voice_settings=voice_settings
            )
        
        elif args.roast:
            print(f"\n🔥 Generating quick roast for: {args.roast}")
            results = workflow.quick_roast(
                args.roast,
                output_filename=args.output,
                avatar_id=args.avatar_id
            )
        
        # Display results
        if results["status"] == "completed":
            print("\n🎉 Success! Generated files:")
            if "transcript" in results:
                print(f"📄 Transcript: {len(results['transcript'])} characters")
            print(f"💬 Hot Take: {len(results.get('hot_take', results.get('roast', '')))} characters")
            print(f"🎵 Audio: {results['audio_path']}")
            print(f"🎥 Video: {results['video_path']}")
            print(f"⏱️  Processing time: {results['processing_time']:.2f} seconds")
            
            # Show hot take preview
            hot_take_text = results.get('hot_take', results.get('roast', ''))
            if hot_take_text:
                print(f"\n💭 Chad's Hot Take Preview:")
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
