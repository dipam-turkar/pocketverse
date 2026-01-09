"""
Story Context Service for Character Chatbot.
Provides functions to fetch story context based on user's episode progress.

This module handles:
- Episode to beat mapping
- Character knowledge state at specific episodes
- Previous plot summaries
- Episode progression context
- Engagement hooks selection
"""

import json
import os
from typing import Dict, List, Optional, Any
from functools import lru_cache


class StoryContextService:
    """Service for fetching story context for character responses."""
    
    def __init__(self, context_dir: str = "context"):
        """
        Initialize the story context service.
        
        Args:
            context_dir: Path to the context directory
        """
        self.context_dir = context_dir
        self._cache = {}
    
    # =========================================================================
    # DATA LOADING (with caching)
    # =========================================================================
    
    def _get_context_path(self, *parts: str) -> str:
        """Get full path to a context file."""
        return os.path.join(self.context_dir, *parts)
    
    def _load_json(self, filepath: str) -> Dict:
        """Load JSON file with caching."""
        if filepath in self._cache:
            return self._cache[filepath]
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._cache[filepath] = data
                return data
        except Exception as e:
            print(f"[STORY_CONTEXT] Error loading {filepath}: {e}")
            return {}
    
    def load_characters(self, show_id: str = "saving_nora") -> Dict:
        """Load character personas from all_characters_optimized_v2.json."""
        filepath = self._get_context_path("characters", "all_characters_optimized_v2.json")
        return self._load_json(filepath)
    
    def load_character_journey(self, show_id: str = "saving_nora") -> Dict:
        """Load character journey data from saving_nora_character_journey.json."""
        filepath = self._get_context_path("character_journey", f"{show_id}_character_journey.json")
        return self._load_json(filepath)
    
    def load_episode_progression(self, show_id: str = "saving_nora") -> Dict:
        """Load episode progression data from saving_nora_episodes.json."""
        filepath = self._get_context_path("episode_progression", f"{show_id}_episodes.json")
        return self._load_json(filepath)
    
    def load_plot_summary(self, show_id: str = "saving_nora") -> Dict:
        """Load plot summary data from saving_nora_plot_summary.json."""
        filepath = self._get_context_path("plot_summaries", f"{show_id}_plot_summary.json")
        return self._load_json(filepath)
    
    # =========================================================================
    # EPISODE TO BEAT MAPPING
    # =========================================================================
    
    def get_beat_for_episode(self, episode: int, show_id: str = "saving_nora") -> Dict:
        """
        Maps episode number to beat information.
        
        Args:
            episode: Episode number (e.g., 25)
            show_id: Show identifier
            
        Returns:
            {
                "beat_id": 3,
                "beat_title": "Athena's Surgery",
                "episode_range": {"start": 21, "end": 30},
                "is_within_beat": True,
                "episodes_into_beat": 5
            }
        """
        episodes_data = self.load_episode_progression(show_id)
        chapters = episodes_data.get("chapters", [])
        
        for chapter in chapters:
            ep_range = chapter.get("episode_range", {})
            start = ep_range.get("start", 0)
            end = ep_range.get("end", 0)
            
            if start <= episode <= end:
                return {
                    "beat_id": chapter.get("beat_id"),
                    "beat_title": chapter.get("beat_title"),
                    "episode_range": ep_range,
                    "is_within_beat": True,
                    "episodes_into_beat": episode - start + 1
                }
        
        # If episode is beyond all beats, return the last beat
        if chapters:
            last_chapter = chapters[-1]
            return {
                "beat_id": last_chapter.get("beat_id"),
                "beat_title": last_chapter.get("beat_title"),
                "episode_range": last_chapter.get("episode_range", {}),
                "is_within_beat": False,
                "episodes_into_beat": 0
            }
        
        return {
            "beat_id": None,
            "beat_title": "Unknown",
            "episode_range": {},
            "is_within_beat": False,
            "episodes_into_beat": 0
        }
    
    # =========================================================================
    # CHARACTER PERSONA
    # =========================================================================
    
    def get_character_persona(self, character_id: str, show_id: str = "saving_nora") -> Dict:
        """
        Get character persona data.
        
        Args:
            character_id: Character identifier (e.g., "nora_smith", "justin_hunt")
            show_id: Show identifier
            
        Returns:
            Character persona dict with voice, psychology, dialogue_examples, etc.
        """
        characters_data = self.load_characters(show_id)
        
        # The character data is stored with character_id as key
        character = characters_data.get(character_id, {})
        
        if not character:
            # Try to find by name match
            for key, data in characters_data.items():
                if key == "meta":
                    continue
                identity = data.get("identity", {})
                if identity.get("name", "").lower().replace(" ", "_") == character_id.lower():
                    return data
        
        return character
    
    def format_character_persona_for_prompt(self, character_id: str, show_id: str = "saving_nora") -> str:
        """
        Format character persona as a string for LLM prompt.
        
        Args:
            character_id: Character identifier
            show_id: Show identifier
            
        Returns:
            Formatted string with character persona
        """
        persona = self.get_character_persona(character_id, show_id)
        
        if not persona:
            return f"Character: {character_id}"
        
        lines = []
        
        # Identity
        identity = persona.get("identity", {})
        lines.append(f"Name: {identity.get('name', character_id)}")
        if identity.get("one_liner"):
            lines.append(f"Role: {identity.get('one_liner')}")
        
        # Psychology
        psychology = persona.get("psychology", {})
        if psychology.get("core_want"):
            lines.append(f"Core Want: {psychology.get('core_want')}")
        if psychology.get("primary_fear"):
            lines.append(f"Primary Fear: {psychology.get('primary_fear')}")
        if psychology.get("self_perception"):
            lines.append(f"Self-perception: {psychology.get('self_perception')}")
        
        return "\n".join(lines)
    
    def format_voice_rules_for_prompt(self, character_id: str, show_id: str = "saving_nora") -> Dict[str, str]:
        """
        Extract voice rules from character persona.
        
        Returns:
            Dict with vocabulary, rhythm, reddit_phrases, never_says
        """
        persona = self.get_character_persona(character_id, show_id)
        
        voice = persona.get("voice", {})
        verbal_tics = persona.get("verbal_tics", [])
        never_says = persona.get("never_says", [])
        reddit_phrases = persona.get("reddit_phrases", [])
        
        return {
            "vocabulary": voice.get("vocabulary", "normal"),
            "rhythm": voice.get("rhythm", "normal"),
            "emotional_default": voice.get("emotional_default", "neutral"),
            "humor": voice.get("humor", "none"),
            "verbal_tics": ", ".join(verbal_tics[:5]) if verbal_tics else "None specific",
            "never_says": ", ".join(never_says[:5]) if never_says else "None specific",
            "reddit_phrases": ", ".join(reddit_phrases[:10]) if reddit_phrases else "None specific"
        }
    
    # =========================================================================
    # PREVIOUS PLOT SUMMARIES
    # =========================================================================
    
    def get_previous_plot_summaries(
        self, 
        current_beat_id: int, 
        show_id: str = "saving_nora",
        max_summaries: int = 5
    ) -> List[Dict]:
        """
        Fetches summaries of previous beats (up to last 5).
        
        Args:
            current_beat_id: User's current beat (e.g., 4)
            show_id: Show identifier
            max_summaries: Maximum number of previous beats to include
            
        Returns:
            List of beat summaries:
            [
                {
                    "beat_id": 1,
                    "title": "Homecoming",
                    "summary": "Start + Mid + End combined"
                },
                ...
            ]
        """
        plot_data = self.load_plot_summary(show_id)
        beats = plot_data.get("beats", [])
        
        summaries = []
        for beat in beats:
            beat_id = beat.get("beat_id", 0)
            if beat_id < current_beat_id:
                # Combine start, mid, end into a coherent summary
                summary_parts = []
                if beat.get("start"):
                    summary_parts.append(beat["start"])
                if beat.get("mid"):
                    summary_parts.append(beat["mid"])
                if beat.get("end"):
                    summary_parts.append(beat["end"])
                
                summaries.append({
                    "beat_id": beat_id,
                    "title": beat.get("title", f"Beat {beat_id}"),
                    "episode_range": f"EP{beat.get('start_episode', '?')}-{beat.get('end_episode', '?')}",
                    "summary": " ".join(summary_parts)
                })
        
        # Return last N summaries (most recent previous beats)
        return summaries[-max_summaries:] if len(summaries) > max_summaries else summaries
    
    def format_previous_plots_for_prompt(
        self, 
        current_beat_id: int, 
        show_id: str = "saving_nora",
        max_summaries: int = 5
    ) -> str:
        """
        Format previous plot summaries as a string for LLM prompt.
        """
        summaries = self.get_previous_plot_summaries(current_beat_id, show_id, max_summaries)
        
        if not summaries:
            return "No previous beats - this is the beginning of the story."
        
        lines = []
        for summary in summaries:
            lines.append(f"**Beat {summary['beat_id']} - {summary['title']} ({summary['episode_range']}):**")
            # Truncate long summaries
            text = summary['summary']
            if len(text) > 500:
                text = text[:500] + "..."
            lines.append(text)
            lines.append("")
        
        return "\n".join(lines)
    
    # =========================================================================
    # CURRENT BEAT EPISODE PROGRESSION
    # =========================================================================
    
    def get_current_beat_episodes(
        self, 
        user_episode: int, 
        show_id: str = "saving_nora"
    ) -> Dict:
        """
        Get episodes in current beat up to user's episode.
        
        Args:
            user_episode: User's current episode
            show_id: Show identifier
            
        Returns:
            {
                "beat_info": {...},
                "known_episodes": [...],  # Episodes user has heard
                "unknown_episodes": [...],  # Remaining episodes in beat (can tease)
                "reached_cliffhangers": [...],
                "known_facts": [...],
                "available_hooks": [...]
            }
        """
        beat_info = self.get_beat_for_episode(user_episode, show_id)
        episodes_data = self.load_episode_progression(show_id)
        chapters = episodes_data.get("chapters", [])
        
        result = {
            "beat_info": beat_info,
            "known_episodes": [],
            "unknown_episodes": [],
            "reached_cliffhangers": [],
            "known_facts": [],
            "available_hooks": []
        }
        
        # Find the current beat's chapter
        for chapter in chapters:
            if chapter.get("beat_id") == beat_info.get("beat_id"):
                episodes = chapter.get("episodes", [])
                
                for ep in episodes:
                    ep_id = ep.get("episode_id", 0)
                    
                    if ep_id <= user_episode:
                        # User has heard this episode
                        result["known_episodes"].append({
                            "episode_id": ep_id,
                            "objective": ep.get("objective", ""),
                            "what_changes": ep.get("what_changes", []),
                            "cliffhanger": ep.get("cliffhanger", ""),
                            "hooks": ep.get("hooks", [])
                        })
                        
                        # Collect cliffhangers
                        if ep.get("cliffhanger"):
                            result["reached_cliffhangers"].append({
                                "episode": ep_id,
                                "cliffhanger": ep["cliffhanger"]
                            })
                        
                        # Collect facts
                        for fact in ep.get("facts_revealed", []):
                            result["known_facts"].append(fact.get("fact", ""))
                        
                        # Collect hooks
                        result["available_hooks"].extend(ep.get("hooks", []))
                    else:
                        # User hasn't heard this yet - can tease but not spoil
                        result["unknown_episodes"].append({
                            "episode_id": ep_id,
                            "hooks": ep.get("hooks", [])  # Can use hooks as teaser
                        })
                
                break
        
        return result
    
    def format_episode_progression_for_prompt(
        self, 
        user_episode: int, 
        show_id: str = "saving_nora"
    ) -> str:
        """
        Format current beat episode progression as a string for LLM prompt.
        """
        data = self.get_current_beat_episodes(user_episode, show_id)
        
        lines = []
        
        # Known episodes
        lines.append("### Episodes user has heard:")
        for ep in data["known_episodes"]:
            marker = "⭐" if ep.get("cliffhanger") else "-"
            lines.append(f"{marker} EP{ep['episode_id']}: {ep['objective']}")
        
        # Reached cliffhangers
        if data["reached_cliffhangers"]:
            lines.append("")
            lines.append("### Key cliffhangers reached:")
            for cliff in data["reached_cliffhangers"]:
                lines.append(f"- EP{cliff['episode']}: \"{cliff['cliffhanger']}\"")
        
        # Known facts
        if data["known_facts"]:
            lines.append("")
            lines.append("### Facts now known to user:")
            for fact in data["known_facts"][:10]:  # Limit to 10
                lines.append(f"- {fact}")
        
        return "\n".join(lines)
    
    # =========================================================================
    # CHARACTER KNOWLEDGE STATE
    # =========================================================================
    
    def get_character_knowledge_at_episode(
        self, 
        character_id: str, 
        user_episode: int,
        show_id: str = "saving_nora"
    ) -> Dict:
        """
        Fetches what a character knows/doesn't know at user's current episode.
        
        Args:
            character_id: Character identifier (e.g., "nora_smith")
            user_episode: User's current episode
            show_id: Show identifier
            
        Returns:
            {
                "beat_id": 3,
                "beat_title": "Athena's Surgery",
                "knows": [...],
                "doesnt_know": [...],
                "can_discuss_freely": [...],
                "must_not_reveal": [...],
                "can_tease": [...],
                "emotional_state": "..."
            }
        """
        journey_data = self.load_character_journey(show_id)
        characters = journey_data.get("characters", {})
        
        # Find the character
        character = characters.get(character_id, {})
        if not character:
            # Try variations
            for key in characters.keys():
                if character_id.lower() in key.lower() or key.lower() in character_id.lower():
                    character = characters[key]
                    break
        
        if not character:
            return {
                "beat_id": None,
                "beat_title": "Unknown",
                "knows": [],
                "doesnt_know": [],
                "can_discuss_freely": [],
                "must_not_reveal": [],
                "can_tease": [],
                "emotional_state": "Unknown"
            }
        
        journey = character.get("journey", [])
        
        # Find the journey entry for user's episode
        for entry in journey:
            ep_range = entry.get("episode_range", {})
            start = ep_range.get("start", 0)
            end = ep_range.get("end", 0)
            
            if start <= user_episode <= end:
                return {
                    "beat_id": entry.get("beat_id"),
                    "beat_title": entry.get("beat_title", ""),
                    "knows": entry.get("knows", []),
                    "doesnt_know": entry.get("doesnt_know", []),
                    "can_discuss_freely": entry.get("can_discuss_freely", []),
                    "must_not_reveal": entry.get("must_not_reveal", []),
                    "can_tease": entry.get("can_tease", []),
                    "emotional_state": entry.get("emotional_state", ""),
                    "relationships": entry.get("relationships", {})
                }
        
        # If beyond all entries, return the last one
        if journey:
            last_entry = journey[-1]
            return {
                "beat_id": last_entry.get("beat_id"),
                "beat_title": last_entry.get("beat_title", ""),
                "knows": last_entry.get("knows", []),
                "doesnt_know": last_entry.get("doesnt_know", []),
                "can_discuss_freely": last_entry.get("can_discuss_freely", []),
                "must_not_reveal": last_entry.get("must_not_reveal", []),
                "can_tease": last_entry.get("can_tease", []),
                "emotional_state": last_entry.get("emotional_state", ""),
                "relationships": last_entry.get("relationships", {})
            }
        
        return {
            "beat_id": None,
            "beat_title": "Unknown",
            "knows": [],
            "doesnt_know": [],
            "can_discuss_freely": [],
            "must_not_reveal": [],
            "can_tease": [],
            "emotional_state": "Unknown"
        }
    
    def format_character_knowledge_for_prompt(
        self, 
        character_id: str, 
        user_episode: int,
        show_id: str = "saving_nora"
    ) -> str:
        """
        Format character knowledge state as a string for LLM prompt.
        """
        knowledge = self.get_character_knowledge_at_episode(character_id, user_episode, show_id)
        
        lines = []
        
        # What character knows
        lines.append("### What YOU know at this point:")
        for item in knowledge.get("knows", [])[:15]:
            lines.append(f"- {item}")
        
        # What character doesn't know
        lines.append("")
        lines.append("### What YOU don't know yet (respond with genuine ignorance if asked):")
        for item in knowledge.get("doesnt_know", [])[:10]:
            lines.append(f"- {item}")
        
        # Can discuss freely
        if knowledge.get("can_discuss_freely"):
            lines.append("")
            lines.append("### Topics you can discuss freely:")
            for item in knowledge["can_discuss_freely"][:10]:
                lines.append(f"- {item}")
        
        # Must not reveal
        if knowledge.get("must_not_reveal"):
            lines.append("")
            lines.append("### Things you MUST NOT reveal:")
            for item in knowledge["must_not_reveal"][:10]:
                lines.append(f"- {item}")
        
        # Can tease
        if knowledge.get("can_tease"):
            lines.append("")
            lines.append("### Things you CAN tease/hint:")
            for item in knowledge["can_tease"][:10]:
                lines.append(f"- {item}")
        
        # Emotional state
        if knowledge.get("emotional_state"):
            lines.append("")
            lines.append(f"### Your emotional state right now:")
            lines.append(knowledge["emotional_state"])
        
        return "\n".join(lines)
    
    # =========================================================================
    # SPOILER RULES & ENGAGEMENT HOOKS
    # =========================================================================
    
    def get_spoiler_rules(
        self, 
        user_episode: int, 
        show_id: str = "saving_nora"
    ) -> Dict:
        """
        Get spoiler prevention rules based on user's episode.
        
        Returns:
            {
                "spoiler_episodes": [...],  # Episodes to never mention
                "spoiler_facts": [...],  # Facts to never reveal
                "engagement_hooks": [...]  # Hooks available to tease
            }
        """
        episodes_data = self.load_episode_progression(show_id)
        chapters = episodes_data.get("chapters", [])
        
        spoiler_episodes = []
        spoiler_facts = []
        engagement_hooks = []
        
        beat_info = self.get_beat_for_episode(user_episode, show_id)
        current_beat_id = beat_info.get("beat_id", 1)
        
        for chapter in chapters:
            chapter_beat_id = chapter.get("beat_id", 0)
            episodes = chapter.get("episodes", [])
            
            for ep in episodes:
                ep_id = ep.get("episode_id", 0)
                
                if ep_id > user_episode:
                    # This is a spoiler episode
                    spoiler_episodes.append({
                        "episode_id": ep_id,
                        "objective": ep.get("objective", "")
                    })
                    
                    # Collect spoiler facts
                    for fact in ep.get("facts_revealed", []):
                        spoiler_facts.append(fact.get("fact", ""))
                    
                    # If it's within the current beat, hooks can be used as teasers
                    if chapter_beat_id == current_beat_id:
                        engagement_hooks.extend(ep.get("hooks", []))
        
        return {
            "spoiler_episodes": spoiler_episodes[:20],  # Limit
            "spoiler_facts": spoiler_facts[:20],
            "engagement_hooks": list(set(engagement_hooks))[:10]  # Dedupe and limit
        }
    
    def format_spoiler_rules_for_prompt(
        self, 
        user_episode: int, 
        show_id: str = "saving_nora"
    ) -> str:
        """
        Format spoiler rules as a string for LLM prompt.
        """
        rules = self.get_spoiler_rules(user_episode, show_id)
        
        lines = []
        
        # Spoiler episodes
        lines.append("### 🚫 NEVER MENTION (User hasn't reached these yet):")
        for ep in rules["spoiler_episodes"][:10]:
            lines.append(f"- EP{ep['episode_id']}: {ep['objective'][:80]}...")
        
        # Spoiler facts
        if rules["spoiler_facts"]:
            lines.append("")
            lines.append("### 🚫 FACTS TO NEVER REVEAL:")
            for fact in rules["spoiler_facts"][:10]:
                lines.append(f"- {fact}")
        
        # Engagement hooks
        if rules["engagement_hooks"]:
            lines.append("")
            lines.append("### ✅ HOOKS YOU CAN TEASE (hint, don't reveal):")
            for hook in rules["engagement_hooks"]:
                lines.append(f"- \"{hook}\"")
        
        return "\n".join(lines)
    
    # =========================================================================
    # COMPLETE CONTEXT BUILDER
    # =========================================================================
    
    def build_complete_context(
        self,
        character_id: str,
        user_episode: int,
        post_episode: int,
        show_id: str = "saving_nora"
    ) -> Dict:
        """
        Build complete context for character response generation.
        
        This is the main method that aggregates all context.
        
        Args:
            character_id: Character identifier (e.g., "nora_smith")
            user_episode: How far the user has progressed
            post_episode: What episode the post is about
            show_id: Show identifier
            
        Returns:
            Complete context dictionary with all sections
        """
        beat_info = self.get_beat_for_episode(user_episode, show_id)
        
        return {
            "character_id": character_id,
            "user_episode": user_episode,
            "post_episode": post_episode,
            "show_id": show_id,
            
            # 1. Character Persona
            "persona": self.get_character_persona(character_id, show_id),
            "persona_formatted": self.format_character_persona_for_prompt(character_id, show_id),
            "voice_rules": self.format_voice_rules_for_prompt(character_id, show_id),
            
            # 2. Previous Plot Summaries
            "previous_plots": self.get_previous_plot_summaries(
                beat_info.get("beat_id", 1), show_id
            ),
            "previous_plots_formatted": self.format_previous_plots_for_prompt(
                beat_info.get("beat_id", 1), show_id
            ),
            
            # 3. Current Beat Episode Progression
            "current_beat": beat_info,
            "episode_progression": self.get_current_beat_episodes(user_episode, show_id),
            "episode_progression_formatted": self.format_episode_progression_for_prompt(
                user_episode, show_id
            ),
            
            # 4. Spoiler Rules & Engagement Hooks
            "spoiler_rules": self.get_spoiler_rules(user_episode, show_id),
            "spoiler_rules_formatted": self.format_spoiler_rules_for_prompt(user_episode, show_id),
            
            # 5. Character Knowledge State
            "character_knowledge": self.get_character_knowledge_at_episode(
                character_id, user_episode, show_id
            ),
            "character_knowledge_formatted": self.format_character_knowledge_for_prompt(
                character_id, user_episode, show_id
            )
        }


# Convenience function for quick access
def get_story_context(
    character_id: str,
    user_episode: int,
    post_episode: int,
    show_id: str = "saving_nora",
    context_dir: str = "context"
) -> Dict:
    """
    Convenience function to get complete story context.
    
    Args:
        character_id: Character identifier
        user_episode: User's current episode
        post_episode: Episode the post is about
        show_id: Show identifier
        context_dir: Path to context directory
        
    Returns:
        Complete context dictionary
    """
    service = StoryContextService(context_dir)
    return service.build_complete_context(
        character_id=character_id,
        user_episode=user_episode,
        post_episode=post_episode,
        show_id=show_id
    )


if __name__ == "__main__":
    # Test the service
    service = StoryContextService()
    
    print("=" * 60)
    print("Testing Story Context Service")
    print("=" * 60)
    
    # Test beat mapping
    print("\n1. Episode to Beat Mapping:")
    beat = service.get_beat_for_episode(25)
    print(f"   Episode 25 -> Beat {beat['beat_id']}: {beat['beat_title']}")
    
    # Test character persona
    print("\n2. Character Persona (Nora):")
    print(service.format_character_persona_for_prompt("nora_smith")[:200] + "...")
    
    # Test previous plots
    print("\n3. Previous Plot Summaries (Beat 3):")
    print(service.format_previous_plots_for_prompt(3)[:300] + "...")
    
    # Test character knowledge
    print("\n4. Character Knowledge (Nora at EP25):")
    print(service.format_character_knowledge_for_prompt("nora_smith", 25)[:300] + "...")
    
    # Test complete context
    print("\n5. Complete Context Build:")
    context = service.build_complete_context("nora_smith", 25, 23)
    print(f"   Keys: {list(context.keys())}")
