"""
VEO (Google's video generation model) prompt generator.
Creates structured prompts with scene, characters, and descriptions for video generation.
"""

from typing import Dict, List, Optional
from .scene_extractor import SceneExtractor


class VEOPromptGenerator:
    """Generates prompts for VEO video generation from scene descriptions"""
    
    def __init__(self, scene_extractor: SceneExtractor):
        """
        Initialize the VEO prompt generator.
        
        Args:
            scene_extractor: SceneExtractor instance
        """
        self.scene_extractor = scene_extractor
        self.canon_loader = scene_extractor.canon_loader
        self.characters = self.canon_loader.load_characters()
    
    def get_character_description(self, character_name: str) -> str:
        """
        Get visual description of a character.
        
        Args:
            character_name: Name of the character
            
        Returns:
            Character description string
        """
        if character_name in self.characters:
            char_data = self.characters[character_name]
            desc = char_data.get('description', '')
            
            # Extract key visual/physical descriptors from description
            # Look for appearance-related keywords
            visual_keywords = [
                'beautiful', 'handsome', 'tall', 'short', 'fair', 'dark',
                'sharp features', 'graceful', 'imposing', 'stunning', 'elegant',
                'five-year-old', 'young', 'mature', 'child', 'daughter', 'son'
            ]
            
            # Try to extract relevant visual parts
            words = desc.lower().split()
            visual_parts = []
            for i, word in enumerate(words):
                if any(kw in word for kw in visual_keywords):
                    # Get surrounding context
                    start = max(0, i-2)
                    end = min(len(words), i+3)
                    visual_parts.append(' '.join(words[start:end]))
            
            if visual_parts:
                return ' '.join(visual_parts[:2])  # Use first 2 relevant parts
            else:
                # Fallback to first sentence
                return desc.split('.')[0] if '.' in desc else desc[:100]
        
        return f"{character_name}, a key character"
    
    def build_scene_prompt(self, scene_data: Dict) -> str:
        """
        Build a detailed scene description for VEO.
        
        Args:
            scene_data: Scene data dictionary from SceneExtractor
            
        Returns:
            Detailed scene description string
        """
        location = scene_data.get('location', 'a dramatic location')
        mood = scene_data.get('mood', 'dramatic')
        characters = scene_data.get('characters', [])
        visual_elements = scene_data.get('visual_elements', {})
        actions = visual_elements.get('actions', [])
        
        # Build character descriptions
        char_descriptions = []
        for char in characters[:3]:  # Limit to 3 main characters
            char_desc = self.get_character_description(char)
            char_descriptions.append(f"{char} ({char_desc})")
        
        # Build the prompt
        prompt_parts = []
        
        # Setting
        prompt_parts.append(f"Scene: {location}")
        
        # Characters
        if char_descriptions:
            prompt_parts.append(f"Characters: {', '.join(char_descriptions)}")
        
        # Mood/atmosphere
        prompt_parts.append(f"Mood: {mood}, cinematic, engaging")
        
        # Key actions (if any)
        if actions:
            prompt_parts.append(f"Action: {', '.join(actions[:3])}")
        
        # Visual style
        prompt_parts.append("Style: professional cinematography, clear focus, emotional depth")
        
        return ". ".join(prompt_parts) + "."
    
    def build_character_perspective_prompt(self, scene_data: Dict, character_name: str) -> str:
        """
        Build a prompt from a specific character's perspective.
        Useful for creating posts where a character shares their moment.
        
        Args:
            scene_data: Scene data dictionary
            character_name: Character whose perspective to use
            
        Returns:
            Perspective-based prompt string
        """
        if character_name not in scene_data.get('characters', []):
            # Character not in scene, create a "witness" perspective
            return self.build_scene_prompt(scene_data)
        
        char_desc = self.get_character_description(character_name)
        location = scene_data.get('location', 'a key location')
        mood = scene_data.get('mood', 'dramatic')
        visual_elements = scene_data.get('visual_elements', {})
        actions = visual_elements.get('actions', [])
        
        # Build from character's perspective
        prompt_parts = []
        
        # Character focus
        prompt_parts.append(f"Focus: {character_name} ({char_desc})")
        prompt_parts.append(f"Location: {location}")
        prompt_parts.append(f"Emotional state: {mood}, personal moment")
        
        # Other characters in frame (if any)
        other_chars = [c for c in scene_data.get('characters', []) if c != character_name]
        if other_chars:
            prompt_parts.append(f"Also visible: {', '.join(other_chars[:2])}")
        
        # Key action from this character's perspective
        if actions:
            prompt_parts.append(f"Key moment: {actions[0]}")
        
        # Visual style - more intimate for character perspective
        prompt_parts.append("Style: character-focused, intimate framing, emotional connection, social media post aesthetic")
        
        return ". ".join(prompt_parts) + "."
    
    def generate_veo_prompt(self, cliffhanger: Dict, perspective_character: Optional[str] = None,
                           include_background: bool = True) -> Dict:
        """
        Generate a complete VEO prompt from a cliffhanger.
        
        Args:
            cliffhanger: Cliffhanger dictionary
            perspective_character: Character perspective (optional)
            include_background: Whether to include subtle background elements
            
        Returns:
            Dictionary with structured prompt components
        """
        # Extract scene data
        scene_data = self.scene_extractor.create_non_spoiler_scene(
            cliffhanger, 
            perspective_character
        )
        
        # Build main prompt
        if perspective_character:
            main_prompt = self.build_character_perspective_prompt(scene_data, perspective_character)
        else:
            main_prompt = self.build_scene_prompt(scene_data)
        
        # Extract components for structured output
        components = {
            'scene': scene_data.get('location', 'dramatic location'),
            'characters': scene_data.get('characters', []),
            'descriptions': {}
        }
        
        # Add character descriptions
        for char in components['characters']:
            components['descriptions'][char] = self.get_character_description(char)
        
        # Build full prompt with optional background hints
        full_prompt = main_prompt
        if include_background and scene_data.get('visual_elements', {}).get('location'):
            # Add subtle environmental context without spoilers
            location = scene_data['visual_elements']['location']
            full_prompt += f" Background setting: {location}, realistic environment."
        
        return {
            'prompt': full_prompt,
            'components': components,
            'scene_data': scene_data,
            'episode': cliffhanger.get('episode'),
            'cliffhanger_title': cliffhanger.get('title'),
            'perspective_character': perspective_character,
            'mood': scene_data.get('mood'),
            'location': scene_data.get('location')
        }
    
    def generate_multiple_prompts(self, cliffhangers: List[Dict], 
                                  characters_per_cliffhanger: int = 1) -> List[Dict]:
        """
        Generate multiple VEO prompts from a list of cliffhangers.
        Can generate prompts from different character perspectives.
        
        Args:
            cliffhangers: List of cliffhanger dictionaries
            characters_per_cliffhanger: Number of character perspectives per cliffhanger
            
        Returns:
            List of prompt dictionaries
        """
        all_prompts = []
        
        for cliffhanger in cliffhangers:
            scene_data = self.scene_extractor.create_non_spoiler_scene(cliffhanger)
            characters = scene_data.get('characters', [])
            
            if characters and characters_per_cliffhanger > 0:
                # Generate from different character perspectives
                for char in characters[:characters_per_cliffhanger]:
                    prompt = self.generate_veo_prompt(cliffhanger, perspective_character=char)
                    all_prompts.append(prompt)
            else:
                # Generate generic prompt
                prompt = self.generate_veo_prompt(cliffhanger)
                all_prompts.append(prompt)
        
        return all_prompts
