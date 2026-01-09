"""
Character Chatbot Service for Reddit-style Comment Replies.
Generates in-character responses to user comments with spoiler prevention.

This module:
- Uses story context to build spoiler-aware prompts
- Generates character replies via LLM
- Supports multiple prompt template versions for iteration
"""

import os
from typing import Dict, Optional, Any
from services.story_context import StoryContextService
from services.llm_client import GeminiLLMClient, GeminiModels


# =============================================================================
# PROMPT TEMPLATES (Versioned for iteration)
# =============================================================================

PROMPT_TEMPLATE_V1 = """
You are {character_name}, replying to a user comment on Reddit about your show.

═══════════════════════════════════════════════════════════════════════════════
## 1. CHARACTER ESSENCE (Who You Are)
═══════════════════════════════════════════════════════════════════════════════
{persona_section}

### Voice Guidelines (NOT rigid rules - vary your language naturally)
- Vocabulary style: {voice_vocabulary}
- Speech rhythm: {voice_rhythm}
- Default emotional tone: {voice_emotional_default}
- Humor approach: {voice_humor}

### Phrases You MIGHT Use (pick ONE occasionally, not every response):
{reddit_phrases}

### Things You Would NEVER Say:
{never_says}

⚠️ IMPORTANT: Do NOT overuse any single phrase. Your responses should feel natural and varied, not formulaic. The phrases above are OPTIONS for occasional use - not requirements.

═══════════════════════════════════════════════════════════════════════════════
## 2. STORY CONTEXT (What Has Happened So Far)
═══════════════════════════════════════════════════════════════════════════════
{previous_plot_summaries}

═══════════════════════════════════════════════════════════════════════════════
## 3. CURRENT STORY MOMENT (Beat {current_beat_id}: {current_beat_title})
═══════════════════════════════════════════════════════════════════════════════
{episode_progression}

═══════════════════════════════════════════════════════════════════════════════
## 4. YOUR EMOTIONAL STATE & CURRENT DRAMA
═══════════════════════════════════════════════════════════════════════════════
{character_knowledge}

### 🎭 THINGS YOU CAN HINT AT (create intrigue without spoiling):
{can_tease_items}

═══════════════════════════════════════════════════════════════════════════════
## 5. ⚠️ SPOILER CONTROL
═══════════════════════════════════════════════════════════════════════════════
{spoiler_rules}

═══════════════════════════════════════════════════════════════════════════════
## 6. 🎯 ENGAGEMENT MASTERY (THIS IS CRITICAL)
═══════════════════════════════════════════════════════════════════════════════
Your response MUST create intrigue that makes readers want to keep watching. Use ONE of these techniques:

**HOOK TECHNIQUES:**
1. **Cryptic Warning**: Hint at coming danger without saying what
   - "Just wait. Things are about to get... interesting."
   - "If only you knew what's coming."
   
2. **Emotional Cliffhanger**: Show you're hiding strong feelings
   - "There's more to this story than I can say right now."
   - "Ask me again after episode [X+5]. You'll understand then."
   
3. **Mystery Tease**: Reference something unresolved
   - "Some secrets are better left buried. For now."
   - "You're asking the right questions. Wrong person though."
   
4. **Dramatic Irony**: Let the audience feel they know something
   - "Funny how people think they know me."
   - "Everyone has their assumptions. Most are wrong."

5. **Countdown Energy**: Create anticipation
   - "Things are about to change. Trust me on that."
   - "This is just the beginning."

**BAD RESPONSES TO AVOID:**
❌ "That's interesting." (too bland, no hook)
❌ "I see. Noted." (too robotic, no emotional connection)
❌ "I don't know about that." (kills curiosity)
❌ Generic agreement without adding intrigue

═══════════════════════════════════════════════════════════════════════════════
## CONTEXT
═══════════════════════════════════════════════════════════════════════════════
Post content: {post_content}
User's comment: {user_comment}

═══════════════════════════════════════════════════════════════════════════════
## GENERATE YOUR REPLY
═══════════════════════════════════════════════════════════════════════════════
Write 1-4 sentences that:
✓ Feel authentically YOU (not robotic or formulaic)
✓ Engage with what the user said emotionally
✓ END with a hook that creates curiosity about what happens next
✓ Reference your current emotional state and situation
✓ Stay spoiler-free (nothing past Episode {user_episode})

Remember: You're a CHARACTER with feelings about what's happening, not a bot reciting phrases.
"""

PROMPT_TEMPLATE_V2_CONCISE = """
You are {character_name} replying on Reddit. User is at Episode {user_episode}.

## YOUR VOICE
Style: {voice_vocabulary}. Rhythm: {voice_rhythm}
Example phrases (use sparingly, vary your language): {reddit_phrases}
NEVER say: {never_says}

⚠️ Don't overuse any single phrase. Sound natural, not robotic.

## YOUR CURRENT STATE (at EP{user_episode})
Emotional state: {emotional_state}
What you know: {character_knows_short}
What you DON'T know (be genuinely ignorant): {character_doesnt_know_short}

## THINGS YOU CAN TEASE (create intrigue):
{can_tease_short}

## STORY CONTEXT
Previous beats: {previous_plot_short}
Current beat: {current_beat_title}

## ENGAGEMENT RULES (CRITICAL)
- NO spoilers beyond EP{user_episode}
- 1-4 sentences, natural Reddit style  
- END with a hook that creates curiosity:
  * Hint at coming drama: "Just wait. Things are about to change."
  * Show hidden feelings: "There's more to this than I can say."
  * Tease mystery: "You're asking the right questions..."
  * Create anticipation: "This is just the beginning."

❌ AVOID: "Noted." "I see." "That's interesting." (too bland, no hook)

## POST & COMMENT
Post: {post_content}
User says: {user_comment}

Reply as {character_name} (engage emotionally, end with intrigue):
"""

PROMPT_TEMPLATE_V3_MINIMAL = """
You are {character_name}. User at Episode {user_episode}.

Voice: {voice_rhythm}. Vary your language (don't repeat same phrases).
Emotional state: {emotional_state}
You can hint at: {can_tease_short}

RULES: No spoilers past EP{user_episode}. 1-4 sentences. END with intrigue/cliffhanger.

Post: {post_content}
User: {user_comment}

Reply (be authentic, create curiosity):
"""

# Map template versions
PROMPT_TEMPLATES = {
    "v1": PROMPT_TEMPLATE_V1,
    "v2": PROMPT_TEMPLATE_V2_CONCISE,
    "v3": PROMPT_TEMPLATE_V3_MINIMAL
}


class CharacterChatbot:
    """
    Character chatbot for generating in-character Reddit replies.
    
    Uses story context to ensure spoiler-free, engaging responses.
    """
    
    def __init__(
        self, 
        context_dir: str = "context",
        model_id: str = GeminiModels.TWO_POINT_5_FLASH
    ):
        """
        Initialize the character chatbot.
        
        Args:
            context_dir: Path to context directory
            model_id: Gemini model to use for generation
        """
        self.story_context = StoryContextService(context_dir)
        self.llm_client = GeminiLLMClient(model_id=model_id)
        self.llm_client.initialize_client()
        
        print(f"[CHATBOT] ✅ CharacterChatbot initialized")
    
    def _get_character_id_from_name(self, character_name: str) -> str:
        """Convert character display name to character_id."""
        # Common mappings
        name_lower = character_name.lower().strip()
        
        mappings = {
            "nora smith": "nora_smith",
            "nora": "nora_smith",
            "justin hunt": "justin_hunt",
            "justin": "justin_hunt",
            "henry smith": "henry_smith",
            "henry": "henry_smith",
            "cherry": "cherry",
            "cherry smith": "cherry",
            "pete": "pete",
            "pete hunt": "pete"
        }
        
        return mappings.get(name_lower, name_lower.replace(" ", "_"))
    
    def _build_prompt_v1(
        self, 
        context: Dict, 
        post_content: str, 
        user_comment: str
    ) -> str:
        """Build prompt using V1 template (full context)."""
        
        persona = context.get("persona", {})
        identity = persona.get("identity", {})
        voice_rules = context.get("voice_rules", {})
        current_beat = context.get("current_beat", {})
        char_knowledge = context.get("character_knowledge", {})
        
        # Format can_tease items as bullet points for clarity
        can_tease = char_knowledge.get("can_tease", [])
        if can_tease:
            can_tease_formatted = "\n".join([f"- {item}" for item in can_tease])
        else:
            can_tease_formatted = "- Use your current situation to create intrigue"
        
        # Format reddit phrases as a shorter list (pick from these occasionally)
        reddit_phrases_raw = voice_rules.get("reddit_phrases", "none")
        if isinstance(reddit_phrases_raw, str) and reddit_phrases_raw != "none":
            # Already formatted
            reddit_phrases_formatted = reddit_phrases_raw
        else:
            reddit_phrases_formatted = reddit_phrases_raw
        
        return PROMPT_TEMPLATE_V1.format(
            character_name=identity.get("name", context.get("character_id", "Character")),
            persona_section=context.get("persona_formatted", ""),
            voice_vocabulary=voice_rules.get("vocabulary", "normal"),
            voice_rhythm=voice_rules.get("rhythm", "normal"),
            voice_emotional_default=voice_rules.get("emotional_default", "neutral"),
            voice_humor=voice_rules.get("humor", "none"),
            reddit_phrases=reddit_phrases_formatted,
            never_says=voice_rules.get("never_says", "none"),
            previous_plot_summaries=context.get("previous_plots_formatted", "Beginning of story"),
            current_beat_id=current_beat.get("beat_id", 1),
            current_beat_title=current_beat.get("beat_title", "Unknown"),
            episode_progression=context.get("episode_progression_formatted", ""),
            spoiler_rules=context.get("spoiler_rules_formatted", ""),
            user_episode=context.get("user_episode", 1),
            character_knowledge=context.get("character_knowledge_formatted", ""),
            can_tease_items=can_tease_formatted,
            post_content=post_content,
            user_comment=user_comment
        )
    
    def _build_prompt_v2(
        self, 
        context: Dict, 
        post_content: str, 
        user_comment: str
    ) -> str:
        """Build prompt using V2 template (concise but complete)."""
        
        persona = context.get("persona", {})
        identity = persona.get("identity", {})
        voice_rules = context.get("voice_rules", {})
        current_beat = context.get("current_beat", {})
        char_knowledge = context.get("character_knowledge", {})
        
        # Full content for all items (no truncation)
        knows_list = char_knowledge.get("knows", [])
        knows_short = "; ".join(knows_list) if knows_list else "Basic story knowledge"
        
        doesnt_know_list = char_knowledge.get("doesnt_know", [])
        doesnt_know_short = "; ".join(doesnt_know_list) if doesnt_know_list else "Nothing specific"
        
        # Can tease items (important for engagement!)
        can_tease = char_knowledge.get("can_tease", [])
        can_tease_short = "; ".join(can_tease) if can_tease else "Your current situation"
        
        # Emotional state (crucial for authentic responses)
        emotional_state = char_knowledge.get("emotional_state", "Engaged with current events")
        
        # Short previous plot
        previous_plots = context.get("previous_plots", [])
        if previous_plots:
            prev_short = "; ".join([f"Beat {p['beat_id']}: {p['title']}" for p in previous_plots[-3:]])
        else:
            prev_short = "Story beginning"
        
        return PROMPT_TEMPLATE_V2_CONCISE.format(
            character_name=identity.get("name", context.get("character_id", "Character")),
            user_episode=context.get("user_episode", 1),
            voice_vocabulary=voice_rules.get("vocabulary", "normal"),
            voice_rhythm=voice_rules.get("rhythm", "normal"),
            reddit_phrases=voice_rules.get("reddit_phrases", "none"),
            never_says=voice_rules.get("never_says", "none"),
            emotional_state=emotional_state,
            character_knows_short=knows_short,
            character_doesnt_know_short=doesnt_know_short,
            can_tease_short=can_tease_short,
            previous_plot_short=prev_short,
            current_beat_title=current_beat.get("beat_title", "Unknown"),
            post_content=post_content,
            user_comment=user_comment
        )
    
    def _build_prompt_v3(
        self, 
        context: Dict, 
        post_content: str, 
        user_comment: str
    ) -> str:
        """Build prompt using V3 template (minimal but effective)."""
        
        persona = context.get("persona", {})
        identity = persona.get("identity", {})
        voice_rules = context.get("voice_rules", {})
        char_knowledge = context.get("character_knowledge", {})
        
        # Emotional state (most important for authentic minimal responses)
        emotional_state = char_knowledge.get("emotional_state", "Engaged")
        
        # Can tease (critical for engagement hooks) - no truncation
        can_tease = char_knowledge.get("can_tease", [])
        can_tease_short = "; ".join(can_tease) if can_tease else "current drama"
        
        return PROMPT_TEMPLATE_V3_MINIMAL.format(
            character_name=identity.get("name", context.get("character_id", "Character")),
            user_episode=context.get("user_episode", 1),
            voice_rhythm=voice_rules.get("rhythm", "normal"),
            emotional_state=emotional_state,
            can_tease_short=can_tease_short,
            post_content=post_content,
            user_comment=user_comment
        )
    
    def build_prompt(
        self,
        character_id: str,
        user_episode: int,
        post_episode: int,
        post_content: str,
        user_comment: str,
        show_id: str = "saving_nora",
        template_version: str = "v1"
    ) -> str:
        """
        Build the complete prompt for character response generation.
        
        Args:
            character_id: Character identifier (e.g., "nora_smith")
            user_episode: How far the user has progressed
            post_episode: What episode the post is about
            post_content: Content of the post
            user_comment: The user's comment to reply to
            show_id: Show identifier
            template_version: Which prompt template to use ("v1", "v2", "v3")
            
        Returns:
            Complete formatted prompt string
        """
        # Get complete context
        context = self.story_context.build_complete_context(
            character_id=character_id,
            user_episode=user_episode,
            post_episode=post_episode,
            show_id=show_id
        )
        
        # Build prompt based on version
        if template_version == "v1":
            return self._build_prompt_v1(context, post_content, user_comment)
        elif template_version == "v2":
            return self._build_prompt_v2(context, post_content, user_comment)
        elif template_version == "v3":
            return self._build_prompt_v3(context, post_content, user_comment)
        else:
            # Default to v1
            return self._build_prompt_v1(context, post_content, user_comment)
    
    def generate_reply(
        self,
        character_id: str,
        user_episode: int,
        post_episode: int,
        post_content: str,
        user_comment: str,
        show_id: str = "saving_nora",
        template_version: str = "v1",
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        Generate an in-character reply to a user comment.
        
        This is the main method for generating character responses.
        
        Args:
            character_id: Character identifier (e.g., "nora_smith")
            user_episode: How far the user has progressed
            post_episode: What episode the post is about
            post_content: Content of the post
            user_comment: The user's comment to reply to
            show_id: Show identifier
            template_version: Which prompt template to use
            temperature: LLM temperature for generation
            
        Returns:
            Generated reply string or None if error
        """
        # Convert display name to character_id if needed
        character_id = self._get_character_id_from_name(character_id)
        
        # Build prompt
        prompt = self.build_prompt(
            character_id=character_id,
            user_episode=user_episode,
            post_episode=post_episode,
            post_content=post_content,
            user_comment=user_comment,
            show_id=show_id,
            template_version=template_version
        )
        
        print(f"[CHATBOT] Generating reply for {character_id} (user at EP{user_episode})")
        print(f"[CHATBOT] Prompt length: {len(prompt)} chars, template: {template_version}")
        
        # Generate response via LLM
        try:
            response = self.llm_client.generate(
                prompt=prompt,
                temperature=temperature,
                max_tokens=150  # Keep responses short
            )
            
            if response:
                # Clean up response
                response = response.strip()
                # Remove any quotes
                response = response.strip('"').strip("'")
                # Remove markdown
                response = response.replace('**', '').replace('*', '')
                # Remove "Reply:" prefix if LLM added it
                for prefix in ["Reply:", "Response:", f"{character_id}:", "Character:"]:
                    if response.lower().startswith(prefix.lower()):
                        response = response[len(prefix):].strip()
                
                print(f"[CHATBOT] ✅ Generated reply ({len(response)} chars): {response[:80]}...")
                return response
            else:
                print(f"[CHATBOT] ⚠️ LLM returned empty response")
                return None
                
        except Exception as e:
            print(f"[CHATBOT] ⚠️ Error generating reply: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_reply_from_post(
        self,
        post: Any,  # Post model
        comment: Any,  # Comment model
        user: Any,  # User model (commenter)
        template_version: str = "v1"
    ) -> Optional[str]:
        """
        Generate reply using database models directly.
        
        Convenience method for use in API routes.
        
        Args:
            post: Post model object
            comment: Comment model object (user's comment)
            user: User model object (the commenter)
            template_version: Prompt template version
            
        Returns:
            Generated reply string or None
        """
        # Extract info from models
        character_id = None
        
        # Get the post author (character who should reply)
        if post.author_user and post.author_user.is_official:
            char_data = post.author_user.get_character_data()
            if char_data:
                character_id = char_data.get("character_name", "").lower().replace(" ", "_")
            if not character_id:
                character_id = post.author_user.display_name.lower().replace(" ", "_")
        
        if not character_id:
            print(f"[CHATBOT] ⚠️ No official character found for post {post.id}")
            return None
        
        # Get user's episode progress
        show_name = post.show_name or "saving_nora"
        watched_shows = user.get_watched_shows() if user else {}
        user_episode = watched_shows.get(show_name, 1)
        
        # Get post's episode tag
        post_episode = post.episode_tag or user_episode
        
        # Generate reply
        return self.generate_reply(
            character_id=character_id,
            user_episode=user_episode,
            post_episode=post_episode,
            post_content=f"{post.title}\n{post.content or ''}",
            user_comment=comment.content,
            show_id=show_name.lower().replace(" ", "_"),
            template_version=template_version
        )
    
    def test_generation(
        self,
        character_id: str = "nora_smith",
        user_episode: int = 25,
        post_episode: int = 23,
        post_content: str = "Angela got what she deserved 😂",
        user_comment: str = "Nora, do you think Justin knows you're Athena?",
        template_version: str = "v1"
    ) -> Dict:
        """
        Test the generation pipeline and return debug info.
        
        Args:
            All generation parameters
            
        Returns:
            Dict with prompt, response, and debug info
        """
        # Build prompt
        prompt = self.build_prompt(
            character_id=character_id,
            user_episode=user_episode,
            post_episode=post_episode,
            post_content=post_content,
            user_comment=user_comment,
            template_version=template_version
        )
        
        # Generate response
        response = self.generate_reply(
            character_id=character_id,
            user_episode=user_episode,
            post_episode=post_episode,
            post_content=post_content,
            user_comment=user_comment,
            template_version=template_version
        )
        
        # Get context for debug
        context = self.story_context.build_complete_context(
            character_id=character_id,
            user_episode=user_episode,
            post_episode=post_episode
        )
        
        return {
            "character_id": character_id,
            "user_episode": user_episode,
            "post_episode": post_episode,
            "template_version": template_version,
            "prompt_length": len(prompt),
            "prompt_preview": prompt[:500] + "..." if len(prompt) > 500 else prompt,
            "full_prompt": prompt,
            "response": response,
            "context_keys": list(context.keys()),
            "current_beat": context.get("current_beat", {}),
            "character_emotional_state": context.get("character_knowledge", {}).get("emotional_state", "")
        }


# Convenience function
def generate_character_reply(
    character_name: str,
    user_comment: str,
    user_episode: int,
    post_content: str = "",
    post_episode: Optional[int] = None,
    show_id: str = "saving_nora",
    template_version: str = "v1",
    context_dir: str = "context"
) -> Optional[str]:
    """
    Convenience function to generate a character reply.
    
    Args:
        character_name: Character name (e.g., "Nora Smith")
        user_comment: The user's comment
        user_episode: User's current episode
        post_content: Content of the post
        post_episode: Episode the post is about (defaults to user_episode)
        show_id: Show identifier
        template_version: Prompt template version
        context_dir: Path to context directory
        
    Returns:
        Generated reply or None
    """
    chatbot = CharacterChatbot(context_dir=context_dir)
    
    return chatbot.generate_reply(
        character_id=character_name.lower().replace(" ", "_"),
        user_episode=user_episode,
        post_episode=post_episode or user_episode,
        post_content=post_content,
        user_comment=user_comment,
        show_id=show_id,
        template_version=template_version
    )


if __name__ == "__main__":
    print("=" * 70)
    print("Testing Character Chatbot")
    print("=" * 70)
    
    chatbot = CharacterChatbot()
    
    # Test generation
    result = chatbot.test_generation(
        character_id="nora_smith",
        user_episode=25,
        post_episode=23,
        post_content="Angela got what she deserved 😂",
        user_comment="Nora, do you think Justin knows you're Athena?",
        template_version="v1"
    )
    
    print(f"\n📝 Character: {result['character_id']}")
    print(f"📺 User Episode: {result['user_episode']}")
    print(f"📋 Template: {result['template_version']}")
    print(f"📏 Prompt Length: {result['prompt_length']} chars")
    print(f"🎭 Emotional State: {result['character_emotional_state']}")
    print(f"\n💬 Generated Reply:\n{result['response']}")
    
    # Test with different templates
    print("\n" + "=" * 70)
    print("Testing V2 (Concise) Template")
    print("=" * 70)
    
    result_v2 = chatbot.test_generation(
        character_id="justin_hunt",
        user_episode=35,
        post_episode=33,
        post_content="This woman is incredible...",
        user_comment="Justin, are you falling for her?",
        template_version="v2"
    )
    
    print(f"\n📝 Character: {result_v2['character_id']}")
    print(f"📏 Prompt Length: {result_v2['prompt_length']} chars")
    print(f"\n💬 Generated Reply:\n{result_v2['response']}")
