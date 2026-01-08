"""
Main post generation engine that orchestrates prompt generation for VEO.
Modular system for generating engaging post prompts from cliffhangers.
"""

from typing import List, Dict, Optional
from pathlib import Path
from .promo_canon_parser import PromoCanonLoader
from .scene_extractor import SceneExtractor
from .veo_prompt_generator import VEOPromptGenerator


class PostGenerationEngine:
    """
    Main engine for generating post prompts from PromoCanon data.
    Modular design allows for easy extension and customization.
    """
    
    def __init__(self, canon_directory: str):
        """
        Initialize the post generation engine.
        
        Args:
            canon_directory: Path to PromoCanon directory containing MD files
        """
        self.canon_loader = PromoCanonLoader(canon_directory)
        self.scene_extractor = SceneExtractor(self.canon_loader)
        self.prompt_generator = VEOPromptGenerator(self.scene_extractor)
    
    def generate_prompts_for_cliffhanger(self, episode_num: int, 
                                         perspective_character: Optional[str] = None,
                                         prompts_per_cliffhanger: int = 2) -> List[Dict]:
        """
        Generate VEO prompts for a specific episode's cliffhangers.
        
        Args:
            episode_num: Episode number
            perspective_character: Specific character perspective (optional)
            prompts_per_cliffhanger: Number of prompts to generate per cliffhanger (default: 2)
            
        Returns:
            List of prompt dictionaries
        """
        cliffhangers = self.canon_loader.get_cliffhanger_by_episode(episode_num)
        
        if not cliffhangers:
            return []
        
        prompts = []
        for cliffhanger in cliffhangers:
            # Extract characters from the cliffhanger
            scene_data = self.scene_extractor.create_non_spoiler_scene(cliffhanger)
            characters = scene_data.get('characters', [])
            
            if perspective_character:
                # Generate from specified character perspective
                prompt = self.prompt_generator.generate_veo_prompt(
                    cliffhanger, 
                    perspective_character=perspective_character
                )
                prompts.append(prompt)
            else:
                # Generate multiple prompts from different character perspectives
                # If not enough characters, generate generic prompts
                if characters and len(characters) >= prompts_per_cliffhanger:
                    # Use different character perspectives
                    for char in characters[:prompts_per_cliffhanger]:
                        prompt = self.prompt_generator.generate_veo_prompt(
                            cliffhanger,
                            perspective_character=char
                        )
                        prompts.append(prompt)
                else:
                    # Generate generic prompt, then from available characters
                    prompt = self.prompt_generator.generate_veo_prompt(cliffhanger)
                    prompts.append(prompt)
                    
                    # Add character-specific prompts if available
                    for char in characters[:prompts_per_cliffhanger - 1]:
                        prompt = self.prompt_generator.generate_veo_prompt(
                            cliffhanger,
                            perspective_character=char
                        )
                        prompts.append(prompt)
        
        return prompts
    
    def generate_prompts_for_character(self, character_name: str, 
                                       min_episode: int = 1, 
                                       max_episode: int = 100,
                                       limit: int = 10) -> List[Dict]:
        """
        Generate prompts featuring a specific character.
        
        Args:
            character_name: Name of the character
            min_episode: Minimum episode number
            max_episode: Maximum episode number
            limit: Maximum number of prompts to generate
            
        Returns:
            List of prompt dictionaries
        """
        # Find engaging cliffhangers with this character
        cliffhangers = self.scene_extractor.find_engaging_cliffhangers(
            min_episode=min_episode,
            max_episode=max_episode,
            character_filter=character_name
        )
        
        # Generate prompts from this character's perspective
        prompts = self.prompt_generator.generate_multiple_prompts(
            cliffhangers[:limit],
            characters_per_cliffhanger=1
        )
        
        # Filter to only this character's perspective
        filtered = [
            p for p in prompts 
            if p.get('perspective_character') == character_name
        ]
        
        return filtered[:limit]
    
    def generate_top_engaging_prompts(self, count: int = 20,
                                     min_episode: int = 1,
                                     max_episode: int = 100) -> List[Dict]:
        """
        Generate prompts for the most engaging cliffhangers.
        
        Args:
            count: Number of prompts to generate
            min_episode: Minimum episode number
            max_episode: Maximum episode number
            
        Returns:
            List of prompt dictionaries sorted by engagement potential
        """
        # Find most engaging cliffhangers
        cliffhangers = self.scene_extractor.find_engaging_cliffhangers(
            min_episode=min_episode,
            max_episode=max_episode
        )
        
        # Generate prompts (one per cliffhanger, from first character's perspective)
        prompts = self.prompt_generator.generate_multiple_prompts(
            cliffhangers[:count],
            characters_per_cliffhanger=1
        )
        
        return prompts
    
    def generate_prompts_for_episode_range(self, start_episode: int, 
                                          end_episode: int,
                                          characters_per_cliffhanger: int = 1) -> List[Dict]:
        """
        Generate prompts for all cliffhangers in an episode range.
        
        Args:
            start_episode: Starting episode number
            end_episode: Ending episode number
            characters_per_cliffhanger: Number of character perspectives per cliffhanger
            
        Returns:
            List of prompt dictionaries
        """
        all_cliffhangers = []
        all_cliffhangers.extend(self.canon_loader.load_major_cliffhangers())
        all_cliffhangers.extend(self.canon_loader.load_minor_cliffhangers())
        
        # Filter by episode range
        filtered = [
            c for c in all_cliffhangers
            if start_episode <= c.get('episode', 0) <= end_episode
        ]
        
        # Generate prompts
        prompts = self.prompt_generator.generate_multiple_prompts(
            filtered,
            characters_per_cliffhanger=characters_per_cliffhanger
        )
        
        return prompts
    
    def get_available_characters(self) -> List[str]:
        """
        Get list of available characters from the canon.
        
        Returns:
            List of character names
        """
        characters = self.canon_loader.load_characters()
        return list(characters.keys())
    
    def get_prompt_summary(self, prompt: Dict) -> str:
        """
        Get a human-readable summary of a prompt.
        
        Args:
            prompt: Prompt dictionary
            
        Returns:
            Summary string
        """
        components = prompt.get('components', {})
        scene = components.get('scene', 'Unknown scene')
        characters = ', '.join(components.get('characters', []))
        mood = prompt.get('mood', 'dramatic')
        episode = prompt.get('episode', 'Unknown')
        
        summary = f"Episode {episode}: {scene} - {characters} ({mood})"
        if prompt.get('perspective_character'):
            summary += f" [From {prompt['perspective_character']}'s perspective]"
        
        return summary


def create_engine(canon_directory: str) -> PostGenerationEngine:
    """
    Factory function to create a PostGenerationEngine.
    
    Args:
        canon_directory: Path to PromoCanon directory
        
    Returns:
        PostGenerationEngine instance
    """
    return PostGenerationEngine(canon_directory)
