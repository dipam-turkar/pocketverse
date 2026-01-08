"""
Automatic comment generation service for official characters.
Generates comments based on character personas from PromoCanon data.
Uses LLM (Gemini) to generate plot-relevant comments.
"""
import os
import random
from typing import List, Dict, Optional, Any
from models import User, Post, Comment
from extensions import db
from services.llm_client import GeminiLLMClient, GeminiModels


class CommentGenerator:
    """Service for generating automatic comments from official characters"""
    
    def __init__(self, canon_directory: Optional[str] = None):
        self.canon_directory = canon_directory
        self.canon_loader = None
        self.llm_client = None
        
        # Initialize PromoCanon loader if directory provided
        if canon_directory:
            try:
                from modules.promo_canon_parser import PromoCanonLoader
                self.canon_loader = PromoCanonLoader(canon_directory)
                print(f"[COMMENT_GEN] ✅ PromoCanon loader initialized from: {canon_directory}")
            except Exception as e:
                print(f"[COMMENT_GEN] ⚠️ Failed to initialize PromoCanon loader: {e}")
        
        # Initialize LLM client
        self.initialize_llm()
    
    def initialize_llm(self):
        """Initialize LLM client for comment generation"""
        try:
            self.llm_client = GeminiLLMClient(model_id=GeminiModels.TWO_POINT_5_FLASH)
            self.llm_client.initialize_client()
            if self.llm_client.gemini_client:
                print(f"[COMMENT_GEN] ✅ LLM client initialized successfully")
            else:
                print(f"[COMMENT_GEN] ⚠️ LLM client initialization failed")
                self.llm_client = None
        except Exception as e:
            print(f"[COMMENT_GEN] ⚠️ Failed to initialize LLM client: {e}")
            import traceback
            traceback.print_exc()
            self.llm_client = None
    
    def get_official_characters(self) -> List[User]:
        """Get all official characters/users"""
        return User.query.filter_by(is_official=True).all()
    
    def get_character_persona(self, character: User) -> Dict[str, Any]:
        """Extract character persona from PromoCanon or character_data"""
        persona = {}
        
        # Get character name first
        char_data = character.get_character_data()
        char_name = char_data.get('character_name') if char_data else None
        if not char_name:
            char_name = character.display_name
        
        # Try to get from PromoCanon first (this has the most detailed character info)
        if self.canon_loader:
            try:
                characters = self.canon_loader.load_characters()
                
                # Try exact match first
                if char_name in characters:
                    canon_char = characters[char_name]
                    persona = {
                        'name': char_name,
                        'description': canon_char.get('description', ''),
                        'personality': canon_char.get('personality', ''),
                        'show_name': char_data.get('show_name') if char_data else None,
                    }
                    print(f"[COMMENT_GEN] Found PromoCanon data for {char_name}")
                else:
                    # Try partial match (first name only)
                    first_name = char_name.split()[0] if ' ' in char_name else char_name
                    for canon_name, canon_data in characters.items():
                        if canon_name.split()[0] == first_name or first_name in canon_name:
                            persona = {
                                'name': char_name,
                                'description': canon_data.get('description', ''),
                                'personality': canon_data.get('personality', ''),
                                'show_name': char_data.get('show_name') if char_data else None,
                            }
                            print(f"[COMMENT_GEN] Found PromoCanon data for {char_name} (matched {canon_name})")
                            break
            except Exception as e:
                print(f"[COMMENT_GEN] Error loading PromoCanon data: {e}")
                import traceback
                traceback.print_exc()
        
        # Fallback to character_data from user model
        if not persona or not persona.get('description'):
            persona = {
                'name': char_name,
                'description': char_data.get('bio', '') if char_data else '',
                'personality': char_data.get('personality', '') if char_data else '',
                'show_name': char_data.get('show_name') if char_data else None,
            }
        
        return persona
    
    def should_character_comment(self, character: User, post: Post, trigger_type: str = "post_created", 
                                 user_comment: Optional[Comment] = None) -> bool:
        """
        Determine if a character should comment based on their persona and the context.
        Returns True if character should comment, False otherwise.
        
        Rules:
        1. Only official characters who are in the story will comment
        2. They will only comment if the comment/post and their description/persona allow that
        """
        persona = self.get_character_persona(character)
        char_name = persona.get('name', character.display_name)
        char_data = character.get_character_data()
        description = persona.get('description', '')
        personality = persona.get('personality', '')
        
        print(f"[COMMENT_GEN] Checking if {char_name} should comment on post {post.id} (trigger: {trigger_type})")
        
        # Rule 1: Only official characters
        if not character.is_official:
            print(f"[COMMENT_GEN] ❌ {char_name} is not an official character - skipping")
            return False
        
        # Rule 2: Character must have PromoCanon description - if no description, won't comment
        if not description or not description.strip():
            print(f"[COMMENT_GEN] ❌ {char_name} has no PromoCanon description - skipping")
            return False
        
        # Rule 3: Character must be in PromoCanon (verify they exist in canon data)
        if self.canon_loader:
            try:
                canon_characters = self.canon_loader.load_characters()
                # Check if character exists in PromoCanon
                char_name_in_canon = char_name in canon_characters
                # Also check partial match
                if not char_name_in_canon:
                    first_name = char_name.split()[0] if ' ' in char_name else char_name
                    char_name_in_canon = any(
                        canon_name.split()[0] == first_name or first_name in canon_name
                        for canon_name in canon_characters.keys()
                    )
                
                if not char_name_in_canon:
                    print(f"[COMMENT_GEN] ❌ {char_name} not found in PromoCanon - skipping")
                    return False
            except Exception as e:
                print(f"[COMMENT_GEN] ⚠️ Error checking PromoCanon: {e}")
                # If we can't check, be conservative - don't comment
                return False
        
        # Skip show matching - if character is in PromoCanon and plot-relevant, they can comment
        
        # Skip if character is the post author (they don't comment on their own post initially)
        if trigger_type == "post_created" and post.author_user and post.author_user.id == character.id:
            print(f"[COMMENT_GEN] ❌ {char_name} is post author - skipping")
            return False
        
        # Rule 5: Check if character is directly mentioned in content (strong signal - skip LLM check)
        char_name_lower = char_name.lower()
        content_to_check = ""
        if trigger_type == "post_created":
            content_to_check = f"{post.title} {post.description or ''} {post.content or ''}".lower()
        elif trigger_type == "user_commented" and user_comment:
            content_to_check = f"{user_comment.content}".lower()
            # Also include post context
            content_to_check += f" {post.title} {post.description or ''} {post.content or ''}".lower()
        
        # Check if character is directly mentioned (hardcoded check - strong signal)
        if char_name_lower in content_to_check:
            import re
            first_name = char_name.split()[0].lower() if ' ' in char_name else char_name_lower
            full_name_pattern = re.compile(r'\b' + re.escape(char_name_lower) + r'\b', re.IGNORECASE)
            first_name_pattern = re.compile(r'\b' + re.escape(first_name) + r'\b', re.IGNORECASE)
            
            if full_name_pattern.search(content_to_check) or first_name_pattern.search(content_to_check):
                print(f"[COMMENT_GEN] ✅ {char_name} mentioned in content - will comment (hardcoded check)")
                return True
        
        # Rule 6: Use LLM to check plot relevance
        # Build plot context from PromoCanon
        plot_context = ""
        if self.canon_loader:
            try:
                episodes = self.canon_loader.load_episodes()
                major_cliffhangers = self.canon_loader.load_major_cliffhangers()
                minor_cliffhangers = self.canon_loader.load_minor_cliffhangers()
                all_cliffhangers = major_cliffhangers + minor_cliffhangers
                
                # Get recent episodes (last 10 for context)
                recent_episodes = episodes[-10:] if len(episodes) > 10 else episodes
                episode_context = "\n".join([
                    f"Episode {ep.get('episode', '?')}: {ep.get('summary', '')[:200]}"
                    for ep in recent_episodes
                ])
                
                # Get recent cliffhangers (last 5)
                recent_cliffhangers = all_cliffhangers[-5:] if len(all_cliffhangers) > 5 else all_cliffhangers
                cliffhanger_context = "\n".join([
                    f"Cliffhanger: {ch.get('cliffhanger_text', ch.get('text', ''))[:200]}"
                    for ch in recent_cliffhangers
                ])
                
                plot_context = f"Recent Plot Points:\n{episode_context}\n\nRecent Cliffhangers:\n{cliffhanger_context}"
            except Exception as e:
                print(f"[COMMENT_GEN] ⚠️ Error loading plot context for relevance check: {e}")
        
        # Build content for LLM check
        post_content = f"{post.title}\n{post.description or ''}\n{post.content or ''}".strip()
        user_comment_context = ""
        if trigger_type == "user_commented" and user_comment:
            user_name = user_comment.author_user.display_name if user_comment.author_user else user_comment.author_name or "someone"
            user_comment_context = f"\nA user ({user_name}) commented: {user_comment.content}"
        
        # Use LLM to determine if character should comment
        if self.llm_client and self.llm_client.gemini_client:
            try:
                relevance_prompt = f"""You are analyzing whether a character should comment on a post/comment based on plot relevance.

Character Information:
- Name: {char_name}
- Description: {description}
- Personality: {personality}

Post/Content:
{post_content}
{user_comment_context}

Story Context:
{plot_context}

Task: Determine if {char_name} should comment on this post/comment based on:
1. Is the content plot-relevant to the character's journey or the story?
2. Would {char_name} naturally respond to this based on their persona?
3. Is there a meaningful connection between the content and the character's story arc?

Respond with ONLY "YES" or "NO" (no explanation, no other text).

Response:"""
                
                print(f"[COMMENT_GEN] Calling LLM to check plot relevance for {char_name}...")
                decision = self.llm_client.generate_simple(
                    prompt=relevance_prompt,
                    temperature=0.3,  # Low temperature for consistent yes/no decisions
                    max_tokens=10,  # Just need YES/NO
                )
                
                if decision:
                    decision = decision.strip().upper()
                    print(f"[COMMENT_GEN] LLM decision for {char_name}: {decision}")
                    
                    # Check if LLM said yes
                    if decision.startswith("YES") or decision == "Y":
                        print(f"[COMMENT_GEN] ✅ {char_name} will comment - LLM determined plot relevance")
                        return True
                    else:
                        print(f"[COMMENT_GEN] ❌ {char_name} won't comment - LLM determined no plot relevance")
                        return False
                else:
                    print(f"[COMMENT_GEN] ⚠️ LLM returned empty response for {char_name}")
                    return False
                    
            except Exception as e:
                print(f"[COMMENT_GEN] ⚠️ Error using LLM for relevance check: {e}")
                import traceback
                traceback.print_exc()
                # Fallback: be conservative - don't comment if LLM fails
                print(f"[COMMENT_GEN] ❌ {char_name} won't comment - LLM check failed")
                return False
        else:
            # If LLM not available, be conservative
            print(f"[COMMENT_GEN] ⚠️ LLM not available for relevance check - skipping {char_name}")
            return False
    
    def generate_comment(self, character: User, post: Post, trigger_type: str = "post_created", 
                        user_comment: Optional[Comment] = None) -> Optional[str]:
        """
        Generate a plot-relevant comment based on character persona and context using LLM.
        Returns comment text that matches how the character behaves in the story.
        """
        persona = self.get_character_persona(character)
        char_name = persona.get('name', character.display_name)
        char_name_lower = char_name.lower()
        description = persona.get('description', '')
        personality = persona.get('personality', '')
        
        print(f"[COMMENT_GEN] Generating comment for {char_name} on post {post.id}")
        
        # Build context for the comment
        post_content = f"{post.title}\n{post.description or ''}\n{post.content or ''}".strip()
        
        # Build plot context from PromoCanon
        plot_context = ""
        if self.canon_loader:
            try:
                episodes = self.canon_loader.load_episodes()
                major_cliffhangers = self.canon_loader.load_major_cliffhangers()
                minor_cliffhangers = self.canon_loader.load_minor_cliffhangers()
                
                # Get recent episodes (last 5)
                recent_episodes = episodes[-5:] if len(episodes) > 5 else episodes
                episode_context = "\n".join([
                    f"Episode {ep.get('episode', '?')}: {ep.get('summary', '')[:200]}"
                    for ep in recent_episodes
                ])
                
                # Get recent cliffhangers (last 3)
                all_cliffhangers = major_cliffhangers + minor_cliffhangers
                recent_cliffhangers = all_cliffhangers[-3:] if len(all_cliffhangers) > 3 else all_cliffhangers
                cliffhanger_context = "\n".join([
                    f"Cliffhanger: {ch.get('cliffhanger_text', ch.get('text', ''))[:200]}"
                    for ch in recent_cliffhangers
                ])
                
                plot_context = f"Recent Plot Points:\n{episode_context}\n\nRecent Cliffhangers:\n{cliffhanger_context}"
            except Exception as e:
                print(f"[COMMENT_GEN] ⚠️ Error loading plot context: {e}")
        
        # Build user comment context if available
        user_comment_context = ""
        if trigger_type == "user_commented" and user_comment:
            user_name = user_comment.author_user.display_name if user_comment.author_user else user_comment.author_name or "someone"
            user_comment_context = f"A user ({user_name}) commented: {user_comment.content}"
        
        # Build more detailed plot context for the character
        character_specific_context = ""
        if self.canon_loader:
            try:
                # Get episodes where this character might be involved
                episodes = self.canon_loader.load_episodes()
                # Find episodes that mention the character or relate to their journey
                char_episodes = []
                for ep in episodes[-10:]:  # Check last 10 episodes
                    ep_text = f"{ep.get('summary', '')} {ep.get('title', '')}".lower()
                    if char_name_lower in ep_text or any(word in ep_text for word in description.lower().split()[:5] if len(word) > 4):
                        char_episodes.append(f"Episode {ep.get('episode', '?')}: {ep.get('summary', '')[:150]}")
                
                if char_episodes:
                    character_specific_context = f"\nCharacter's Recent Story Arc:\n" + "\n".join(char_episodes[-3:])
            except Exception as e:
                print(f"[COMMENT_GEN] ⚠️ Error loading character-specific context: {e}")
        
        # Build LLM prompt with enhanced context
        prompt = f"""You are {char_name}, a character from a story. Generate a short, plot-relevant comment based on the character's persona and the context provided.

Character Information:
- Name: {char_name}
- Description: {description}
- Personality: {personality}

Current Post/Content:
{post_content}

{user_comment_context}

Story Context:
{plot_context}
{character_specific_context}

Instructions:
- Write a comment that {char_name} would make based on their persona and the story context
- Keep it short (1-2 sentences, max 50 words)
- Make it plot-relevant and authentic to the character's journey
- Match the character's personality and speaking style from the description
- Respond naturally to the post/comment content
- Reference specific plot points or character journey elements if relevant
- Do not use quotes or markdown formatting
- Write in first person as {char_name}

Comment:"""

        # Generate comment using LLM
        if self.llm_client and self.llm_client.gemini_client:
            try:
                print(f"[COMMENT_GEN] Calling LLM to generate comment for {char_name}...")
                print(f"[COMMENT_GEN] Prompt length: {len(prompt)} characters")
                
                comment = self.llm_client.generate(
                    prompt=prompt,
                    temperature=0.7,  # Some creativity but stay in character
                    max_tokens=100,  # Limit to keep comments short
                    top_p=0.8,
                    top_k=40,
                )
                
                if comment:
                    # Clean up the comment (remove quotes, markdown, etc.)
                    comment = comment.strip('"').strip("'").strip()
                    # Remove markdown formatting if present
                    comment = comment.replace('**', '').replace('*', '').replace('_', '')
                    # Remove "Comment:" prefix if LLM added it
                    if comment.lower().startswith('comment:'):
                        comment = comment[8:].strip()
                    # Remove any leading/trailing colons or dashes
                    comment = comment.strip(':').strip('-').strip()
                    
                    # Limit length (max 200 chars, but prefer shorter)
                    if len(comment) > 200:
                        comment = comment[:200].rsplit(' ', 1)[0] + "..."
                    
                    # Ensure it's not empty
                    if not comment or len(comment.strip()) < 3:
                        print(f"[COMMENT_GEN] ⚠️ LLM returned empty/too short comment, using fallback")
                        return "I see."
                    
                    print(f"[COMMENT_GEN] ✅ Generated comment for {char_name} ({len(comment)} chars): {comment[:80]}...")
                    return comment
                else:
                    print(f"[COMMENT_GEN] ⚠️ LLM returned empty response, using fallback")
                    return "I see."
                
            except Exception as e:
                print(f"[COMMENT_GEN] ⚠️ Error generating comment with LLM: {e}")
                import traceback
                traceback.print_exc()
                # Fallback to simple comment
                return "I see."
        else:
            # Fallback if LLM not available
            print(f"[COMMENT_GEN] ⚠️ LLM not available, using fallback comment")
            return "I see."
    
    def generate_comments_for_post(self, post: Post, trigger_type: str = "post_created", 
                                   user_comment: Optional[Comment] = None) -> List[Comment]:
        """
        Generate comments from official characters for a given post.
        Characters comment based on their persona and relevance to the post.
        Returns list of created Comment objects.
        """
        print(f"[COMMENT_GEN] Generating comments for post {post.id} (trigger: {trigger_type})")
        
        official_characters = self.get_official_characters()
        if not official_characters:
            print(f"[COMMENT_GEN] No official characters found")
            return []
        
        print(f"[COMMENT_GEN] Found {len(official_characters)} official character(s)")
        created_comments = []
        
        for character in official_characters:
            # Skip if character is the post author (for post_created trigger)
            if trigger_type == "post_created" and post.author_user and post.author_user.id == character.id:
                print(f"[COMMENT_GEN] Skipping {character.display_name} - they are the post author")
                continue
            
            # Check if character should comment (simple relevance check)
            if not self.should_character_comment(character, post, trigger_type, user_comment):
                continue
            
            # Generate comment based on character persona
            comment_text = self.generate_comment(character, post, trigger_type, user_comment)
            if not comment_text:
                continue
            
            # Create the comment
            try:
                comment = Comment(
                    post_id=post.id,
                    author_id=character.id,
                    content=comment_text
                )
                db.session.add(comment)
                created_comments.append(comment)
                print(f"[COMMENT_GEN] ✅ Created comment from {character.display_name}: {comment_text[:50]}...")
            except Exception as e:
                print(f"[COMMENT_GEN] ❌ Error creating comment: {e}")
                import traceback
                traceback.print_exc()
        
        if created_comments:
            db.session.commit()
            print(f"[COMMENT_GEN] ✅ Created {len(created_comments)} automatic comment(s) for post {post.id}")
        else:
            print(f"[COMMENT_GEN] No characters chose to comment on post {post.id}")
        
        return created_comments

