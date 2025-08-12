#!/usr/bin/env python3
"""
Test script for OpenAI/GPT hot take generation only.
This allows testing Chad's responses without using ElevenLabs or HeyGen credits.
"""

import sys
import argparse
from gpt_generator import HotTakeGenerator

def test_hot_take_generation():
    """Test hot take generation with sample inputs."""
    
    print("🧪 Chad Goldstein - GPT Hot Take Test")
    print("=" * 50)
    
    try:
        # Initialize the hot take generator
        print("🚀 Initializing GPT hot take generator...")
        generator = HotTakeGenerator()
        
        # Test connection first
        print("🔧 Testing OpenAI connection...")
        if generator.test_connection():
            print("✅ OpenAI connection successful")
        else:
            print("❌ OpenAI connection failed")
            return 1
        
        # Sample test cases
        test_cases = [
            {
                "name": "Pet Tech Startup",
                "pitch": "We're building PetConnect, an AI-powered platform that matches pet owners with the perfect dog walkers in their neighborhood. Our proprietary algorithm analyzes pet personality, owner preferences, and walker expertise to create optimal matches. We're seeking $2M in Series A funding to scale nationwide.",
                "context": "Series A pitch for pet tech startup"
            },
            {
                "name": "Quick Roast Topic", 
                "pitch": "A blockchain-based dating app for influencers",
                "context": None,
                "is_roast": True
            },
            {
                "name": "FinTech Startup",
                "pitch": "Our revolutionary FinTech platform uses machine learning to predict market trends and automatically invest users' spare change. We've processed over $50M in transactions and have 100K active users. Looking for $10M Series B.",
                "context": "Series B FinTech pitch"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'='*60}")
            print(f"🎭 Test Case {i}: {test_case['name']}")
            print("="*60)
            print(f"Input: {test_case['pitch']}")
            if test_case['context']:
                print(f"Context: {test_case['context']}")
            
            print(f"\n🤔 Generating Chad's hot take...")
            
            try:
                if test_case.get('is_roast'):
                    response = generator.generate_quick_roast(test_case['pitch'])
                else:
                    response = generator.generate_hot_take(test_case['pitch'], test_case['context'])
                
                print(f"\n🔥 Chad's Response:")
                print("-" * 50)
                print(response)
                print("-" * 50)
                print(f"✅ Response length: {len(response)} characters")
                
            except Exception as e:
                print(f"❌ Failed to generate response: {str(e)}")
        
        print(f"\n{'='*60}")
        print("🎉 GPT Hot Take Test Completed!")
        print("💡 If the responses look good, you can now test the full pipeline.")
        
        return 0
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return 1

def interactive_test():
    """Interactive mode for testing custom inputs."""
    
    print("🎭 Chad Goldstein - Interactive GPT Test")
    print("=" * 50)
    
    try:
        generator = HotTakeGenerator()
        
        print("Enter your startup pitch or topic (or 'quit' to exit):")
        
        while True:
            user_input = input("\n💬 Your input: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Thanks for testing Chad's hot takes!")
                break
            
            if not user_input:
                continue
            
            # Ask if it's a roast or regular pitch
            is_roast = input("Is this a quick roast topic? (y/n): ").lower().startswith('y')
            
            context = None
            if not is_roast:
                context = input("Context (optional): ").strip() or None
            
            print(f"\n🤔 Chad is thinking...")
            
            try:
                if is_roast:
                    response = generator.generate_quick_roast(user_input)
                else:
                    response = generator.generate_hot_take(user_input, context)
                
                print(f"\n🔥 Chad's Hot Take:")
                print("-" * 50)
                print(response)
                print("-" * 50)
                
            except Exception as e:
                print(f"❌ Error: {str(e)}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Interactive test failed: {str(e)}")
        return 1

def main():
    parser = argparse.ArgumentParser(description="Test Chad's GPT hot take generation only")
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    parser.add_argument(
        "--text", "-t",
        type=str,
        help="Test with specific text input"
    )
    parser.add_argument(
        "--roast", "-r",
        type=str,
        help="Test quick roast with specific topic"
    )
    parser.add_argument(
        "--context", "-c",
        type=str,
        help="Context for the hot take (only with --text)"
    )
    
    args = parser.parse_args()
    
    if args.interactive:
        return interactive_test()
    elif args.text:
        try:
            generator = HotTakeGenerator()
            print(f"🎭 Testing with text: {args.text}")
            if args.context:
                print(f"📋 Context: {args.context}")
            
            response = generator.generate_hot_take(args.text, args.context)
            
            print(f"\n🔥 Chad's Hot Take:")
            print("-" * 50)
            print(response)
            print("-" * 50)
            
            return 0
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return 1
    elif args.roast:
        try:
            generator = HotTakeGenerator()
            print(f"🔥 Testing roast for: {args.roast}")
            
            response = generator.generate_quick_roast(args.roast)
            
            print(f"\n🔥 Chad's Roast:")
            print("-" * 50)
            print(response)
            print("-" * 50)
            
            return 0
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return 1
    else:
        # Run default test cases
        return test_hot_take_generation()

if __name__ == "__main__":
    sys.exit(main())
