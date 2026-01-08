"""
Debug script to test post generation engine.
Configure the settings at the top to specify which posts to generate.
"""

import sys
import json
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.post_generation_engine import create_engine

# ============================================================================
# CONFIGURATION - Modify these settings to specify which posts to generate
# ============================================================================

# Path to PromoCanon directory
CANON_DIRECTORY = "PromoCanon_Show_33adb096b04ecd6b23ce9341160b199f2d489311_1_100"

# Generation mode: Choose one of the following:
#   "episode" - Generate for specific episode(s)
#   "character" - Generate from character perspective
#   "top_engaging" - Get top N most engaging
#   "episode_range" - Generate for episode range
GENERATION_MODE = "character"

# Settings for "episode" mode
EPISODE_NUM = 7  # Episode number to generate
EPISODE_CHARACTER = None  # Character perspective (None for generic, or "Nora Smith", etc.)
PROMPTS_PER_CLIFFHANGER = 3  # Number of prompts to generate per cliffhanger (2-3 recommended)

# Settings for "character" mode
CHARACTER_NAME = "Nora Smith"  # Character name
CHARACTER_MIN_EPISODE = 1
CHARACTER_MAX_EPISODE = 10
CHARACTER_LIMIT = 5

# Settings for "top_engaging" mode
TOP_COUNT = 5  # Number of prompts to generate
TOP_MIN_EPISODE = 1
TOP_MAX_EPISODE = 20

# Settings for "episode_range" mode
RANGE_START = 1
RANGE_END = 10
RANGE_CHARACTERS_PER_CLIFFHANGER = 1

# Output settings
OUTPUT_FORMAT = "detailed"  # "detailed" or "json" or "simple"
SAVE_TO_FILE = False  # Set to True to save output to file
OUTPUT_FILE = "generated_prompts.json"

# ============================================================================
# Main execution
# ============================================================================

def print_prompt_detailed(prompt, index=None):
    """Print prompt in detailed format"""
    prefix = f"{index}. " if index is not None else ""
    print(f"\n{'='*80}")
    print(f"{prefix}PROMPT {index if index is not None else ''}")
    print(f"{'='*80}")
    print(f"Episode: {prompt.get('episode', 'N/A')}")
    print(f"Cliffhanger Title: {prompt.get('cliffhanger_title', 'N/A')}")
    print(f"Location: {prompt.get('location', 'N/A')}")
    print(f"Mood: {prompt.get('mood', 'N/A')}")
    if prompt.get('perspective_character'):
        print(f"Perspective: {prompt['perspective_character']}")
    
    print(f"\n--- VEO Prompt ---")
    print(prompt.get('prompt', 'N/A'))
    
    print(f"\n--- Components ---")
    components = prompt.get('components', {})
    print(f"Scene: {components.get('scene', 'N/A')}")
    print(f"Characters: {', '.join(components.get('characters', []))}")
    if components.get('descriptions'):
        print(f"Character Descriptions:")
        for char, desc in components['descriptions'].items():
            print(f"  - {char}: {desc[:100]}...")
    
    print(f"\n--- Scene Data ---")
    scene_data = prompt.get('scene_data', {})
    print(f"Key Moment: {scene_data.get('key_moment', 'N/A')[:150]}...")
    print(f"Visual Elements: {scene_data.get('visual_elements', {})}")


def print_prompt_simple(prompt, index=None):
    """Print prompt in simple format"""
    prefix = f"{index}. " if index is not None else ""
    summary = f"Episode {prompt.get('episode', 'N/A')}: {prompt.get('location', 'N/A')} - {prompt.get('mood', 'N/A')}"
    if prompt.get('perspective_character'):
        summary += f" [{prompt['perspective_character']}]"
    print(f"{prefix}{summary}")
    print(f"   Prompt: {prompt.get('prompt', 'N/A')[:150]}...")


def main():
    """Main execution function"""
    print("="*80)
    print("POST GENERATION ENGINE - DEBUG SCRIPT")
    print("="*80)
    print(f"Canon Directory: {CANON_DIRECTORY}")
    print(f"Generation Mode: {GENERATION_MODE}")
    print("="*80)
    
    # Initialize engine
    try:
        engine = create_engine(CANON_DIRECTORY)
        print(f"\n✓ Engine initialized successfully")
        print(f"✓ Available characters: {', '.join(engine.get_available_characters())}")
    except Exception as e:
        print(f"\n✗ Error initializing engine: {e}")
        return
    
    # Generate prompts based on mode
    prompts = []
    
    try:
        if GENERATION_MODE == "episode":
            print(f"\nGenerating prompts for Episode {EPISODE_NUM}...")
            if EPISODE_CHARACTER:
                print(f"  Character perspective: {EPISODE_CHARACTER}")
            print(f"  Prompts per cliffhanger: {PROMPTS_PER_CLIFFHANGER}")
            prompts = engine.generate_prompts_for_cliffhanger(
                episode_num=EPISODE_NUM,
                perspective_character=EPISODE_CHARACTER,
                prompts_per_cliffhanger=PROMPTS_PER_CLIFFHANGER
            )
        
        elif GENERATION_MODE == "character":
            print(f"\nGenerating prompts from {CHARACTER_NAME}'s perspective...")
            print(f"  Episode range: {CHARACTER_MIN_EPISODE}-{CHARACTER_MAX_EPISODE}")
            print(f"  Limit: {CHARACTER_LIMIT}")
            prompts = engine.generate_prompts_for_character(
                character_name=CHARACTER_NAME,
                min_episode=CHARACTER_MIN_EPISODE,
                max_episode=CHARACTER_MAX_EPISODE,
                limit=CHARACTER_LIMIT
            )
        
        elif GENERATION_MODE == "top_engaging":
            print(f"\nGenerating top {TOP_COUNT} most engaging prompts...")
            print(f"  Episode range: {TOP_MIN_EPISODE}-{TOP_MAX_EPISODE}")
            prompts = engine.generate_top_engaging_prompts(
                count=TOP_COUNT,
                min_episode=TOP_MIN_EPISODE,
                max_episode=TOP_MAX_EPISODE
            )
        
        elif GENERATION_MODE == "episode_range":
            print(f"\nGenerating prompts for episodes {RANGE_START}-{RANGE_END}...")
            print(f"  Characters per cliffhanger: {RANGE_CHARACTERS_PER_CLIFFHANGER}")
            prompts = engine.generate_prompts_for_episode_range(
                start_episode=RANGE_START,
                end_episode=RANGE_END,
                characters_per_cliffhanger=RANGE_CHARACTERS_PER_CLIFFHANGER
            )
        
        else:
            print(f"\n✗ Unknown generation mode: {GENERATION_MODE}")
            print("  Valid modes: 'episode', 'character', 'top_engaging', 'episode_range'")
            return
        
        print(f"\n✓ Generated {len(prompts)} prompts")
        
    except Exception as e:
        print(f"\n✗ Error generating prompts: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Display prompts
    if not prompts:
        print("\n⚠ No prompts generated. Check your configuration.")
        return
    
    print(f"\n{'='*80}")
    print(f"GENERATED PROMPTS ({len(prompts)} total)")
    print(f"{'='*80}")
    
    if OUTPUT_FORMAT == "json":
        # JSON output
        output_data = {
            'generation_mode': GENERATION_MODE,
            'config': {
                'canon_directory': CANON_DIRECTORY,
                'episode_num': EPISODE_NUM if GENERATION_MODE == "episode" else None,
                'character_name': CHARACTER_NAME if GENERATION_MODE == "character" else None,
                'top_count': TOP_COUNT if GENERATION_MODE == "top_engaging" else None,
            },
            'prompts': prompts
        }
        output = json.dumps(output_data, indent=2)
        print(output)
        
        if SAVE_TO_FILE:
            with open(OUTPUT_FILE, 'w') as f:
                f.write(output)
            print(f"\n✓ Saved to {OUTPUT_FILE}")
    
    elif OUTPUT_FORMAT == "simple":
        # Simple output
        for i, prompt in enumerate(prompts, 1):
            print_prompt_simple(prompt, index=i)
    
    else:  # detailed
        # Detailed output
        for i, prompt in enumerate(prompts, 1):
            print_prompt_detailed(prompt, index=i)
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total prompts generated: {len(prompts)}")
    
    # Episode distribution
    episodes = [p.get('episode') for p in prompts if p.get('episode')]
    if episodes:
        print(f"Episode range: {min(episodes)} - {max(episodes)}")
        print(f"Unique episodes: {len(set(episodes))}")
    
    # Character distribution
    characters = []
    for p in prompts:
        chars = p.get('components', {}).get('characters', [])
        characters.extend(chars)
    if characters:
        unique_chars = list(set(characters))
        print(f"Characters featured: {', '.join(unique_chars)}")
    
    # Perspective distribution
    perspectives = [p.get('perspective_character') for p in prompts if p.get('perspective_character')]
    if perspectives:
        print(f"Character perspectives: {', '.join(set(perspectives))}")
    
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
