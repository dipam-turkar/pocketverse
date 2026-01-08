"""
Scene extractor module that identifies catchy, engaging moments from cliffhangers.
Extracts visual scenes that would make good posts without spoilers.
"""

import re
from typing import List, Dict, Optional, Set
from .promo_canon_parser import PromoCanonLoader


class SceneExtractor:
    """Extracts engaging visual scenes from cliffhangers for post generation"""
    
    def __init__(self, canon_loader: PromoCanonLoader):
        """
        Initialize the scene extractor.
        
        Args:
            canon_loader: PromoCanonLoader instance with loaded data
        """
        self.canon_loader = canon_loader
        self.characters = canon_loader.load_characters()
    
    def extract_characters_from_text(self, text: str) -> List[str]:
        """
        Extract character names mentioned in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of character names found
        """
        found_characters = []
        text_lower = text.lower()
        
        for char_name, char_data in self.characters.items():
            # Check for full name
            if char_name.lower() in text_lower:
                found_characters.append(char_name)
            else:
                # Check for first name only
                first_name = char_name.split()[0] if ' ' in char_name else char_name
                if first_name.lower() in text_lower and len(first_name) > 3:
                    found_characters.append(char_name)
        
        return found_characters
    
    def extract_location_from_text(self, text: str) -> Optional[str]:
        """
        Extract location/setting from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Location string or None
        """
        # Common location patterns
        location_patterns = [
            r'(?:in|at|inside|outside|near|by)\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(?:hotel|restaurant|airport|lobby|suite|villa|deck|stairwell|garage|conference|kindergarten)',
        ]
        
        locations = []
        for pattern in location_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                location = match.group(1) if match.lastindex else match.group(0)
                if location and len(location) > 2:
                    locations.append(location)
        
        # Return most specific location found
        if locations:
            return locations[0]
        return None
    
    def extract_visual_elements(self, cliffhanger: Dict) -> Dict:
        """
        Extract visual elements from a cliffhanger for scene description.
        
        Args:
            cliffhanger: Cliffhanger dictionary
            
        Returns:
            Dictionary with visual scene elements
        """
        text = cliffhanger.get('cliffhanger_text', '')
        characters = self.extract_characters_from_text(text)
        location = self.extract_location_from_text(text)
        
        # Extract action verbs and key moments
        action_patterns = [
            r'(?:picks? up|carries?|hugs?|kisses?|stops?|confronts?|discovers?|sees?|spots?|meets?)',
            r'(?:cries?|shouts?|says?|declares?|asks?|exclaims?)',
            r'(?:walks?|runs?|rushes?|arrives?|leaves?)',
        ]
        
        actions = []
        for pattern in action_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            actions.extend([m.group(0) for m in matches])
        
        # Extract emotional tone
        emotion_keywords = {
            'dramatic': ['stunned', 'shocked', 'disbelief', 'frozen', 'speechless'],
            'tense': ['struggling', 'protesting', 'cries out', 'confrontation', 'threat'],
            'emotional': ['tears', 'cries', 'hugs', 'devastation', 'grief', 'longing'],
            'mysterious': ['mysterious', 'unknown', 'secret', 'hidden', 'unaware'],
            'action': ['forcibly', 'authoritatively', 'rushes', 'catches', 'discovers']
        }
        
        detected_emotions = []
        text_lower = text.lower()
        for emotion, keywords in emotion_keywords.items():
            if any(kw in text_lower for kw in keywords):
                detected_emotions.append(emotion)
        
        return {
            'characters': characters,
            'location': location,
            'actions': list(set(actions))[:5],  # Limit to 5 unique actions
            'emotions': detected_emotions,
            'episode': cliffhanger.get('episode'),
            'title': cliffhanger.get('title'),
            'severity': cliffhanger.get('severity', 'unknown')
        }
    
    def create_non_spoiler_scene(self, cliffhanger: Dict, perspective_character: Optional[str] = None) -> Dict:
        """
        Create a non-spoiler scene description from a cliffhanger.
        Focuses on the visual moment without revealing plot outcomes.
        
        Args:
            cliffhanger: Cliffhanger dictionary
            perspective_character: Character whose perspective to use (optional)
            
        Returns:
            Dictionary with scene description suitable for post generation
        """
        visual_elements = self.extract_visual_elements(cliffhanger)
        text = cliffhanger.get('cliffhanger_text', '')
        
        # Extract the key visual moment (first sentence or key phrase)
        # Remove spoiler content by focusing on the setup, not the resolution
        sentences = re.split(r'[.!?]+', text)
        key_moment = sentences[0].strip() if sentences else text[:200]
        
        # Create a character-focused description if perspective is provided
        if perspective_character and perspective_character in visual_elements['characters']:
            # Rewrite from that character's perspective
            scene_description = f"{perspective_character} in {visual_elements['location'] or 'a key moment'}"
        else:
            # Use first mentioned character or generic description
            main_char = visual_elements['characters'][0] if visual_elements['characters'] else "A character"
            scene_description = f"{main_char} in {visual_elements['location'] or 'a dramatic moment'}"
        
        # Build engaging but non-spoiler caption
        # Focus on the visual/emotional moment, not the plot outcome
        engaging_elements = []
        if visual_elements['emotions']:
            engaging_elements.append(f"a {visual_elements['emotions'][0]} moment")
        if visual_elements['location']:
            engaging_elements.append(f"at {visual_elements['location']}")
        if visual_elements['actions']:
            engaging_elements.append(f"as {visual_elements['actions'][0]}")
        
        return {
            'scene_description': scene_description,
            'key_moment': key_moment,
            'characters': visual_elements['characters'],
            'location': visual_elements['location'],
            'mood': visual_elements['emotions'][0] if visual_elements['emotions'] else 'dramatic',
            'episode': cliffhanger.get('episode'),
            'cliffhanger_title': cliffhanger.get('title'),
            'perspective_character': perspective_character,
            'visual_elements': visual_elements
        }
    
    def find_engaging_cliffhangers(self, min_episode: int = 1, max_episode: int = 100, 
                                   character_filter: Optional[str] = None) -> List[Dict]:
        """
        Find cliffhangers that would make engaging posts.
        
        Args:
            min_episode: Minimum episode number
            max_episode: Maximum episode number
            character_filter: Filter by character name (optional)
            
        Returns:
            List of cliffhanger dictionaries with scene extractions
        """
        all_cliffhangers = []
        all_cliffhangers.extend(self.canon_loader.load_major_cliffhangers())
        all_cliffhangers.extend(self.canon_loader.load_minor_cliffhangers())
        
        # Filter by episode range
        filtered = [
            c for c in all_cliffhangers 
            if min_episode <= c.get('episode', 0) <= max_episode
        ]
        
        # Filter by character if specified
        if character_filter:
            filtered = [
                c for c in filtered 
                if character_filter in self.extract_characters_from_text(c.get('cliffhanger_text', ''))
            ]
        
        # Score cliffhangers by engagement potential
        scored_cliffhangers = []
        for cliffhanger in filtered:
            visual = self.extract_visual_elements(cliffhanger)
            
            # Score based on:
            # - Number of characters (more = more engaging)
            # - Presence of clear location
            # - Emotional intensity
            # - Action elements
            score = 0
            score += len(visual['characters']) * 2
            score += 3 if visual['location'] else 0
            score += len(visual['emotions']) * 2
            score += len(visual['actions']) * 1
            score += 5 if cliffhanger.get('severity') == 'major' else 2
            
            scored_cliffhangers.append({
                'cliffhanger': cliffhanger,
                'score': score,
                'visual_elements': visual
            })
        
        # Sort by score (highest first)
        scored_cliffhangers.sort(key=lambda x: x['score'], reverse=True)
        
        return [item['cliffhanger'] for item in scored_cliffhangers]
