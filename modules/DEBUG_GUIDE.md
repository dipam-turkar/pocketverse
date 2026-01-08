# Debug Script Guide - Where to Configure Post Generation

## Quick Reference: Configuration Location

All configuration is at the **top of `debug_prompt_generation.py`** (lines 12-50).

## Configuration Options

### 1. Canon Directory
```python
CANON_DIRECTORY = "PromoCanon_Show_33adb096b04ecd6b23ce9341160b199f2d489311_1_100"
```
**Location:** Line 15

### 2. Generation Mode
```python
GENERATION_MODE = "top_engaging"  # Options: "episode", "character", "top_engaging", "episode_range"
```
**Location:** Line 18

### 3. Episode-Specific Generation
```python
EPISODE_NUM = 7  # Episode number
EPISODE_CHARACTER = None  # None or "Nora Smith", "Justin Hunt", etc.
```
**Location:** Lines 21-22  
**Used when:** `GENERATION_MODE = "episode"`

### 4. Character Perspective Generation
```python
CHARACTER_NAME = "Nora Smith"
CHARACTER_MIN_EPISODE = 1
CHARACTER_MAX_EPISODE = 20
CHARACTER_LIMIT = 5
```
**Location:** Lines 25-28  
**Used when:** `GENERATION_MODE = "character"`

### 5. Top Engaging Prompts
```python
TOP_COUNT = 5
TOP_MIN_EPISODE = 1
TOP_MAX_EPISODE = 20
```
**Location:** Lines 31-33  
**Used when:** `GENERATION_MODE = "top_engaging"`

### 6. Episode Range Generation
```python
RANGE_START = 1
RANGE_END = 10
RANGE_CHARACTERS_PER_CLIFFHANGER = 1
```
**Location:** Lines 36-38  
**Used when:** `GENERATION_MODE = "episode_range"`

### 7. Output Format
```python
OUTPUT_FORMAT = "detailed"  # "detailed", "json", or "simple"
SAVE_TO_FILE = False
OUTPUT_FILE = "generated_prompts.json"
```
**Location:** Lines 41-44

## Usage Examples

### Example 1: Generate 5 top engaging prompts
```python
GENERATION_MODE = "top_engaging"
TOP_COUNT = 5
TOP_MIN_EPISODE = 1
TOP_MAX_EPISODE = 20
```

### Example 2: Generate for specific episode from character perspective
```python
GENERATION_MODE = "episode"
EPISODE_NUM = 7
EPISODE_CHARACTER = "Nora Smith"
```

### Example 3: Generate from character perspective (multiple episodes)
```python
GENERATION_MODE = "character"
CHARACTER_NAME = "Nora Smith"
CHARACTER_MIN_EPISODE = 1
CHARACTER_MAX_EPISODE = 10
CHARACTER_LIMIT = 5
```

### Example 4: Generate for episode range
```python
GENERATION_MODE = "episode_range"
RANGE_START = 1
RANGE_END = 10
RANGE_CHARACTERS_PER_CLIFFHANGER = 2  # Multiple perspectives per cliffhanger
```

## Running the Debug Script

```bash
# From the project root
python modules/debug_prompt_generation.py

# Or from modules directory
cd modules
python debug_prompt_generation.py
```

## Code Entry Points (for reference)

If you want to call the engine directly from code:

1. **By Episode** - `post_generation_engine.py` line 30
   ```python
   engine.generate_prompts_for_cliffhanger(episode_num=7, perspective_character="Nora Smith")
   ```

2. **By Character** - `post_generation_engine.py` line 60
   ```python
   engine.generate_prompts_for_character(character_name="Nora Smith", min_episode=1, max_episode=20, limit=5)
   ```

3. **Top Engaging** - `post_generation_engine.py` line 97
   ```python
   engine.generate_top_engaging_prompts(count=5, min_episode=1, max_episode=20)
   ```

4. **Episode Range** - `post_generation_engine.py` line 125
   ```python
   engine.generate_prompts_for_episode_range(start_episode=1, end_episode=10, characters_per_cliffhanger=1)
   ```
