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
    
    def _generate_response(self, 
                          input_text: str, 
                          user_message: str,
                          response_type: str = "hot_take",
                          persona_id: str = "chad_goldstein",
                          system_extra: str = "") -> Dict[str, Any]:
        """
        Common method to generate responses using OpenAI API.
        
        Args:
            input_text: The main input text (pitch transcript or topic)
            user_message: The complete user message to send to the API
            response_type: Type of response ("hot_take" or "roast")
            persona_id: Persona ID to use
            system_extra: Extra instructions for the system message
            
        Returns:
            Dictionary with response data
        """
        # Get persona information
        persona = persona_manager.get_persona(persona_id)
        if not persona:
            print(f"⚠️  WARNING: Persona '{persona_id}' not found. Using Chad Goldstein as fallback.")
            persona_id = "chad_goldstein"
            persona = persona_manager.get_persona(persona_id)
        
        # Get persona's prompt
        persona_prompt = self._get_persona_prompt(persona_id)
        
        start_time = time.time()
        
        try:
            # Construct system message with any extra instructions
            system_message = persona_prompt
            if system_extra:
                system_message += f"\n\n{system_extra}"
            
            response = self.client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "system",
                        "content": system_message
                    },
                    {
                        "role": "user", 
                        "content": user_message
                    }
                ],
                verbosity="low",
                service_tier="priority"
            )
            
            end_time = time.time()
            latency = end_time - start_time
            
            # Determine the result key based on response type
            result_key = "roast" if response_type == "roast" else "hot_take"
            
            result = {
                result_key: response.choices[0].message.content.strip(),
                "latency_seconds": latency,
                "input_tokens": response.usage.prompt_tokens if response.usage else None,
                "output_tokens": response.usage.completion_tokens if response.usage else None,
                "total_tokens": response.usage.total_tokens if response.usage else None,
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason if response.choices else None
            }
            
            # Log latency information
            log_prefix = "Quick Roast" if response_type == "roast" else "Hot Take"
            print(f"⏱️  OpenAI API Latency ({log_prefix}): {latency:.2f}s")
            if response.usage:
                print(f"📊 Tokens: {result['input_tokens']} input, {result['output_tokens']} output, {result['total_tokens']} total")
            
            return result
            
        except Exception as e:
            end_time = time.time()
            latency = end_time - start_time
            print(f"❌ OpenAI API Error after {latency:.2f}s: {str(e)}")
            raise Exception(f"Failed to generate {response_type}: {str(e)}")
    
    def _build_user_message(self, input_text: str, response_type: str, context: Optional[str] = None, persona_name: str = "Chad", max_duration: str = "20 seconds", audio_tags: bool = False) -> str:
        """
        Build the user message for the API call.
        
        Args:
            input_text: The main input text
            response_type: Type of response ("hot_take" or "roast")
            context: Optional additional context
            persona_name: Name of the persona
            max_duration: Maximum duration for the response
            audio_tags: Whether to include audio tags for dramatic effect
            
        Returns:
            Complete user message string
        """
        # Build the base message based on response type
        if response_type == "hot_take":
            user_message = f"Here's a startup pitch I just heard:\n\n{input_text}"
            if context:
                user_message += f"\n\nAdditional context: {context}"
            user_message += f"\n\nGive me your hot take, {persona_name}! Keep it to {max_duration} MAX."
        else:  # roast
            user_message = f"Give me a quick hot take roast about: {input_text}"
            user_message += f"\n\nKeep it to {max_duration} MAX."
        
        # Add common speech formatting instructions
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

Replace acronyms with their sounded-out versions, like "AI" (as "a-eye") or "AWS" (as "a-double you-s")."""
        
        # Add audio tags instruction if requested
        if audio_tags:
            user_message += f"""

Add audio tags in square brackets to make it sound more realistic and for dramatic effect. Some examples of tags:
* [happy]
* [energetic]
* [excited]
* [thoughtful]
* [sarcastic]
* [curious]
* [mischievously]
* [annoyed]
* [woo]
* [chuckles]
* [snorts]
* [laughs]
* [laughs harder]
* [starts laughing]
* [exhales sharply]
* [pauses]
* [stammers]
* [rushed]
* [gasp]
* [sigh]
* [gulps]
* [whispering]
* [shouting]
* [quietly]
* [loudly]
"""
        
        return user_message
    
    def generate_hot_take(self, pitch_transcript: str, context: Optional[str] = None, persona_id: str = "chad_goldstein", audio_tags: bool = False) -> Dict[str, Any]:
        """Generate a hot take response based on the pitch transcript."""
        # Get persona for name
        persona = persona_manager.get_persona(persona_id)
        persona_name = persona.name if persona else "Chad"
        
        user_message = self._build_user_message(
            input_text=pitch_transcript,
            response_type="hot_take",
            context=context,
            persona_name=persona_name,
            max_duration="20 seconds",
            audio_tags=audio_tags
        )
        
        return self._generate_response(
            input_text=pitch_transcript,
            user_message=user_message,
            response_type="hot_take",
            persona_id=persona_id
        )
    
    def generate_quick_roast(self, topic: str, persona_id: str = "chad_goldstein", audio_tags: bool = False) -> Dict[str, Any]:
        """Generate a quick roast on any topic."""
        # Get persona for name
        persona = persona_manager.get_persona(persona_id)
        persona_name = persona.name if persona else "Chad"
        
        user_message = self._build_user_message(
            input_text=topic,
            response_type="roast",
            persona_name=persona_name,
            max_duration="15 seconds",
            audio_tags=audio_tags
        )
        
        return self._generate_response(
            input_text=topic,
            user_message=user_message,
            response_type="roast",
            persona_id=persona_id,
            system_extra="Keep this response short and punchy - just 2-3 sentences max."
        )
    
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
