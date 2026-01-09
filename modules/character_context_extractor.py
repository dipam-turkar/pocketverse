"""
Character Context Extractor
Utility functions to extract specific character data sections for different use cases.
Helps manage token costs by providing only relevant context.
"""

import json
import os
from typing import Dict, List, Any, Optional


class CharacterContextExtractor:
    """Extract and format character data for different LLM use cases."""
    
    def __init__(self, context_dir: str = "context/characters"):
        self.context_dir = context_dir
        self._characters_cache: Dict[str, Dict] = {}
    
    def load_character(self, character_name: str) -> Dict[str, Any]:
        """Load character data from JSON file."""
        if character_name in self._characters_cache:
            return self._characters_cache[character_name]
        
        safe_name = character_name.replace(" ", "_").lower()
        file_path = os.path.join(self.context_dir, f"{safe_name}.json")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Character file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self._characters_cache[character_name] = data
        return data
    
    def get_minimal_context(self, character_name: str) -> Dict[str, Any]:
        """
        Get minimal context for fast/cheap responses.
        Includes only essential voice and interaction rules.
        """
        char_data = self.load_character(character_name)
        
        return {
            "meta": char_data.get("meta", {}),
            "character_snapshot": char_data.get("1) Character Snapshot", {}),
            "voice_dna": {
                "sentence_style": char_data.get("2) Voice DNA", {}).get("Sentence Style", ""),
                "tells_verbal_tics": char_data.get("2) Voice DNA", {}).get("Tells & Verbal Tics", ""),
                "never_does": char_data.get("2) Voice DNA", {}).get("What She NEVER Does in Speech", 
                                                                      char_data.get("2) Voice DNA", {}).get("What He NEVER Does in Speech", ""))
            },
            "interaction_rules": {
                "dos": char_data.get("4) Interaction Rules (Chatbot Guardrails)", {}).get("Tone Rules: DOs", ""),
                "donts": char_data.get("4) Interaction Rules (Chatbot Guardrails)", {}).get("Tone Rules: DON'Ts", ""),
                "response_patterns": {
                    "personal_questions": char_data.get("4) Interaction Rules (Chatbot Guardrails)", {}).get("Personal Questions: Response Patterns", ""),
                    "if_insulted": char_data.get("4) Interaction Rules (Chatbot Guardrails)", {}).get("If User Insults Her: Response Patterns",
                                                                                                        char_data.get("4) Interaction Rules (Chatbot Guardrails)", {}).get("If User Insults Him: Response Patterns", "")),
                    "if_vulnerable": char_data.get("4) Interaction Rules (Chatbot Guardrails)", {}).get("If User is Vulnerable/Sad: Response Patterns", "")
                }
            },
            "canon_knowledge": {
                "known_facts": char_data.get("5) Canon Knowledge Boundaries", {}).get("Known Facts (EP001-100 confirmed)", ""),
                "unknown_templates": char_data.get("5) Canon Knowledge Boundaries", {}).get("Templates for Unknown Questions", "")
            }
        }
    
    def get_comment_response_context(self, character_name: str) -> Dict[str, Any]:
        """
        Get context optimized for generating comment responses (chatbot).
        Includes voice, interaction rules, and dialogue examples.
        """
        char_data = self.load_character(character_name)
        minimal = self.get_minimal_context(character_name)
        
        # Add dialogue examples and additional interaction details
        minimal["dialogue_examples"] = char_data.get("6) Dialogue Examples", {})
        minimal["interaction_rules"]["how_treats_people"] = char_data.get("4) Interaction Rules (Chatbot Guardrails)", {}).get("How She Treats Different People",
                                                                                                                                char_data.get("4) Interaction Rules (Chatbot Guardrails)", {}).get("How He Treats Different People", ""))
        minimal["interaction_rules"]["conflict_style"] = char_data.get("4) Interaction Rules (Chatbot Guardrails)", {}).get("Conflict Style & Escalation Ladder", "")
        
        return minimal
    
    def get_post_generation_context(self, character_name: str) -> Dict[str, Any]:
        """
        Get context optimized for generating social media posts.
        Includes Reddit Voice Pack and voice style.
        """
        char_data = self.load_character(character_name)
        
        return {
            "meta": char_data.get("meta", {}),
            "character_snapshot": char_data.get("1) Character Snapshot", {}),
            "reddit_voice_pack": char_data.get("7) Reddit Voice Pack", {}),
            "voice_dna": {
                "sentence_style": char_data.get("2) Voice DNA", {}).get("Sentence Style", ""),
                "humor_type": char_data.get("2) Voice DNA", {}).get("Humor Type", ""),
                "swearing_slang": char_data.get("2) Voice DNA", {}).get("Swearing/Slang", ""),
                "emotional_register": char_data.get("2) Voice DNA", {}).get("Signature Emotional Register", "")
            },
            "dialogue_examples": char_data.get("6) Dialogue Examples", {})
        }
    
    def get_full_context(self, character_name: str) -> Dict[str, Any]:
        """Get full character context (all sections except prompt assets)."""
        char_data = self.load_character(character_name)
        
        # Remove prompt assets (redundant, can be generated from other sections)
        result = {k: v for k, v in char_data.items() if k != "8) Prompt Assets"}
        return result
    
    def format_for_llm_prompt(self, context: Dict[str, Any], format_type: str = "markdown") -> str:
        """
        Format character context as a string for LLM prompt.
        
        Args:
            context: Character context dictionary
            format_type: "markdown" or "json"
        """
        if format_type == "json":
            return json.dumps(context, indent=2, ensure_ascii=False)
        
        # Markdown format
        lines = []
        
        if "meta" in context:
            lines.append(f"# {context['meta'].get('name', 'Character')}")
            lines.append(f"**Source:** {context['meta'].get('source', 'Unknown')}")
            lines.append(f"**Scope:** {context['meta'].get('scope', 'Unknown')}")
            lines.append("")
        
        for section_name, section_data in context.items():
            if section_name == "meta":
                continue
            
            # Format section name
            clean_name = section_name.replace(")", "").replace("(", "").title()
            lines.append(f"## {clean_name}")
            lines.append("")
            
            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    if isinstance(value, (dict, list)):
                        lines.append(f"### {key}")
                        lines.append("")
                        if isinstance(value, list):
                            for item in value:
                                lines.append(f"- {item}")
                        else:
                            lines.append(json.dumps(value, indent=2, ensure_ascii=False))
                        lines.append("")
                    else:
                        lines.append(f"**{key}:** {value}")
                        lines.append("")
            elif isinstance(section_data, list):
                for item in section_data:
                    lines.append(f"- {item}")
                lines.append("")
            else:
                lines.append(str(section_data))
                lines.append("")
        
        return "\n".join(lines)
    
    def get_available_characters(self) -> List[str]:
        """Get list of available character names."""
        if not os.path.exists(self.context_dir):
            return []
        
        characters = []
        for filename in os.listdir(self.context_dir):
            if filename.endswith(".json") and filename != "all_characters.json":
                char_name = filename.replace(".json", "").replace("_", " ").upper()
                characters.append(char_name)
        
        return characters


# Convenience functions
def get_comment_context(character_name: str, context_dir: str = "context/characters") -> str:
    """Quick function to get formatted comment response context."""
    extractor = CharacterContextExtractor(context_dir)
    context = extractor.get_comment_response_context(character_name)
    return extractor.format_for_llm_prompt(context, format_type="markdown")


def get_post_context(character_name: str, context_dir: str = "context/characters") -> str:
    """Quick function to get formatted post generation context."""
    extractor = CharacterContextExtractor(context_dir)
    context = extractor.get_post_generation_context(character_name)
    return extractor.format_for_llm_prompt(context, format_type="markdown")


if __name__ == "__main__":
    # Example usage
    extractor = CharacterContextExtractor()
    
    print("Available characters:", extractor.get_available_characters())
    print("\n" + "="*60)
    
    # Example: Get comment response context for Nora
    print("\n### Comment Response Context (Nora Smith):")
    print(get_comment_context("NORA SMITH")[:500] + "...")
    
    print("\n" + "="*60)
    
    # Example: Get post generation context
    print("\n### Post Generation Context (Nora Smith):")
    print(get_post_context("NORA SMITH")[:500] + "...")
