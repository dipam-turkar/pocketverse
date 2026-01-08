"""
Automatic comment generation service for official characters.
Generates comments based on character personas from PromoCanon data.
"""
import os
import random
from typing import List, Dict, Optional, Any
from models import User, Post, Comment
from extensions import db


class CommentGenerator:
    """Service for generating automatic comments from official characters"""
    
    def __init__(self, canon_directory: Optional[str] = None):
        self.canon_directory = canon_directory
        self.canon_loader = None
        
        # Initialize PromoCanon loader if directory provided
        if canon_directory:
            try:
                from modules.promo_canon_parser import PromoCanonLoader
                self.canon_loader = PromoCanonLoader(canon_directory)
                print(f"[COMMENT_GEN] ✅ PromoCanon loader initialized from: {canon_directory}")
            except Exception as e:
                print(f"[COMMENT_GEN] ⚠️ Failed to initialize PromoCanon loader: {e}")
    
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
        Keep it simple - characters don't have to comment.
        """
        persona = self.get_character_persona(character)
        char_name = persona.get('name', character.display_name)
        
        print(f"[COMMENT_GEN] Checking if {char_name} should comment on post {post.id} (trigger: {trigger_type})")
        
        # Build post content for relevance checking
        post_content = f"{post.title} {post.description or ''} {post.content or ''}".lower()
        char_name_lower = char_name.lower()
        
        # Skip if character is the post author (they don't comment on their own post initially)
        if trigger_type == "post_created" and post.author_user and post.author_user.id == character.id:
            print(f"[COMMENT_GEN] ❌ {char_name} is post author - skipping")
            return False
        
        # Check if character is mentioned in post - high relevance
        if char_name_lower in post_content:
            print(f"[COMMENT_GEN] ✅ {char_name} mentioned in post - will comment")
            return True
        
        # Check if post author is another character from same show
        if post.author_user and post.author_user.is_official:
            author_char_data = post.author_user.get_character_data()
            char_show = persona.get('show_name') or (character.get_character_data().get('show_name') if character.get_character_data() else None)
            author_show = author_char_data.get('show_name')
            
            if char_show and author_show and char_show == author_show:
                # Same show - 50% chance to comment
                should_comment = random.random() < 0.5
                print(f"[COMMENT_GEN] {char_name} same show as author - {'✅ will comment' if should_comment else '❌ won\'t comment'}")
                return should_comment
        
        # Check personality traits for engagement likelihood
        description = persona.get('description', '').lower()
        personality = persona.get('personality', '').lower()
        combined = f"{personality} {description}"
        
        # Characters with certain traits are more likely to comment
        engaging_traits = ['outspoken', 'opinionated', 'protective', 'curious', 'social', 'friendly', 'bold', 'assertive']
        reserved_traits = ['quiet', 'shy', 'reserved', 'private', 'introverted', 'silent', 'withdrawn']
        
        has_engaging = any(trait in combined for trait in engaging_traits)
        has_reserved = any(trait in combined for trait in reserved_traits)
        
        if has_engaging:
            # 50% chance for engaging characters
            should_comment = random.random() < 0.5
            print(f"[COMMENT_GEN] {char_name} has engaging traits - {'✅ will comment' if should_comment else '❌ won\'t comment'}")
            return should_comment
        elif has_reserved:
            # 15% chance for reserved characters
            should_comment = random.random() < 0.15
            print(f"[COMMENT_GEN] {char_name} has reserved traits - {'✅ will comment' if should_comment else '❌ won\'t comment'}")
            return should_comment
        else:
            # 30% default chance - keep it simple, not everyone comments
            should_comment = random.random() < 0.3
            print(f"[COMMENT_GEN] {char_name} default check - {'✅ will comment' if should_comment else '❌ won\'t comment'}")
            return should_comment
    
    def generate_comment(self, character: User, post: Post, trigger_type: str = "post_created", 
                        user_comment: Optional[Comment] = None) -> Optional[str]:
        """
        Generate a comment based on character persona and context.
        Returns comment text that matches how the character behaves in the story.
        """
        persona = self.get_character_persona(character)
        char_name = persona.get('name', character.display_name)
        description = persona.get('description', '')
        personality = persona.get('personality', '')
        
        print(f"[COMMENT_GEN] Generating comment for {char_name} on post {post.id}")
        
        # Build post content for context
        post_content = f"{post.title} {post.description or ''} {post.content or ''}".lower()
        char_name_lower = char_name.lower()
        
        # Build context-aware comment based on trigger type and character persona
        comment_templates = []
        
        if trigger_type == "post_created":
            # Character reacting to a new post
            if char_name_lower in post_content:
                # Character is mentioned in post - personal reaction
                comment_templates = [
                    "This hits close to home.",
                    "I never thought I'd see this here.",
                    "Some things can't stay hidden forever.",
                    "The truth always finds a way out.",
                    "This is about me, isn't it?",
                ]
            else:
                # General reaction - character observing
                comment_templates = [
                    "Interesting.",
                    "I see.",
                    "Hmm.",
                    "This is... unexpected.",
                    "I'm watching this closely.",
                ]
        
        elif trigger_type == "user_commented":
            # Character reacting to a user's comment
            if user_comment:
                user_name = user_comment.author_user.display_name if user_comment.author_user else user_comment.author_name or "someone"
                comment_templates = [
                    f"You don't know the half of it, {user_name}.",
                    "If only it were that simple.",
                    "There's more to this than meets the eye.",
                    "You're not wrong, but you're not entirely right either.",
                    f"{user_name}, you're missing something important.",
                ]
            else:
                comment_templates = [
                    "I have thoughts, but I'll keep them to myself for now.",
                    "This conversation is getting interesting.",
                    "Some things are better left unsaid.",
                ]
        
        # Add personality-specific comments based on character description
        description_lower = description.lower()
        personality_lower = personality.lower() if personality else ''
        combined = f"{personality_lower} {description_lower}"
        
        # Protective/defensive characters
        if any(trait in combined for trait in ['protective', 'defensive', 'guardian', 'shield']):
            comment_templates.extend([
                "I need to protect what matters.",
                "This isn't safe.",
                "We need to be careful here.",
                "I won't let harm come to those I care about.",
            ])
        
        # Curious/investigative characters
        if any(trait in combined for trait in ['curious', 'investigative', 'questioning', 'seeking']):
            comment_templates.extend([
                "I need to know more.",
                "There's something I'm missing here.",
                "This raises questions.",
                "I have to dig deeper into this.",
            ])
        
        # Emotional/sensitive characters
        if any(trait in combined for trait in ['emotional', 'sensitive', 'feeling', 'heart']):
            comment_templates.extend([
                "This is hard to process.",
                "My heart can't take this.",
                "I'm not ready for this conversation.",
                "This brings up too many feelings.",
            ])
        
        # Strong/assertive characters
        if any(trait in combined for trait in ['strong', 'assertive', 'bold', 'confident', 'powerful']):
            comment_templates.extend([
                "I won't back down from this.",
                "This is exactly what I expected.",
                "I'm ready for whatever comes next.",
            ])
        
        # Mysterious/secretive characters
        if any(trait in combined for trait in ['mysterious', 'secretive', 'hidden', 'enigmatic']):
            comment_templates.extend([
                "There are things I can't reveal.",
                "Some secrets must stay buried.",
                "You wouldn't understand even if I told you.",
            ])
        
        # If no templates, use generic fallback
        if not comment_templates:
            comment_templates = [
                "I see.",
                "Interesting.",
                "Hmm.",
            ]
        
        # Select a random template that matches character voice
        comment = random.choice(comment_templates)
        
        print(f"[COMMENT_GEN] ✅ Generated comment for {char_name}: {comment[:50]}...")
        return comment
    
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

