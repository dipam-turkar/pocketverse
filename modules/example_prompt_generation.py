"""
Example usage of the post generation engine for VEO prompts.
Demonstrates how to generate prompts from cliffhangers.
"""

from .post_generation_engine import create_engine


def example_basic_usage():
    """Basic example of generating prompts"""
    # Initialize engine with PromoCanon directory
    canon_dir = "PromoCanon_Show_33adb096b04ecd6b23ce9341160b199f2d489311_1_100"
    engine = create_engine(canon_dir)
    
    # Generate prompts for a specific episode
    prompts = engine.generate_prompts_for_cliffhanger(episode_num=7)
    
    print("Prompts for Episode 7:")
    for prompt in prompts:
        print(f"\n{engine.get_prompt_summary(prompt)}")
        print(f"VEO Prompt: {prompt['prompt']}")
        print(f"Components: {prompt['components']}")


def example_character_perspective():
    """Example of generating prompts from character perspectives"""
    canon_dir = "PromoCanon_Show_33adb096b04ecd6b23ce9341160b199f2d489311_1_100"
    engine = create_engine(canon_dir)
    
    # Generate prompts from Nora's perspective
    prompts = engine.generate_prompts_for_character(
        character_name="Nora Smith",
        min_episode=1,
        max_episode=20,
        limit=5
    )
    
    print("\nPrompts from Nora's perspective:")
    for prompt in prompts:
        print(f"\nEpisode {prompt['episode']}: {prompt['cliffhanger_title']}")
        print(f"Prompt: {prompt['prompt']}")


def example_top_engaging():
    """Example of getting top engaging prompts"""
    canon_dir = "PromoCanon_Show_33adb096b04ecd6b23ce9341160b199f2d489311_1_100"
    engine = create_engine(canon_dir)
    
    # Get top 10 most engaging prompts
    prompts = engine.generate_top_engaging_prompts(count=10)
    
    print("\nTop 10 Engaging Prompts:")
    for i, prompt in enumerate(prompts, 1):
        print(f"\n{i}. {engine.get_prompt_summary(prompt)}")
        print(f"   Location: {prompt.get('location', 'N/A')}")
        print(f"   Mood: {prompt.get('mood', 'N/A')}")


def example_episode_range():
    """Example of generating prompts for an episode range"""
    canon_dir = "PromoCanon_Show_33adb096b04ecd6b23ce9341160b199f2d489311_1_100"
    engine = create_engine(canon_dir)
    
    # Generate prompts for episodes 1-10, multiple character perspectives
    prompts = engine.generate_prompts_for_episode_range(
        start_episode=1,
        end_episode=10,
        characters_per_cliffhanger=2  # Generate from 2 character perspectives
    )
    
    print(f"\nGenerated {len(prompts)} prompts for episodes 1-10:")
    for prompt in prompts[:5]:  # Show first 5
        print(f"\n{engine.get_prompt_summary(prompt)}")
        print(f"Full prompt: {prompt['prompt'][:200]}...")


def example_specific_cliffhanger():
    """Example of generating prompt for a specific cliffhanger scenario"""
    canon_dir = "PromoCanon_Show_33adb096b04ecd6b23ce9341160b199f2d489311_1_100"
    engine = create_engine(canon_dir)
    
    # Get cliffhangers for episode 7 (airport scene example)
    prompts = engine.generate_prompts_for_cliffhanger(
        episode_num=7,
        perspective_character="Nora Smith"
    )
    
    if prompts:
        prompt = prompts[0]
        print("\nExample: Airport scene from Nora's perspective")
        print(f"Episode: {prompt['episode']}")
        print(f"Cliffhanger: {prompt['cliffhanger_title']}")
        print(f"\nVEO Prompt:\n{prompt['prompt']}")
        print(f"\nComponents:")
        print(f"  Scene: {prompt['components']['scene']}")
        print(f"  Characters: {', '.join(prompt['components']['characters'])}")
        print(f"  Location: {prompt.get('location', 'N/A')}")
        print(f"  Mood: {prompt.get('mood', 'N/A')}")


if __name__ == "__main__":
    print("=== Post Generation Engine Examples ===\n")
    
    print("1. Basic Usage:")
    example_basic_usage()
    
    print("\n\n2. Character Perspective:")
    example_character_perspective()
    
    print("\n\n3. Top Engaging Prompts:")
    example_top_engaging()
    
    print("\n\n4. Episode Range:")
    example_episode_range()
    
    print("\n\n5. Specific Cliffhanger:")
    example_specific_cliffhanger()
