#!/usr/bin/env python3
"""
Test script to try out the ElevenLabs eleven_v3 model (hardcoded).
"""

from voice_generator import VoiceGenerator
import json
import requests
from config import Config

def test_eleven_v3_direct_api():
    """Test eleven_v3 model using direct API call."""
    try:
        print("=== Testing ElevenLabs eleven_v3 Model (Direct API) ===\n")
        
        # Test direct API access
        print("1. Testing direct API access to eleven_v3...")
        
        # Get the API token from config
        api_token = getattr(Config, 'ELEVENLABS_API_TOKEN', None)
        if not api_token:
            print("   ✗ ELEVENLABS_API_TOKEN not found in config")
            return False
        
        url = "https://api.us.elevenlabs.io/v1/text-to-speech/gAKthYOSzqg2QQCLq9YD"
        
        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'authorization': f'Bearer {api_token}',
            'content-type': 'application/json',
            'origin': 'https://elevenlabs.io',
            'priority': 'u=1, i',
            'referer': 'https://elevenlabs.io/',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
        }
        
        payload = {
            "text": "[chuckles] Like sneaking a minibar into Met Gala, a jacket that pours shots. [exhales sharply] Sexy. [pause] I did it in two thousand three, tequila belt, yacht impounded. But your moat’s a puddle, users fit in my fucking wine cellar. [annoyed] I put radio on the fucking internet. [pause] Let’s drown it in champagne.",
            #"text": "[excited] Hello! This is a test of the ElevenLabs eleven_v3 model using direct API access. [thoughtful] I wonder how it handles different emotional expressions and vocal styles. [curious] Let me try some various audio tags to see the range of capabilities. [chuckles] This should be interesting! [energetic] The model should be able to convey excitement, [frustrated] frustration, [surprised] surprise, and [sarcastic] even sarcasm. [mischievously] Let's see if it can handle whispering too. [whispering] Can you hear this whispered part? [loudly] And now back to normal volume! [laughs] This is quite fun to test. [pauses] Sometimes a pause can be very effective. [gasp] Oh! Did you hear that gasp? [sigh] And now a sigh of relief. [woo] Woo! That was exciting! [stammers] I-I'm testing stuttering now. [rushed] And speaking quickly to test rushed speech. [quietly] And back to quiet again. [shouting] AND NOW SHOUTING! [exhales sharply] Whew, that was intense. [gulps] *gulp* Nervous much? [snorts] *snort* That was unexpected. [laughs harder] *laughs uncontrollably* [starts laughing] *starts laughing* This is getting ridiculous! [annoyed] Ugh, enough with the audio tags already! [happy] But seriously, this eleven_v3 model seems pretty impressive!",
            "model_id": "eleven_v3",
            "voice_settings": {
                "stability": 0.5,
                "use_speaker_boost": True
            }
        }
        
        print(f"   Making request to: {url}")
        print(f"   Using model: {payload['model_id']}")
        print(f"   Using voice ID from URL: gAKthYOSzqg2QQCLq9YD")
        
        response = requests.post(url, headers=headers, json=payload, stream=True)
        
        print(f"   Response status: {response.status_code}")
        print(f"   Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("   ✓ Success! Direct API access works with eleven_v3")
            
            # Save the audio stream
            output_path = Config.OUTPUT_DIR / "test_eleven_v3_direct_api.mp3"
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"   Audio saved to: {output_path}")
            return True
            
        else:
            print(f"   ✗ Failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   Error text: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ✗ Exception during direct API test: {str(e)}")
        return False

def test_eleven_v3_model():
    """Test the eleven_v3 model specifically, even if not in available models list."""
    try:
        # Initialize the voice generator
        voice_gen = VoiceGenerator()
        
        print("=== Testing ElevenLabs eleven_v3 Model (Hardcoded) ===\n")
        
        # Test 1: Check available models first
        print("1. Checking available models...")
        all_models = voice_gen.get_available_models()
        eleven_v3_model = None
        
        for model in all_models['models']:
            if model.model_id == "eleven_v3":
                eleven_v3_model = model
                break
        
        if eleven_v3_model:
            print(f"   ✓ Found eleven_v3 model in available models!")
            print(f"   Name: {eleven_v3_model.name}")
            print(f"   Description: {eleven_v3_model.description}")
            print(f"   Can do TTS: {eleven_v3_model.can_do_text_to_speech}")
            print()
        else:
            print("   ⚠ eleven_v3 not in available models list, but will try anyway...")
            print("   Available models:")
            for model in all_models['models']:
                print(f"     - {model.model_id}: {model.name}")
            print()
        
        # Test 2: Generate speech with eleven_v3 model (hardcoded)
        print("2. Testing speech generation with eleven_v3 (hardcoded)...")
        test_text = "Hello! This is a test of the ElevenLabs eleven_v3 model. It should sound great!"
        
        try:
            audio_path = voice_gen.generate_speech(
                text=test_text,
                output_filename="test_eleven_v3.mp3",
                model_id="eleven_v3",  # Hardcoded to eleven_v3
                voice_settings={
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            )
            print(f"   ✓ Successfully generated audio with eleven_v3!")
            print(f"   Audio saved to: {audio_path}")
            print()
        except Exception as e:
            print(f"   ✗ Failed to generate speech with eleven_v3: {str(e)}")
            print("   This might mean the model doesn't exist or requires special access.")
            return False
        
        # Test 3: Compare with default model
        print("3. Comparing with default model...")
        try:
            default_audio_path = voice_gen.generate_speech(
                text=test_text,
                output_filename="test_default_model.mp3",
                voice_settings={
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            )
            print(f"   ✓ Successfully generated audio with default model!")
            print(f"   Default audio saved to: {default_audio_path}")
            print()
        except Exception as e:
            print(f"   ✗ Failed to generate speech with default model: {str(e)}")
        
        print("\n=== Test completed successfully! ===")
        print("\nGenerated files:")
        print("- test_eleven_v3.mp3 (eleven_v3 model)")
        print("- test_default_model.mp3 (default model)")
        print("\nYou can now compare the audio quality and characteristics!")
        
        return True
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        return False

if __name__ == "__main__":
    # Test direct API access first
    print("Testing direct API access to eleven_v3...")
    direct_success = test_eleven_v3_direct_api()
    
    print("\n" + "="*60 + "\n")
    
    # Test through the voice generator
    print("Testing through voice generator...")
    generator_success = test_eleven_v3_model()
    
    print("\n" + "="*60 + "\n")
    print("SUMMARY:")
    print(f"Direct API test: {'✓ PASSED' if direct_success else '✗ FAILED'}")
    print(f"Generator test: {'✓ PASSED' if generator_success else '✗ FAILED'}")
