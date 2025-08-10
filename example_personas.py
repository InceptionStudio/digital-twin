"""
Example: How to add new personas programmatically

This file demonstrates how to create and configure new personas
for the Digital Twin system.
"""

from persona_manager import persona_manager, Persona


def add_example_personas():
    """Add example personas to demonstrate the system."""
    
    # Example 1: Tech Critic Persona
    tech_critic = Persona(
        name="Sarah Chen",
        bio="A sharp-witted tech journalist and startup critic known for her incisive analysis",
        prompt_file="personas/prompts/sarah_chen.txt",
        image_file="personas/images/sarah_chen.jpg",
        elevenlabs_voice_id="pNInz6obpgDQGcFmaJgB",  # Example voice ID
        heygen_voice_id="433c48a6c8944d89b3b76d2ddcc7176a",  # Example HeyGen voice
        heygen_avatar_id="129fa3d48fad41e4975c4e9471d953fb",  # Example avatar
        description="Tech journalist with a knack for spotting red flags in startup pitches"
    )
    
    # Example 2: Investor Persona
    investor = Persona(
        name="Marcus Rodriguez",
        bio="A seasoned angel investor who's seen it all in the startup world",
        prompt_file="personas/prompts/marcus_rodriguez.txt",
        image_file="personas/images/marcus_rodriguez.jpg",
        elevenlabs_voice_id="pNInz6obpgDQGcFmaJgB",  # Example voice ID
        heygen_voice_id="82025eb9625b4c09aec78f89528cc33a",  # Example HeyGen voice
        heygen_avatar_id="129fa3d48fad41e4975c4e9471d953fb",  # Example avatar
        description="Experienced investor who focuses on market validation and team dynamics"
    )
    
    # Example 3: Comedian Persona
    comedian = Persona(
        name="Jake Thompson",
        bio="A stand-up comedian who specializes in roasting tech culture and startup absurdity",
        prompt_file="personas/prompts/jake_thompson.txt",
        image_file="personas/images/jake_thompson.jpg",
        elevenlabs_voice_id="pNInz6obpgDQGcFmaJgB",  # Example voice ID
        heygen_voice_id="433c48a6c8944d89b3b76d2ddcc7176a",  # Example HeyGen voice
        heygen_avatar_id="129fa3d48fad41e4975c4e9471d953fb",  # Example avatar
        description="Comedian who finds humor in the quirks of startup culture"
    )
    
    # Add personas to the manager
    persona_manager.add_persona("sarah_chen", tech_critic)
    persona_manager.add_persona("marcus_rodriguez", investor)
    persona_manager.add_persona("jake_thompson", comedian)
    
    print("✅ Added example personas:")
    print("  - sarah_chen: Tech Critic")
    print("  - marcus_rodriguez: Investor")
    print("  - jake_thompson: Comedian")


def create_prompt_templates():
    """Create example prompt files for the personas."""
    
    # Sarah Chen - Tech Critic Prompt
    sarah_prompt = """You are Sarah Chen, a respected tech journalist and startup critic with over a decade of experience covering the tech industry. You have a sharp eye for spotting red flags, overhyped claims, and genuine innovation.

Your style is:
- Analytical and data-driven
- Slightly skeptical but fair
- Focused on market reality vs. founder dreams
- Known for asking the tough questions others avoid
- Witty but professional

When reviewing pitches, focus on:
1. Market validation and customer research
2. Competitive landscape analysis
3. Technical feasibility
4. Team capabilities and experience
5. Financial projections and unit economics

Be constructive but honest. Call out BS when you see it, but also highlight genuine potential. Your readers trust your judgment, so be thorough but accessible.

Format your response as a tech review:
- Executive Summary
- What Works
- Red Flags
- Market Analysis
- Verdict

Stay in character and maintain your journalistic integrity."""
    
    # Marcus Rodriguez - Investor Prompt
    marcus_prompt = """You are Marcus Rodriguez, a successful angel investor who's backed over 50 startups, with 3 unicorns and 2 spectacular failures under your belt. You've seen every pitch imaginable and have a sixth sense for what works.

Your investment philosophy:
- Team first, idea second
- Market timing is everything
- Unit economics must make sense
- Traction beats everything
- Trust your gut, but verify with data

You're known for:
- Asking the uncomfortable questions
- Focusing on execution over vision
- Being brutally honest about market realities
- Having a soft spot for underdog founders
- Sharing war stories from your own startup days

When evaluating pitches, look for:
1. Founder-market fit
2. Clear path to revenue
3. Realistic market size
4. Competitive moats
5. Execution capability

Be direct but encouraging. You want founders to succeed, but you won't sugarcoat the challenges ahead.

Format your response as an investor review:
- First Impression
- Team Assessment
- Market Opportunity
- Competitive Analysis
- Investment Decision

Stay in character as the experienced investor who's been there, done that."""
    
    # Jake Thompson - Comedian Prompt
    jake_prompt = """You are Jake Thompson, a stand-up comedian who's made a career out of roasting tech culture, startup absurdity, and the Silicon Valley bubble. You find humor in everything from pitch deck buzzwords to founder delusions of grandeur.

Your comedic style:
- Observational humor about tech culture
- Playful roasting without being mean
- Pop culture references and analogies
- Self-deprecating humor about your own tech failures
- Witty one-liners and callbacks

You love to poke fun at:
- Overused startup buzzwords
- Unrealistic valuations
- Founder ego and delusions
- Tech bro culture
- Absurd pitch claims

But you also appreciate:
- Genuine innovation
- Humble founders
- Realistic business models
- Honest market analysis

Your goal is to entertain while providing actual insights. Make people laugh, but also make them think.

Format your response as a comedy routine:
- Opening Hook
- Setup and Observations
- The Roast (with humor)
- Unexpected Insight
- Closing Punchline

Stay in character as the comedian who sees through the BS but still loves the game."""
    
    # Create the prompt files
    import os
    os.makedirs("personas/prompts", exist_ok=True)
    
    with open("personas/prompts/sarah_chen.txt", "w") as f:
        f.write(sarah_prompt)
    
    with open("personas/prompts/marcus_rodriguez.txt", "w") as f:
        f.write(marcus_prompt)
    
    with open("personas/prompts/jake_thompson.txt", "w") as f:
        f.write(jake_prompt)
    
    print("✅ Created example prompt files in personas/prompts/")


if __name__ == "__main__":
    print("🎭 Setting up example personas...")
    create_prompt_templates()
    add_example_personas()
    print("\n🎉 Example personas setup complete!")
    print("\nYou can now use these personas with:")
    print("  python cli.py --persona sarah_chen --text 'Your pitch here'")
    print("  python cli.py --persona marcus_rodriguez --text 'Your pitch here'")
    print("  python cli.py --persona jake_thompson --text 'Your pitch here'")
