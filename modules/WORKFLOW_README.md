# Post Generation Workflow - Complete Guide

## Overview

This system generates engaging image posts for PocketFM shows by:
1. Parsing cliffhanger data from markdown files
2. Extracting visual scenes without spoilers
3. Generating structured prompts for image generation
4. Creating images using Nano Banana (Gemini) API
5. Saving images to disk for posting

## Architecture

```
PromoCanon MD Files
    ↓
[PromoCanon Parser] → Parses cliffhangers, characters, episodes → Caches to JSON
    ↓
[Scene Extractor] → Identifies catchy visual moments → Extracts characters, locations, actions
    ↓
[VEO Prompt Generator] → Creates structured prompts → Scene + Characters + Descriptions
    ↓
[Post Generation Engine] → Orchestrates generation → Filters by episode/character
    ↓
[Nano Banana Client] → Generates images → Returns base64 images
    ↓
[Image Generator Script] → Saves to disk → Creates posts ready for upload
```

## Components

### 1. PromoCanon Parser (`promo_canon_parser.py`)

**Purpose**: Parses markdown files containing show data

**Input Files**:
- `2_Characters_1-20.md` - Character descriptions
- `5_Major_Cliffhangers_1-100.md` - Major plot cliffhangers
- `6_Minor_Cliffhangers_1-100.md` - Minor cliffhangers
- `7_Episodic_Summary_1-100.md` - Episode summaries

**Output**: Structured data (cached to JSON for performance)

**Assumptions**:
- Files follow consistent markdown format
- Character names are in bold (`**Character Name**`)
- Cliffhangers have episode numbers and structured sections
- Files are organized by show in `PromoCanon_Show_{ID}/` directories

**Example Parsed Data**:
```json
{
  "episode": 7,
  "title": "The Kidnapping Misunderstanding",
  "cliffhanger_text": "In the hotel restaurant, Justin Hunt...",
  "type": "PLOT-BASED Major",
  "severity": "major"
}
```

### 2. Scene Extractor (`scene_extractor.py`)

**Purpose**: Extracts visual, engaging moments from cliffhangers

**What it does**:
- Identifies characters mentioned in text
- Extracts location/setting
- Finds key actions and emotions
- Creates non-spoiler scene descriptions
- Scores cliffhangers by engagement potential

**Assumptions**:
- Character names in cliffhanger text match character file names
- Locations are mentioned with common patterns (hotel, restaurant, etc.)
- Visual moments can be inferred from action verbs

**Example Output**:
```python
{
  'characters': ['Justin Hunt', 'Cherry Smith', 'Pete Hunt'],
  'location': 'hotel restaurant',
  'actions': ['picks up', 'cries out', 'declares'],
  'emotions': ['tense', 'emotional', 'action'],
  'mood': 'tense'
}
```

### 3. VEO Prompt Generator (`veo_prompt_generator.py`)

**Purpose**: Creates structured prompts for image generation

**Input**: Scene data from Scene Extractor
**Output**: Formatted prompt with scene, characters, descriptions

**Prompt Structure**:
```
Scene: [location]
Characters: [character1] ([description]), [character2] ([description])
Mood: [mood], cinematic, engaging
Action: [key actions]
Style: professional cinematography, clear focus, emotional depth
Background setting: [location], realistic environment.
```

**Example Generated Prompt**:
```
Scene: hotel restaurant. Characters: Justin Hunt (Powerful businessman and protective single father), Cherry Smith (Nora's precocious five-year-old daughter). Mood: tense, cinematic, engaging. Action: picks up, cries out, declares. Style: professional cinematography, clear focus, emotional depth. Background setting: hotel restaurant, realistic environment.
```

**Assumptions**:
- Character descriptions are available in character files
- Prompts should be non-spoiler (focus on visual moment, not outcome)
- Multiple character perspectives can be generated per cliffhanger

### 4. Post Generation Engine (`post_generation_engine.py`)

**Purpose**: Main orchestration - provides high-level API

**Key Methods**:
- `generate_prompts_for_cliffhanger()` - By episode number
- `generate_prompts_for_character()` - By character name
- `generate_top_engaging_prompts()` - Most engaging scenes
- `generate_prompts_for_episode_range()` - Episode range

**Assumptions**:
- Users want to generate posts from character perspectives
- Multiple prompts per cliffhanger (different perspectives) increase engagement
- Engagement can be scored by: character count, location clarity, emotional intensity

### 5. Nano Banana Client (`nano_banana_client.py`)

**Purpose**: Generates images using Google's Gemini API

**API Endpoint**:
```
https://aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model}:streamGenerateContent
```

**Request Format**:
```json
{
  "contents": [{
    "role": "user",
    "parts": [{"text": "prompt text"}]
  }],
  "generationConfig": {
    "temperature": 0.7,
    "maxOutputTokens": 2048,
    "responseModalities": ["IMAGE"],
    "imageConfig": {
      "aspectRatio": "1:1"
    }
  }
}
```

**Assumptions**:
- Uses GCP service account credentials from `creds.py`
- Model: `gemini-2.5-flash-image` (default)
- Aspect ratios must be standard format ("1:1", "16:9", etc.)
- Returns base64-encoded images in response

**Response Format**:
```json
{
  "candidates": [{
    "content": {
      "parts": [{
        "inlineData": {
          "mimeType": "image/png",
          "data": "base64_encoded_image..."
        }
      }]
    }
  }]
}
```

### 6. Image Generation Script (`generate_images_from_prompts.py`)

**Purpose**: End-to-end workflow from prompts to saved images

**Workflow**:
1. Load PromoCanon data
2. Generate prompts for specified episode
3. Call Nano Banana API for each prompt
4. Extract base64 image data
5. Save images to disk
6. Optionally upload to GCS
7. Save results to JSON

**Configuration**:
```python
EPISODE_NUM = 7
PROMPTS_PER_CLIFFHANGER = 3
MAX_IMAGES_TO_GENERATE = 3
SAVE_TO_DISK = True
IMAGES_DIR = "generated_images"
```

## Complete Workflow Example

### Step 1: Parse Data
```python
from modules.post_generation_engine import create_engine

engine = create_engine("PromoCanon_Show_...")
# Automatically parses and caches to .cache/ directory
```

### Step 2: Generate Prompts
```python
prompts = engine.generate_prompts_for_cliffhanger(
    episode_num=7,
    prompts_per_cliffhanger=3
)
# Returns 3 prompts from different character perspectives
```

### Step 3: Generate Images
```python
from modules.nano_banana_client import create_nano_banana_client

client = create_nano_banana_client()
result = client.generate_image(
    prompt=prompts[0]['prompt'],
    width=1024,
    height=1024
)
# Returns: {"image_url": "data:image/png;base64,...", "image_id": "...", ...}
```

### Step 4: Save to Disk
```python
# Extract base64 from data URL
image_base64 = result['image_url'].split(",")[1]

# Save to disk
disk_path = client.save_image_to_disk(
    image_base64=image_base64,
    filepath="generated_images/episode_7_nora_1234567890.png"
)
```

## Example Prompts Generated

### Example 1: Episode 7 - Nora's Perspective
```
Scene: hotel restaurant
Characters: Nora Smith (Brilliant surgeon and dedicated mother), Cherry Smith (Nora's precocious five-year-old daughter)
Mood: dramatic, cinematic, engaging
Action: picks up, cries out
Style: professional cinematography, clear focus, emotional depth
Background setting: hotel restaurant, realistic environment.
```

### Example 2: Episode 7 - Justin's Perspective
```
Focus: Justin Hunt (Powerful businessman and protective single father)
Location: hotel restaurant
Emotional state: tense, personal moment
Also visible: Cherry Smith, Pete Hunt
Key moment: picks up
Style: character-focused, intimate framing, emotional connection, social media post aesthetic
```

### Example 3: Episode 15 - Twin Discovery
```
Scene: hotel stairwell
Characters: Pete Hunt (Nora's missing son), Cherry Smith (Nora's precocious five-year-old daughter)
Mood: dramatic, cinematic, engaging
Action: come face-to-face, asks
Style: professional cinematography, clear focus, emotional depth
Background setting: hotel stairwell, realistic environment.
```

## Assumptions Made

1. **File Structure**: PromoCanon files follow consistent naming and format
2. **Character Matching**: Character names in text match exactly with character file entries
3. **Non-Spoiler Focus**: Posts should hint at drama without revealing outcomes
4. **Character Perspectives**: Posts are more engaging from character viewpoints
5. **API Compatibility**: Nano Banana uses Google Gemini API format
6. **Image Storage**: Base64 images are sufficient for initial storage (can be uploaded to GCS later)

## Usage

### Quick Start
```bash
# 1. Generate prompts (debug)
python modules/debug_prompt_generation.py

# 2. Generate images from prompts
python modules/generate_images_from_prompts.py
```

### Configuration
Edit `generate_images_from_prompts.py`:
- `EPISODE_NUM` - Which episode to generate for
- `PROMPTS_PER_CLIFFHANGER` - How many perspectives per cliffhanger
- `MAX_IMAGES_TO_GENERATE` - Limit for testing
- `SAVE_TO_DISK` - Enable/disable disk saving
- `IMAGES_DIR` - Where to save images

## Output

### Generated Files
- `generated_images/` - Directory with PNG images
- `generated_images.json` - Metadata about generated images
- `.cache/` - Parsed data cache (in PromoCanon directory)

### Image Naming
Format: `episode_{episode}_{character}_{timestamp}.png`
Example: `episode_7_Nora_Smith_1234567890.png`

### Results JSON Structure
```json
{
  "generation_config": {
    "episode_num": 7,
    "max_images": 3
  },
  "results": [{
    "prompt_data": {...},
    "image_id": "...",
    "image_url": "data:image/png;base64,...",
    "disk_path": "generated_images/episode_7_Nora_Smith_1234567890.png",
    "status": "completed"
  }]
}
```

## Next Steps

1. **Upload to GCS**: Set `GCS_UPLOAD = True` and configure bucket
2. **Create Posts**: Use `OfficialPostCreator` to create posts with generated images
3. **Batch Processing**: Extend to process multiple episodes
4. **Post Scheduling**: Add scheduling logic for posting at optimal times

## Dependencies

- Standard library: `re`, `json`, `pathlib`, `base64`
- Google Cloud: `google-cloud-aiplatform`, `google-cloud-storage`, `google-auth`
- External: `requests`

Install: `pip install -r requirements.txt`
