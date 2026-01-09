#!/usr/bin/env python3
"""
Seed script to populate the database with test posts for Character Chatbot demo.

Usage:
    python seed_test_data.py
    
    # With image generation (requires GCP credentials)
    python seed_test_data.py --generate-images
    
    # Reset database first
    python seed_test_data.py --reset
"""

import os
import sys
import argparse
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models import User, Pocketshow, Post, Comment

# =============================================================================
# TEST DATA
# =============================================================================

# Official Characters
CHARACTERS = [
    {
        "username": "nora_smith",
        "display_name": "Nora Smith",
        "password": "nora123",
        "is_official": True,
        "character_data": {
            "character_name": "Nora Smith",
            "show_name": "Saving Nora",
            "bio": "Brilliant surgeon/hacker. Sleepy. Don't bother me unless it's important.",
            "personality": "Detached, deadpan, protective of family"
        },
        "watched_shows": {"saving_nora": 100}  # Character knows everything
    },
    {
        "username": "justin_hunt",
        "display_name": "Justin Hunt",
        "password": "justin123",
        "is_official": True,
        "character_data": {
            "character_name": "Justin Hunt",
            "show_name": "Saving Nora",
            "bio": "CEO of Hunt Corporation. Devoted father. Don't waste my time.",
            "personality": "Commanding, protective, formal"
        },
        "watched_shows": {"saving_nora": 100}
    }
]

# Test Users (for commenting)
TEST_USERS = [
    {
        "username": "fan_at_ep25",
        "display_name": "SaveNora_Fan",
        "password": "test123",
        "is_official": False,
        "watched_shows": {"saving_nora": 25}  # At episode 25
    },
    {
        "username": "fan_at_ep15",
        "display_name": "JustStarted",
        "password": "test123",
        "is_official": False,
        "watched_shows": {"saving_nora": 15}  # Early in story
    },
    {
        "username": "fan_at_ep50",
        "display_name": "BingeWatcher",
        "password": "test123",
        "is_official": False,
        "watched_shows": {"saving_nora": 50}  # Midway
    }
]

# Pocketshow
POCKETSHOW = {
    "name": "Saving Nora",
    "description": "The official subreddit for Saving Nora - where characters from the show interact with fans!"
}

# Test Posts (from our test scenarios)
TEST_POSTS = [
    # Post 1: Nora at EP23 (Angela exposed)
    {
        "character": "nora_smith",
        "title": "Some people learn the hard way",
        "description": "Lying about things you don't understand tends to backfire.",
        "content": "Angela claimed she contacted a surgeon. She didn't. I watched. It was satisfying.",
        "show_name": "saving_nora",
        "episode_tag": 23,
        "image_prompt": "Hospital corridor outside operating room. Angela Smith stands humiliated, her face red with embarrassment, as medical staff ignore her. Harsh fluorescent hospital lighting. Dramatic scene, professional cinematography."
    },
    
    # Post 2: Justin at EP17 (Confused about Pete)
    {
        "character": "justin_hunt",
        "title": "Children are... unpredictable",
        "description": "My son has been different lately. I can't explain it.",
        "content": "Pete answered that Tom Cruise was the first president. I had to fire both tutors. Something is very wrong.",
        "show_name": "saving_nora",
        "episode_tag": 17,
        "image_prompt": "Luxurious penthouse study. Wealthy businessman sits at mahogany desk, looking troubled. A child's drawing visible on desk. Dim desk lamp lighting, contemplative atmosphere. Cinematic, dramatic."
    },
    
    # Post 3: Nora at EP5 (Early story)
    {
        "character": "nora_smith",
        "title": "Just another day avoiding unnecessary conversations",
        "description": "Some people think they're important enough to demand attention. They're not.",
        "content": "Checked into my room. The view is nice. I could sleep for days.",
        "show_name": "saving_nora",
        "episode_tag": 5,
        "image_prompt": "Elegant luxury hotel lobby. Beautiful woman in simple expensive dress stands near elevator, calm expression. A businessman watches from across lobby. Warm evening light through windows. Cinematic."
    },
    
    # Post 4: Justin at EP38 (New York, feelings developing)
    {
        "character": "justin_hunt",
        "title": "Debts and obligations",
        "description": "I made a deal. I intend to honor it.",
        "content": "Ms. Smith saved my grandmother. In exchange, I'll help her find her son. A man keeps his word.",
        "show_name": "saving_nora",
        "episode_tag": 38,
        "image_prompt": "Grand mansion entrance hall with marble floors. Well-dressed CEO in tailored suit looks out window at estate grounds. Soft expression. Afternoon sunlight through tall windows. Elegant, cinematic."
    },
    
    # Post 5: Nora at EP28 (Mother's love)
    {
        "character": "nora_smith",
        "title": "...",
        "description": "She's growing so fast.",
        "content": "Five years I missed. I won't miss more.",
        "show_name": "saving_nora",
        "episode_tag": 28,
        "image_prompt": "Cozy hotel room. Beautiful woman sits on bed, small child curled up against her sleeping. Tender maternal expression, genuine love. Warm lamplight. Emotional, intimate scene."
    },
    
    # Post 6: Nora at EP70 (Society established)
    {
        "character": "nora_smith",
        "title": "Social obligations",
        "description": "They wanted me here. I'm here. Can I leave now?",
        "content": "Jon Myers wanted to make me his student. I declined. Some people don't understand when they're outmatched.",
        "show_name": "saving_nora",
        "episode_tag": 70,
        "image_prompt": "Glamorous New York gala ballroom. Elegant woman in black gown holds champagne glass untouched. Society members around her. Crystal chandeliers sparkle. A man watches her from across the room. Sophisticated, cinematic."
    }
]


def create_user(data: dict, existing_users: dict) -> User:
    """Create a user if not exists."""
    if data["username"] in existing_users:
        print(f"  → User '{data['username']}' already exists")
        return existing_users[data["username"]]
    
    user = User(
        username=data["username"],
        display_name=data["display_name"],
        is_official=data.get("is_official", False)
    )
    user.set_password(data["password"])
    
    if data.get("character_data"):
        user.set_character_data(data["character_data"])
    
    if data.get("watched_shows"):
        user.set_watched_shows(data["watched_shows"])
    
    db.session.add(user)
    print(f"  ✅ Created user: {data['display_name']} ({'Official' if data.get('is_official') else 'Regular'})")
    return user


def create_pocketshow(data: dict) -> Pocketshow:
    """Create pocketshow if not exists."""
    existing = Pocketshow.query.filter_by(name=data["name"]).first()
    if existing:
        print(f"  → Pocketshow '{data['name']}' already exists")
        return existing
    
    pocketshow = Pocketshow(
        name=data["name"],
        description=data["description"]
    )
    db.session.add(pocketshow)
    print(f"  ✅ Created pocketshow: {data['name']}")
    return pocketshow


def generate_image(prompt: str, filename: str) -> str:
    """Generate an image using the image generator."""
    try:
        from services.image_generator import ImageGenerator
        import base64
        
        generator = ImageGenerator()
        result = generator.generate_image(prompt)
        
        if result.get("success") and result.get("image_base64"):
            # Save image
            upload_folder = os.path.join(os.path.dirname(__file__), "static", "uploads")
            os.makedirs(upload_folder, exist_ok=True)
            
            filepath = os.path.join(upload_folder, filename)
            image_data = base64.b64decode(result["image_base64"])
            
            with open(filepath, "wb") as f:
                f.write(image_data)
            
            print(f"  ✅ Generated image: {filename}")
            return f"/uploads/{filename}"
        else:
            print(f"  ⚠️ Image generation failed: {result.get('error', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"  ⚠️ Image generation error: {e}")
        return None


def create_post(data: dict, author: User, pocketshow: Pocketshow, generate_images: bool = False) -> Post:
    """Create a post."""
    image_url = None
    
    if generate_images and data.get("image_prompt"):
        # Generate image
        filename = f"post_{author.username}_{data['episode_tag']}.png"
        image_url = generate_image(data["image_prompt"], filename)
    
    post = Post(
        title=data["title"],
        description=data.get("description", ""),
        content=data.get("content", ""),
        pocketshow_id=pocketshow.id,
        author_id=author.id,
        show_name=data.get("show_name"),
        episode_tag=data.get("episode_tag"),
        image_url=image_url
    )
    
    db.session.add(post)
    print(f"  ✅ Created post: '{data['title'][:40]}...' by {author.display_name} (EP{data.get('episode_tag', '?')})")
    return post


def seed_database(generate_images: bool = False, reset: bool = False):
    """Main seeding function."""
    app = create_app()
    
    with app.app_context():
        if reset:
            print("\n🗑️  Resetting database...")
            db.drop_all()
            db.create_all()
            print("  ✅ Database reset complete")
        
        print("\n" + "=" * 60)
        print("🌱 SEEDING DATABASE FOR CHARACTER CHATBOT DEMO")
        print("=" * 60)
        
        # Get existing users
        existing_users = {u.username: u for u in User.query.all()}
        
        # 1. Create official character users
        print("\n📋 Creating official character users...")
        character_users = {}
        for char_data in CHARACTERS:
            user = create_user(char_data, existing_users)
            character_users[char_data["username"]] = user
            existing_users[char_data["username"]] = user
        
        # 2. Create test users
        print("\n👥 Creating test users for commenting...")
        test_users = {}
        for user_data in TEST_USERS:
            user = create_user(user_data, existing_users)
            test_users[user_data["username"]] = user
            existing_users[user_data["username"]] = user
        
        db.session.commit()
        
        # 3. Create pocketshow
        print("\n📺 Creating pocketshow...")
        pocketshow = create_pocketshow(POCKETSHOW)
        db.session.commit()
        
        # 4. Create posts
        print("\n📝 Creating test posts...")
        posts = []
        for post_data in TEST_POSTS:
            author = character_users.get(post_data["character"])
            if author:
                post = create_post(post_data, author, pocketshow, generate_images)
                posts.append(post)
        
        db.session.commit()
        
        # Summary
        print("\n" + "=" * 60)
        print("✅ SEEDING COMPLETE!")
        print("=" * 60)
        
        print(f"\n📊 Database Summary:")
        print(f"  • Users: {User.query.count()} total")
        print(f"    - Official characters: {User.query.filter_by(is_official=True).count()}")
        print(f"    - Regular users: {User.query.filter_by(is_official=False).count()}")
        print(f"  • Pocketshows: {Pocketshow.query.count()}")
        print(f"  • Posts: {Post.query.count()}")
        print(f"  • Comments: {Comment.query.count()}")
        
        print(f"\n🔐 Test Credentials:")
        print(f"  Official Characters (for posting):")
        for char in CHARACTERS:
            print(f"    • {char['username']} / {char['password']}")
        print(f"\n  Regular Users (for commenting):")
        for user in TEST_USERS:
            print(f"    • {user['username']} / {user['password']} (at EP{user['watched_shows']['saving_nora']})")
        
        print(f"\n🚀 To run the app:")
        print(f"  python app.py")
        print(f"  Then open: http://localhost:5000")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed test data for Character Chatbot demo")
    parser.add_argument("--generate-images", "-g", action="store_true", 
                       help="Generate images for posts (requires GCP credentials)")
    parser.add_argument("--reset", "-r", action="store_true",
                       help="Reset database before seeding")
    
    args = parser.parse_args()
    
    seed_database(generate_images=args.generate_images, reset=args.reset)
