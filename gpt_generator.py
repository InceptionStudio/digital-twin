import openai
from typing import Optional
from config import Config

class HotTakeGenerator:
    def __init__(self):
        self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        self.chad_prompt = self._load_chad_prompt()
    
    def _load_chad_prompt(self) -> str:
        """Load the Chad Goldstein character prompt from file."""
        try:
            with open("chadprompt.txt", "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            # Fallback prompt if file not found
            return """You are "Chad Goldstein, General Partner at Bling Capital Partners" — a flamboyant, self-congratulatory, and unreasonably confident venture capitalist who delivers pitch and pitch deck critiques with a mix of ruthless candor, misguided self-comparisons to Warren Buffett, and unfiltered tech-bro energy.

You are almost like Kevin O'Leary from Shark Tank, except you've had one exit, three podcasts, and a six-figure follower count on LinkedIn, so you consider yourself "basically a thought leader with liquidity." You're funny, sharp, and occasionally insightful — but you never let humility get in the way of your hot takes.

Format your response like an investor-style commentary:
* Opening one-liner or metaphor-heavy quip
* Highlights — what works in the pitch and deck
* Roast — what's questionable, missing, or overhyped
* Closing — your "verdict"

Stay in character the entire time. Be witty, self-deluded, and entertaining."""
    
    def generate_hot_take(self, pitch_transcript: str, context: Optional[str] = None) -> str:
        """Generate a hot take response based on the pitch transcript."""
        
        # Construct the user message
        user_message = f"Here's a startup pitch I just heard:\n\n{pitch_transcript}"
        
        if context:
            user_message += f"\n\nAdditional context: {context}"
        
        user_message += "\n\nGive me your hot take, Chad!"
        
        try:
            # Note: Using gpt-4 as GPT-5 may not be available yet
            # Update model name when GPT-5 becomes available
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
                max_tokens=800,
                temperature=0.8,  # Higher temperature for more creative/entertaining responses
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise Exception(f"Failed to generate hot take: {str(e)}")
    
    def generate_quick_roast(self, topic: str) -> str:
        """Generate a quick roast on any topic."""
        user_message = f"Give me a quick hot take roast about: {topic}"
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",  # Change to "gpt-5" when available
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
                max_tokens=200,
                temperature=0.9,
                presence_penalty=0.2
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise Exception(f"Failed to generate quick roast: {str(e)}")
    
    def test_connection(self) -> bool:
        """Test the OpenAI API connection."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5
            )
            return True
        except Exception:
            return False
