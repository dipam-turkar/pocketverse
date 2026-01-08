# Post Generation Engine for VEO Prompts

A modular system for generating VEO (Google's video generation model) prompts from PromoCanon cliffhanger data. The system extracts engaging scenes from cliffhangers and creates structured prompts suitable for video generation.

## Architecture

The system is built with modularity in mind, allowing easy extension for different shows and use cases:

```
promo_canon_parser.py      → Parses MD files (cliffhangers, characters, episodes)
scene_extractor.py         → Extracts visual scenes from cliffhangers
veo_prompt_generator.py    → Generates structured VEO prompts
post_generation_engine.py  → Main orchestration engine
```

## Features

- **Non-spoiler scene extraction**: Focuses on visual moments without revealing plot outcomes
- **Character perspective support**: Generate prompts from specific character viewpoints
- **Engagement scoring**: Automatically identifies most engaging cliffhangers
- **Modular design**: Easy to extend for different shows and formats
- **Structured prompts**: Includes scene, characters, descriptions, mood, location

## Quick Start

```python
from modules.post_generation_engine import create_engine

# Initialize with PromoCanon directory
engine = create_engine("PromoCanon_Show_33adb096b04ecd6b23ce9341160b199f2d489311_1_100")

# Generate prompts for Episode 7 (airport scene)
prompts = engine.generate_prompts_for_cliffhanger(episode_num=7)

# Access prompt data
for prompt in prompts:
    print(prompt['prompt'])  # Full VEO prompt
    print(prompt['components'])  # Structured components
```

## Usage Examples

### Example 1: Character Perspective Posts

Generate posts from a character's perspective (e.g., "Nora posts that she just came out of airport"):

```python
# Generate prompts from Nora's perspective
prompts = engine.generate_prompts_for_character(
    character_name="Nora Smith",
    min_episode=1,
    max_episode=20,
    limit=5
)

for prompt in prompts:
    print(f"Episode {prompt['episode']}: {prompt['cliffhanger_title']}")
    print(f"From {prompt['perspective_character']}'s perspective:")
    print(prompt['prompt'])
```

### Example 2: Top Engaging Scenes

Find the most engaging cliffhangers for post generation:

```python
# Get top 10 most engaging prompts
prompts = engine.generate_top_engaging_prompts(count=10)

for i, prompt in enumerate(prompts, 1):
    print(f"{i}. Episode {prompt['episode']}")
    print(f"   Scene: {prompt['components']['scene']}")
    print(f"   Characters: {', '.join(prompt['components']['characters'])}")
    print(f"   Mood: {prompt['mood']}")
    print(f"   Prompt: {prompt['prompt']}\n")
```

### Example 3: Episode Range

Generate prompts for a range of episodes:

```python
# Generate for episodes 1-10, multiple character perspectives
prompts = engine.generate_prompts_for_episode_range(
    start_episode=1,
    end_episode=10,
    characters_per_cliffhanger=2  # Generate from 2 character perspectives
)

print(f"Generated {len(prompts)} prompts")
```

### Example 4: Specific Cliffhanger

Generate a prompt for a specific cliffhanger with character perspective:

```python
# Generate prompt for Episode 7 from Nora's perspective
prompts = engine.generate_prompts_for_cliffhanger(
    episode_num=7,
    perspective_character="Nora Smith"
)

if prompts:
    prompt = prompts[0]
    print(f"Episode: {prompt['episode']}")
    print(f"Cliffhanger: {prompt['cliffhanger_title']}")
    print(f"Location: {prompt['location']}")
    print(f"VEO Prompt:\n{prompt['prompt']}")
```

## Prompt Structure

Each generated prompt is a dictionary with the following structure:

```python
{
    'prompt': str,                    # Full VEO prompt string
    'components': {
        'scene': str,                 # Scene location/description
        'characters': List[str],      # Character names
        'descriptions': {             # Character descriptions
            'Character Name': str
        }
    },
    'scene_data': dict,               # Extracted scene information
    'episode': int,                   # Episode number
    'cliffhanger_title': str,         # Title of the cliffhanger
    'perspective_character': str,     # Character perspective (if specified)
    'mood': str,                      # Emotional mood (dramatic, tense, etc.)
    'location': str                   # Scene location
}
```

## VEO Prompt Format

The generated prompts follow this structure:

```
Scene: [location]
Characters: [character1] ([description]), [character2] ([description])
Mood: [mood], cinematic, engaging
Action: [key actions]
Style: professional cinematography, clear focus, emotional depth
Background setting: [location], realistic environment.
```

Example output:
```
Scene: hotel restaurant
Characters: Justin Hunt (Powerful businessman and protective single father), Cherry Smith (Nora's precocious five-year-old daughter)
Mood: dramatic, cinematic, engaging
Action: picks up, cries out, declares
Style: professional cinematography, clear focus, emotional depth
Background setting: hotel restaurant, realistic environment.
```

## How It Works

1. **Parsing**: The `PromoCanonLoader` parses markdown files to extract:
   - Major and minor cliffhangers
   - Character descriptions
   - Episode summaries

2. **Scene Extraction**: The `SceneExtractor` identifies:
   - Characters in the scene
   - Location/setting
   - Key actions
   - Emotional tone
   - Visual elements

3. **Prompt Generation**: The `VEOPromptGenerator` creates:
   - Structured prompts with scene, characters, descriptions
   - Character-specific perspectives
   - Non-spoiler descriptions

4. **Orchestration**: The `PostGenerationEngine` provides:
   - High-level API for common use cases
   - Filtering and scoring
   - Batch generation

## Extending for Other Shows

The system is designed to work with any PromoCanon directory structure:

```
PromoCanon_Show_[ID]/
├── 2_Characters_1-20.md
├── 5_Major_Cliffhangers_1-100.md
├── 6_Minor_Cliffhangers_1-100.md
└── 7_Episodic_Summary_1-100.md
```

Simply point the engine to a different directory:

```python
engine = create_engine("PromoCanon_Show_AnotherShow_ID")
```

## Integration with Post Creation

Once you have VEO prompts, you can integrate with the post creation system:

```python
from modules.post_generation_engine import create_engine
from modules.official_post_creator import OfficialPostCreator

# Generate prompts
engine = create_engine("PromoCanon_Show_...")
prompts = engine.generate_top_engaging_prompts(count=10)

# Create posts (after generating videos from prompts)
post_creator = OfficialPostCreator()

for prompt in prompts:
    # Generate video using VEO with prompt['prompt']
    # video_url = generate_video_with_veo(prompt['prompt'])
    
    # Create post
    post = post_creator.create_post(
        pocketshow_id=1,
        title=f"Episode {prompt['episode']}: {prompt['cliffhanger_title']}",
        author_id=character_user_id,
        content=f"From {prompt['perspective_character']}'s perspective...",
        image_url=None,  # Or video_url if using video
        metadata={
            'episode': prompt['episode'],
            'cliffhanger_title': prompt['cliffhanger_title'],
            'veo_prompt': prompt['prompt'],
            'location': prompt['location'],
            'mood': prompt['mood']
        }
    )
```

## Notes

- The system focuses on **non-spoiler** content - it extracts visual moments without revealing plot outcomes
- Character perspectives are automatically extracted from cliffhanger text
- Engagement scoring considers: number of characters, location clarity, emotional intensity, action elements
- All prompts are designed for VEO video generation with clear scene, character, and description components
