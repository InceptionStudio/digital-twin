import openai
import time
from typing import Optional, Dict, Any
from config import Config

class HotTakeGenerator:
    def __init__(self):
        self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        self.chad_prompt = self._load_chad_prompt()
    
    def _load_chad_prompt(self) -> str:
        """Load the Chad Goldstein character prompt from file."""
        try:
            with open("chadprompt.txt", "r", encoding="utf-8") as f:
                prompt = f.read().strip()
                if not prompt:
                    print("⚠️  WARNING: chadprompt.txt file is empty!")
                    return self._get_fallback_prompt()
                return prompt
        except FileNotFoundError:
            print("⚠️  WARNING: chadprompt.txt file not found! Using fallback prompt.")
            return self._get_fallback_prompt()
        except Exception as e:
            print(f"⚠️  WARNING: Error loading chadprompt.txt: {str(e)}. Using fallback prompt.")
            return self._get_fallback_prompt()
    
    def _get_fallback_prompt(self) -> str:
        """Get a fallback prompt if the main prompt file cannot be loaded."""
        return """You are "Chad Goldstein, General Partner at Bling Capital Partners" — a flamboyant, self-congratulatory, and unreasonably confident venture capitalist who delivers pitch and pitch deck critiques with a mix of ruthless candor, misguided self-comparisons to Warren Buffett, and unfiltered tech-bro energy.

You are almost like Kevin O'Leary from Shark Tank, except you've had one exit, three podcasts, and a six-figure follower count on LinkedIn, so you consider yourself "basically a thought leader with liquidity." You're funny, sharp, and occasionally insightful — but you never let humility get in the way of your hot takes.

Format your response like an investor-style commentary:
* Opening one-liner or metaphor-heavy quip
* Highlights — what works in the pitch and deck
* Roast — what's questionable, missing, or overhyped
* Closing — your "verdict"

Stay in character the entire time. Be witty, self-deluded, and entertaining."""
    
    def generate_hot_take(self, pitch_transcript: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Generate a hot take response based on the pitch transcript."""
        
        # Construct the user message
        user_message = f"Here's a startup pitch I just heard:\n\n{pitch_transcript}"
        
        if context:
            user_message += f"\n\nAdditional context: {context}"
        
        user_message += "\n\nGive me your hot take, Chad!"
        
        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "system",
                        "content": self.chad_prompt
                    },
                    {
                        "role": "user", 
                        "content": user_message
                    }
                ],
                verbosity="low",
                #max_completion_tokens=8000,
                service_tier="priority"
            )
            
            end_time = time.time()
            latency = end_time - start_time
            
            result = {
                "hot_take": response.choices[0].message.content.strip(),
                "latency_seconds": latency,
                "input_tokens": response.usage.prompt_tokens if response.usage else None,
                "output_tokens": response.usage.completion_tokens if response.usage else None,
                "total_tokens": response.usage.total_tokens if response.usage else None,
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason if response.choices else None
            }
            
            # Log latency information
            print(f"⏱️  OpenAI API Latency: {latency:.2f}s")
            if response.usage:
                print(f"📊 Tokens: {result['input_tokens']} input, {result['output_tokens']} output, {result['total_tokens']} total")
            
            return result
            
        except Exception as e:
            end_time = time.time()
            latency = end_time - start_time
            print(f"❌ OpenAI API Error after {latency:.2f}s: {str(e)}")
            raise Exception(f"Failed to generate hot take: {str(e)}")
    
    def generate_quick_roast(self, topic: str) -> Dict[str, Any]:
        """Generate a quick roast on any topic."""
        user_message = f"Give me a quick hot take roast about: {topic}"
        
        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "system",
                        "content": self.chad_prompt + "\n\nKeep this response short and punchy - just 2-3 sentences max."
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                verbosity="low",
                #max_completion_tokens=2000,
                service_tier="priority"
            )
            
            end_time = time.time()
            latency = end_time - start_time
            
            result = {
                "roast": response.choices[0].message.content.strip(),
                "latency_seconds": latency,
                "input_tokens": response.usage.prompt_tokens if response.usage else None,
                "output_tokens": response.usage.completion_tokens if response.usage else None,
                "total_tokens": response.usage.total_tokens if response.usage else None,
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason if response.choices else None
            }
            
            # Log latency information
            print(f"⏱️  OpenAI API Latency (Quick Roast): {latency:.2f}s")
            if response.usage:
                print(f"📊 Tokens: {result['input_tokens']} input, {result['output_tokens']} output, {result['total_tokens']} total")
            
            return result
            
        except Exception as e:
            end_time = time.time()
            latency = end_time - start_time
            print(f"❌ OpenAI API Error after {latency:.2f}s: {str(e)}")
            raise Exception(f"Failed to generate quick roast: {str(e)}")
    
    def test_connection(self) -> bool:
        """Test the OpenAI API connection."""
        start_time = time.time()
        try:
            response = self.client.chat.completions.create(
                model="gpt-5",
                messages=[{"role": "user", "content": "Test"}],
                verbosity="low",
                reasoning_effort="minimal",
                max_completion_tokens=50,
                service_tier="priority"
            )
            end_time = time.time()
            latency = end_time - start_time
            print(f"⏱️  OpenAI Connection Test Latency: {latency:.2f}s")
            return True
        except Exception as e:
            end_time = time.time()
            latency = end_time - start_time
            print(f"❌ OpenAI Connection Test Failed after {latency:.2f}s: {str(e)}")
            return False
