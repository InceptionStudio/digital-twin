import openai
import time
from typing import Optional, Dict, Any
from config import Config
from persona_manager import persona_manager

class HotTakeGenerator:
    def __init__(self):
        self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
    
    def _get_persona_prompt(self, persona_id: str = "chad_goldstein") -> str:
        """Get the persona's prompt content."""
        prompt_content = persona_manager.get_prompt_content(persona_id)
        if prompt_content:
            return prompt_content
        
        # Fallback to Chad's prompt if persona not found
        return self._load_chad_prompt()
    
    def _load_chad_prompt(self) -> str:
        """Load the Chad Goldstein character prompt from file."""
        try:
            # Try to get Chad's prompt from persona manager first
            prompt_content = persona_manager.get_prompt_content("chad_goldstein")
            if prompt_content:
                return prompt_content
            
            # Fallback to direct file read
            with open("personas/prompts/chad_goldstein.txt", "r", encoding="utf-8") as f:
                prompt = f.read().strip()
                if not prompt:
                    print("⚠️  WARNING: personas/prompts/chad_goldstein.txt file is empty!")
                    return self._get_fallback_prompt()
                return prompt
        except FileNotFoundError:
            print("⚠️  WARNING: personas/prompts/chad_goldstein.txt file not found! Using fallback prompt.")
            return self._get_fallback_prompt()
        except Exception as e:
            print(f"⚠️  WARNING: Error loading personas/prompts/chad_goldstein.txt: {str(e)}. Using fallback prompt.")
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
    
    def generate_hot_take(self, pitch_transcript: str, context: Optional[str] = None, persona_id: str = "chad_goldstein") -> Dict[str, Any]:
        """Generate a hot take response based on the pitch transcript."""
        
        # Get persona information
        persona = persona_manager.get_persona(persona_id)
        if not persona:
            print(f"⚠️  WARNING: Persona '{persona_id}' not found. Using Chad Goldstein as fallback.")
            persona_id = "chad_goldstein"
            persona = persona_manager.get_persona(persona_id)
        
        # Get persona's prompt
        persona_prompt = self._get_persona_prompt(persona_id)
        
        # Construct the user message
        user_message = f"Here's a startup pitch I just heard:\n\n{pitch_transcript}"
        
        if context:
            user_message += f"\n\nAdditional context: {context}"
        
        user_message += f"\n\nGive me your hot take, {persona.name}! Keep it to 20 seconds MAX."
        user_message += f"""

Be sure to generate only the spoken words. Generate sentences that sound natural when spoken.
Incorporate Punctuation Marks:
* Commas (,): Create shorter breaks.
* Periods (.): Introduce longer breaks with downward inflection.

Write out numbers and avoid abbreviations for clarity. For example:
* "2012" becomes "twenty twelve."
* "3/8" becomes "three eighths of an inch."
* "01:18" becomes "one minute and eighteen seconds."
* "10-19-2016" becomes "October nineteenth, two thousand sixteen."
* "150th CT NE, Redmond, WA" becomes "150th Court Northeast, Redmond, Washington."

Replace acronyms with their sounded-out versions, like "AI" (as "a-eye") or "AWS" (as "a-double you-s").
"""
        
        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "system",
                        "content": persona_prompt
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
    
    def generate_quick_roast(self, topic: str, persona_id: str = "chad_goldstein") -> Dict[str, Any]:
        """Generate a quick roast on any topic."""
        # Get persona information
        persona = persona_manager.get_persona(persona_id)
        if not persona:
            print(f"⚠️  WARNING: Persona '{persona_id}' not found. Using Chad Goldstein as fallback.")
            persona_id = "chad_goldstein"
            persona = persona_manager.get_persona(persona_id)
        
        # Get persona's prompt
        persona_prompt = self._get_persona_prompt(persona_id)
        
        user_message = f"Give me a quick hot take roast about: {topic}"
        user_message += f"\n\nKeep it to 15 seconds MAX."
        
        user_message += f"""

Be sure to generate only the spoken words. Generate sentences that sound natural when spoken.
Incorporate Punctuation Marks:
* Commas (,): Create shorter breaks.
* Periods (.): Introduce longer breaks with downward inflection.

Write out numbers and avoid abbreviations for clarity. For example:
* "2012" becomes "twenty twelve."
* "3/8" becomes "three eighths of an inch."
* "01:18" becomes "one minute and eighteen seconds."
* "10-19-2016" becomes "October nineteenth, two thousand sixteen."
* "150th CT NE, Redmond, WA" becomes "150th Court Northeast, Redmond, Washington."

Replace acronyms with their sounded-out versions, like "AI" (as "a-eye") or "AWS" (as "a-double you-s").
"""

        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "system",
                        "content": persona_prompt + "\n\nKeep this response short and punchy - just 2-3 sentences max."
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
