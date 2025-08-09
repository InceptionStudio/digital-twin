#!/usr/bin/env python3
"""
Example usage of the Chad Goldstein Digital Twin workflow.
This script demonstrates various ways to use the system.
"""

import os
import sys
from pathlib import Path
from chad_workflow import ChadWorkflow

def main():
    """Demonstrate various usage patterns."""
    
    print("🚀 Chad Goldstein Digital Twin - Example Usage\n")
    
    try:
        # Initialize the workflow
        print("Initializing workflow...")
        workflow = ChadWorkflow()
        print("✅ Workflow initialized successfully\n")
        
        # Test all service connections
        print("🔧 Testing service connections...")
        test_results = workflow.test_all_services()
        
        all_connected = True
        for service, status in test_results.items():
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {service.title()}: {'Connected' if status else 'Failed'}")
            if not status:
                all_connected = False
        
        if not all_connected:
            print("\n⚠️  Some services are not connected. Please check your API keys in .env file.")
            print("You can still run the examples, but they may fail at certain steps.\n")
        else:
            print("✅ All services connected successfully!\n")
        
        # Example 1: Process text input
        print("📝 Example 1: Processing text input")
        print("─" * 50)
        
        sample_pitch = """
        We're building PetConnect, an AI-powered platform that matches pet owners 
        with the perfect dog walkers in their neighborhood. Our proprietary algorithm 
        analyzes pet personality, owner preferences, and walker expertise to create 
        optimal matches. We're seeking $2M in Series A funding to scale nationwide.
        """
        
        print("Input text:", sample_pitch.strip())
        print("\nProcessing...")
        
        try:
            results = workflow.process_text_input(
                sample_pitch,
                context="Series A pitch for pet tech startup",
                output_filename="example_text_demo"
            )
            
            print(f"✅ Text processing completed in {results['processing_time']:.2f} seconds")
            print(f"🎵 Audio file: {results['audio_path']}")
            print(f"🎥 Video file: {results['video_path']}")
            print("\n💭 Chad's Hot Take:")
            print("─" * 40)
            print(results['hot_take'][:300] + "..." if len(results['hot_take']) > 300 else results['hot_take'])
            print("─" * 40)
            
        except Exception as e:
            print(f"❌ Text processing failed: {str(e)}")
        
        print("\n" + "="*60 + "\n")
        
        # Example 2: Quick roast
        print("🔥 Example 2: Quick roast generation")
        print("─" * 50)
        
        roast_topic = "A blockchain-based dating app for influencers"
        print(f"Roast topic: {roast_topic}")
        print("\nGenerating roast...")
        
        try:
            results = workflow.quick_roast(
                roast_topic,
                output_filename="example_roast_demo"
            )
            
            print(f"✅ Roast completed in {results['processing_time']:.2f} seconds")
            print(f"🎵 Audio file: {results['audio_path']}")
            print(f"🎥 Video file: {results['video_path']}")
            print("\n🔥 Chad's Roast:")
            print("─" * 40)
            print(results['roast'])
            print("─" * 40)
            
        except Exception as e:
            print(f"❌ Roast generation failed: {str(e)}")
        
        print("\n" + "="*60 + "\n")
        
        # Example 3: Service information
        print("📋 Example 3: Service information")
        print("─" * 50)
        
        try:
            info = workflow.get_service_info()
            
            print("Configuration:")
            config = info.get('config', {})
            for key, value in config.items():
                print(f"  {key}: {value}")
            
            if 'elevenlabs_voices' in info:
                voices = info['elevenlabs_voices'].get('voices', [])
                print(f"\nElevenLabs voices available: {len(voices)}")
                for voice in voices[:3]:  # Show first 3
                    print(f"  - {voice.get('name', 'Unknown')} ({voice.get('voice_id', 'No ID')})")
                if len(voices) > 3:
                    print(f"  ... and {len(voices) - 3} more")
            
            if 'heygen_avatars' in info:
                avatars = info['heygen_avatars'].get('data', {}).get('avatars', [])
                print(f"\nHeyGen avatars available: {len(avatars)}")
                for avatar in avatars[:3]:  # Show first 3
                    print(f"  - {avatar.get('name', 'Unknown')} ({avatar.get('avatar_id', 'No ID')})")
                if len(avatars) > 3:
                    print(f"  ... and {len(avatars) - 3} more")
                    
        except Exception as e:
            print(f"❌ Failed to get service info: {str(e)}")
        
        print("\n" + "="*60 + "\n")
        
        # Example 4: Custom voice settings
        print("🎛️  Example 4: Custom voice settings")
        print("─" * 50)
        
        custom_voice_settings = {
            "stability": 0.9,      # Higher stability
            "similarity_boost": 0.8,  # Higher similarity
            "style": 0.9           # More expressive
        }
        
        print("Voice settings:", custom_voice_settings)
        print("Generating with custom voice...")
        
        try:
            results = workflow.process_text_input(
                "This startup idea is so revolutionary, it makes the iPhone look like a flip phone!",
                output_filename="example_custom_voice",
                voice_settings=custom_voice_settings
            )
            
            print(f"✅ Custom voice generation completed in {results['processing_time']:.2f} seconds")
            print(f"🎵 Audio file: {results['audio_path']}")
            print(f"🎥 Video file: {results['video_path']}")
            
        except Exception as e:
            print(f"❌ Custom voice generation failed: {str(e)}")
        
        print("\n" + "="*60 + "\n")
        
        # Example 5: File cleanup
        print("🧹 Example 5: File cleanup")
        print("─" * 50)
        
        print("Cleaning up generated files...")
        try:
            workflow.cleanup_files()
            print("✅ Cleanup completed")
        except Exception as e:
            print(f"❌ Cleanup failed: {str(e)}")
        
        print("\n🎉 All examples completed!")
        print("\nNext steps:")
        print("1. Try the CLI: python cli.py --help")
        print("2. Start the web API: python web_api.py")
        print("3. Upload your own audio/video files")
        print("4. Customize Chad's personality in chadprompt.txt")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Examples cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error running examples: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
