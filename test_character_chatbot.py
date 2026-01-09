#!/usr/bin/env python3
"""
Test Script for Character Chatbot Flow

This script tests the character chatbot with various sample posts and user comments
to verify that characters respond appropriately without spoilers.

Usage:
    python test_character_chatbot.py
    
    # Test specific scenario
    python test_character_chatbot.py --scenario 1
    
    # Test specific character
    python test_character_chatbot.py --character nora_smith
    
    # Test specific template
    python test_character_chatbot.py --template v2
"""

import argparse
import json
import sys
from typing import Dict, List

# Add project root to path
sys.path.insert(0, '.')

# =============================================================================
# SAMPLE TEST SCENARIOS
# =============================================================================

TEST_SCENARIOS: List[Dict] = [
    # =========================================================================
    # SCENARIO 1: Nora at Beat 1 (Early story - user just started)
    # =========================================================================
    {
        "id": 1,
        "name": "Nora - Early Story (EP5)",
        "description": "User is early in the story, hasn't seen the twin swap yet",
        "character_id": "nora_smith",
        "user_episode": 5,
        "post_episode": 4,
        "post": {
            "image_scene": "Elegant hotel lobby at Hotel Finest. Nora Smith stands near the elevator, wearing a simple but expensive dress. Her expression is calm, almost bored. Justin Hunt watches her from across the lobby with suspicion. The lighting is warm evening light through floor-to-ceiling windows.",
            "title": "Just another day avoiding unnecessary conversations",
            "caption": "Some people think they're important enough to demand attention. They're not.",
            "content": "Checked into my room. The view is nice. I could sleep for days."
        },
        "user_comments": [
            "Nora, why did you come back to the US? Is it really just for the engagement?",
            "That guy watching you looks intense. Do you know him?",
            "Where's Cherry? Is she with you at the hotel?",
            "I heard you used to be different before you went abroad. What happened?"
        ]
    },
    
    # =========================================================================
    # SCENARIO 2: Nora at Beat 3 (Post Surgery - Angela exposed)
    # =========================================================================
    {
        "id": 2,
        "name": "Nora - After Angela's Exposure (EP25)",
        "description": "User has seen Angela get exposed, surgery completed",
        "character_id": "nora_smith",
        "user_episode": 25,
        "post_episode": 23,
        "post": {
            "image_scene": "Hospital corridor outside operating room. Angela Smith stands humiliated, her face red with embarrassment, as medical staff ignore her. In the background, the OR doors are closed. The lighting is harsh fluorescent hospital lighting.",
            "title": "Some people learn the hard way",
            "caption": "Lying about things you don't understand tends to backfire.",
            "content": "Angela claimed she contacted a surgeon. She didn't. I watched. It was satisfying."
        },
        "user_comments": [
            "Nora, do you think Justin suspects you're Athena now?",
            "Angela totally deserved that! How did it feel watching her get exposed?",
            "Wait, are YOU the surgeon everyone is looking for?!",
            "What's your relationship with Justin like now after all this?"
        ]
    },
    
    # =========================================================================
    # SCENARIO 3: Justin at Beat 2 (Confused about Pete)
    # =========================================================================
    {
        "id": 3,
        "name": "Justin - Confused About Son (EP18)",
        "description": "Justin is confused by Pete's behavior changes (it's actually Cherry)",
        "character_id": "justin_hunt",
        "user_episode": 18,
        "post_episode": 17,
        "post": {
            "image_scene": "Luxurious penthouse study. Justin Hunt sits at his desk, papers scattered, looking troubled. A child's drawing is visible on the desk. The room is dimly lit by a desk lamp, creating a contemplative atmosphere.",
            "title": "Children are... unpredictable",
            "caption": "My son has been different lately. I can't explain it.",
            "content": "Pete answered that Tom Cruise was the first president. I had to fire both tutors. Something is very wrong."
        },
        "user_comments": [
            "Justin, have you considered that maybe Pete is just going through a phase?",
            "That's hilarious about Tom Cruise! Kids say the funniest things.",
            "Do you think Ms. Smith has something to do with Pete's changes?",
            "Maybe you should spend more time with him instead of working?"
        ]
    },
    
    # =========================================================================
    # SCENARIO 4: Justin at Beat 4 (New York, Growing feelings)
    # =========================================================================
    {
        "id": 4,
        "name": "Justin - New York Surgery Deal (EP40)",
        "description": "Justin made a deal with Nora, feelings developing",
        "character_id": "justin_hunt",
        "user_episode": 40,
        "post_episode": 38,
        "post": {
            "image_scene": "Hunt family estate in New York. Grand entrance hall with marble floors. Justin stands in a tailored suit, looking out a window at the grounds. His expression is softer than usual, almost contemplative. Afternoon sunlight streams through tall windows.",
            "title": "Debts and obligations",
            "caption": "I made a deal. I intend to honor it.",
            "content": "Ms. Smith saved my grandmother. In exchange, I'll help her find her son. A man keeps his word."
        },
        "user_comments": [
            "Justin, are you falling for Nora? Be honest!",
            "Do you really think you'll find her son?",
            "What do you think of Nora's medical skills? Pretty impressive, right?",
            "Your grandmother is lucky. Nora seems like an amazing person."
        ]
    },
    
    # =========================================================================
    # SCENARIO 5: Nora - User trying to fish for spoilers
    # =========================================================================
    {
        "id": 5,
        "name": "Nora - Spoiler Fishing (EP15)",
        "description": "User at EP15 trying to get Nora to reveal future events",
        "character_id": "nora_smith",
        "user_episode": 15,
        "post_episode": 14,
        "post": {
            "image_scene": "Hotel room balcony at night. Nora sits in a chair, looking at the city skyline. Cherry is asleep inside, visible through the glass door. Nora's expression is distant, thoughtful. City lights twinkle in the background.",
            "title": "Quiet nights",
            "caption": "She's sleeping. I should be too.",
            "content": "Aunt Irene needs surgery. Only one person can help her. The universe has a sense of humor."
        },
        "user_comments": [
            "Nora, will you ever find your son? I need to know!",
            "Are you going to operate on Irene yourself?",
            "Do you and Justin ever get together? Please tell me!",
            "I heard Pete might be your son - is that true?!"
        ]
    },
    
    # =========================================================================
    # SCENARIO 6: Justin - Early skepticism of Nora
    # =========================================================================
    {
        "id": 6,
        "name": "Justin - Skeptical of Nora (EP10)",
        "description": "Justin is still hostile and suspicious of Nora",
        "character_id": "justin_hunt",
        "user_episode": 10,
        "post_episode": 9,
        "post": {
            "image_scene": "Hotel hallway. Justin Hunt walks with purpose, his bodyguard Sean trailing behind. His expression is cold, calculating. He glances at a door - Nora's room. The lighting is neutral hotel corridor lighting.",
            "title": "Vigilance",
            "caption": "I know when someone is after something. The question is what.",
            "content": "Ms. Smith keeps appearing near my son. Coincidence? I don't believe in those."
        },
        "user_comments": [
            "Why are you so suspicious of Nora? She seems harmless.",
            "Do you think she's trying to use Pete to get to you?",
            "Justin, have you ever considered that maybe Nora has her own problems?",
            "What would you do if you found out Nora was important to Pete?"
        ]
    },
    
    # =========================================================================
    # SCENARIO 7: Nora at Beat 6 (Society established)
    # =========================================================================
    {
        "id": 7,
        "name": "Nora - Society Queen (EP70)",
        "description": "Nora is established in New York society, Carefree Pills success",
        "character_id": "nora_smith",
        "user_episode": 70,
        "post_episode": 68,
        "post": {
            "image_scene": "Glamorous New York gala. Nora in an elegant black gown, holding a champagne glass she hasn't touched. Society members surround her, but she maintains her characteristic distance. Crystal chandeliers sparkle above. Justin watches her from across the room.",
            "title": "Social obligations",
            "caption": "They wanted me here. I'm here. Can I leave now?",
            "content": "Jon Myers wanted to make me his student. I declined. Some people don't understand when they're outmatched."
        },
        "user_comments": [
            "Nora, you're so cool! How does it feel to be successful?",
            "Is Justin still pursuing you? The tension is killing me!",
            "Your mother must have been amazing. Did you inherit her skills?",
            "Do you ever get tired of pretending to be just 'Ms. Smith'?"
        ]
    },
    
    # =========================================================================
    # SCENARIO 8: Cherry/Pete Perspective (if we had them)
    # =========================================================================
    {
        "id": 8,
        "name": "Nora - Mother's Love (EP30)",
        "description": "Nora showing her softer side about Cherry",
        "character_id": "nora_smith",
        "user_episode": 30,
        "post_episode": 28,
        "post": {
            "image_scene": "Cozy hotel room. Nora sits on a bed, Cherry (actually Pete in disguise, but Nora doesn't know) curled up against her. Nora's expression is the softest we've ever seen - genuine maternal love. Warm lamplight illuminates the scene.",
            "title": "...",
            "caption": "She's growing so fast.",
            "content": "Five years I missed. I won't miss more."
        },
        "user_comments": [
            "This is so sweet! You really love Cherry, don't you?",
            "Do you ever think about your other child? The one that was taken?",
            "You seem different when you're with her. More... human.",
            "What would you do if you found your son?"
        ]
    }
]


# =============================================================================
# TEST RUNNER
# =============================================================================

def run_test_scenario(
    scenario: Dict,
    comment_index: int = 0,
    template_version: str = "v1",
    show_prompt: bool = False
) -> Dict:
    """
    Run a single test scenario.
    
    Args:
        scenario: Test scenario dictionary
        comment_index: Which user comment to test (0-3)
        template_version: Prompt template to use
        show_prompt: Whether to display the full prompt
        
    Returns:
        Result dictionary
    """
    from services.story_context import StoryContextService
    
    # Build post content (no truncation - full context is important)
    post_content = f"{scenario['post']['title']}\n\n{scenario['post']['caption']}\n\n{scenario['post']['content']}"
    if scenario['post'].get('image_scene'):
        post_content = f"[Image: {scenario['post']['image_scene']}]\n\n{post_content}"
    
    # Get user comment
    user_comment = scenario['user_comments'][comment_index % len(scenario['user_comments'])]
    
    # Get context for display
    service = StoryContextService()
    context = service.build_complete_context(
        character_id=scenario['character_id'],
        user_episode=scenario['user_episode'],
        post_episode=scenario['post_episode']
    )
    
    result = {
        "scenario_id": scenario['id'],
        "scenario_name": scenario['name'],
        "character_id": scenario['character_id'],
        "user_episode": scenario['user_episode'],
        "post_episode": scenario['post_episode'],
        "template_version": template_version,
        "user_comment": user_comment,
        "current_beat": context.get('current_beat', {}),
        "character_emotional_state": context.get('character_knowledge', {}).get('emotional_state', ''),
        "response": None,
        "prompt_length": 0,
        "error": None
    }
    
    # Try to generate response
    try:
        from services.character_chatbot import CharacterChatbot
        
        chatbot = CharacterChatbot(context_dir="context")
        
        # Build prompt for display
        prompt = chatbot.build_prompt(
            character_id=scenario['character_id'],
            user_episode=scenario['user_episode'],
            post_episode=scenario['post_episode'],
            post_content=post_content,
            user_comment=user_comment,
            template_version=template_version
        )
        result['prompt_length'] = len(prompt)
        
        if show_prompt:
            result['full_prompt'] = prompt
        
        # Generate response
        response = chatbot.generate_reply(
            character_id=scenario['character_id'],
            user_episode=scenario['user_episode'],
            post_episode=scenario['post_episode'],
            post_content=post_content,
            user_comment=user_comment,
            template_version=template_version
        )
        
        result['response'] = response
        
    except ImportError as e:
        result['error'] = f"Import error (LLM not available): {e}"
        result['response'] = "[LLM not available - run with actual credentials]"
    except Exception as e:
        result['error'] = str(e)
        import traceback
        traceback.print_exc()
    
    return result


def print_scenario_header(scenario: Dict):
    """Print a formatted scenario header."""
    print("\n" + "=" * 80)
    print(f"📺 SCENARIO {scenario['id']}: {scenario['name']}")
    print("=" * 80)
    print(f"📝 Description: {scenario['description']}")
    print(f"🎭 Character: {scenario['character_id']}")
    print(f"📍 User Episode: {scenario['user_episode']} | Post Episode: {scenario['post_episode']}")
    print("-" * 80)


def print_post(scenario: Dict):
    """Print the post details."""
    post = scenario['post']
    print("\n📷 IMAGE SCENE:")
    print(f"   {post['image_scene']}")
    print(f"\n📌 POST TITLE: {post['title']}")
    print(f"💬 CAPTION: {post['caption']}")
    print(f"📄 CONTENT: {post['content']}")


def print_result(result: Dict, comment_num: int):
    """Print a test result."""
    print(f"\n{'─' * 60}")
    print(f"💭 USER COMMENT #{comment_num + 1}:")
    print(f"   \"{result['user_comment']}\"")
    print(f"\n🎭 CHARACTER RESPONSE:")
    if result['response']:
        print(f"   \"{result['response']}\"")
    else:
        print(f"   ⚠️ No response generated")
    if result.get('error'):
        print(f"\n   ⚠️ Error: {result['error']}")
    print(f"\n📊 Stats: Prompt={result['prompt_length']} chars | Beat={result['current_beat'].get('beat_title', 'N/A')}")


def run_all_scenarios(template_version: str = "v1", test_all_comments: bool = False):
    """Run all test scenarios."""
    print("\n" + "🚀" * 40)
    print("    CHARACTER CHATBOT TEST SUITE")
    print("🚀" * 40)
    
    results = []
    
    for scenario in TEST_SCENARIOS:
        print_scenario_header(scenario)
        print_post(scenario)
        
        if test_all_comments:
            # Test all comments
            for i, comment in enumerate(scenario['user_comments']):
                result = run_test_scenario(scenario, i, template_version)
                print_result(result, i)
                results.append(result)
        else:
            # Test just the first comment
            result = run_test_scenario(scenario, 0, template_version)
            print_result(result, 0)
            results.append(result)
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    success_count = sum(1 for r in results if r['response'] and not r.get('error'))
    print(f"✅ Successful: {success_count}/{len(results)}")
    print(f"📝 Template used: {template_version}")
    
    return results


def run_single_scenario(
    scenario_id: int, 
    template_version: str = "v1",
    show_prompt: bool = False,
    test_all_comments: bool = False
):
    """Run a single scenario by ID."""
    scenario = next((s for s in TEST_SCENARIOS if s['id'] == scenario_id), None)
    
    if not scenario:
        print(f"❌ Scenario {scenario_id} not found. Available: {[s['id'] for s in TEST_SCENARIOS]}")
        return
    
    print_scenario_header(scenario)
    print_post(scenario)
    
    if test_all_comments:
        for i, comment in enumerate(scenario['user_comments']):
            result = run_test_scenario(scenario, i, template_version, show_prompt)
            print_result(result, i)
            if show_prompt and i == 0:  # Show prompt only for first
                print(f"\n📜 FULL PROMPT (first 2000 chars):")
                print(result.get('full_prompt', 'N/A')[:2000])
    else:
        result = run_test_scenario(scenario, 0, template_version, show_prompt)
        print_result(result, 0)
        if show_prompt:
            print(f"\n📜 FULL PROMPT:")
            print(result.get('full_prompt', 'N/A'))


def run_character_scenarios(character_id: str, template_version: str = "v1"):
    """Run all scenarios for a specific character."""
    character_scenarios = [s for s in TEST_SCENARIOS if s['character_id'] == character_id]
    
    if not character_scenarios:
        print(f"❌ No scenarios found for character: {character_id}")
        print(f"Available characters: {set(s['character_id'] for s in TEST_SCENARIOS)}")
        return
    
    print(f"\n🎭 Running {len(character_scenarios)} scenarios for {character_id}")
    
    for scenario in character_scenarios:
        print_scenario_header(scenario)
        print_post(scenario)
        result = run_test_scenario(scenario, 0, template_version)
        print_result(result, 0)


def interactive_test():
    """Run an interactive test session."""
    print("\n" + "🎮" * 40)
    print("    INTERACTIVE CHARACTER CHATBOT TEST")
    print("🎮" * 40)
    
    # List scenarios
    print("\n📋 Available Scenarios:")
    for s in TEST_SCENARIOS:
        print(f"   {s['id']}. {s['name']} (EP{s['user_episode']})")
    
    try:
        scenario_id = int(input("\nSelect scenario ID: "))
        scenario = next((s for s in TEST_SCENARIOS if s['id'] == scenario_id), None)
        
        if not scenario:
            print("❌ Invalid scenario")
            return
        
        print(f"\n✅ Selected: {scenario['name']}")
        print(f"\n📝 Available comments:")
        for i, c in enumerate(scenario['user_comments']):
            print(f"   {i + 1}. {c}")
        
        comment_idx = int(input("\nSelect comment (1-4): ")) - 1
        template = input("Template version (v1/v2/v3) [v1]: ").strip() or "v1"
        show_prompt = input("Show full prompt? (y/n) [n]: ").lower() == 'y'
        
        print_scenario_header(scenario)
        print_post(scenario)
        result = run_test_scenario(scenario, comment_idx, template, show_prompt)
        print_result(result, comment_idx)
        
        if show_prompt:
            print(f"\n📜 FULL PROMPT:")
            print(result.get('full_prompt', 'N/A'))
            
    except (ValueError, KeyboardInterrupt):
        print("\n👋 Exiting interactive mode")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Character Chatbot")
    parser.add_argument("--scenario", "-s", type=int, help="Run specific scenario by ID")
    parser.add_argument("--character", "-c", type=str, help="Run all scenarios for a character")
    parser.add_argument("--template", "-t", type=str, default="v1", help="Template version (v1/v2/v3)")
    parser.add_argument("--all-comments", "-a", action="store_true", help="Test all comments per scenario")
    parser.add_argument("--show-prompt", "-p", action="store_true", help="Show full prompt")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    parser.add_argument("--list", "-l", action="store_true", help="List all scenarios")
    
    args = parser.parse_args()
    
    if args.list:
        print("\n📋 Available Test Scenarios:")
        print("-" * 60)
        for s in TEST_SCENARIOS:
            print(f"  {s['id']:2d}. {s['name']}")
            print(f"      Character: {s['character_id']} | User EP: {s['user_episode']}")
            print(f"      Comments: {len(s['user_comments'])}")
            print()
    elif args.interactive:
        interactive_test()
    elif args.scenario:
        run_single_scenario(
            args.scenario, 
            args.template, 
            args.show_prompt,
            args.all_comments
        )
    elif args.character:
        run_character_scenarios(args.character, args.template)
    else:
        run_all_scenarios(args.template, args.all_comments)
