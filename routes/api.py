from flask import Blueprint, request, jsonify, session
from extensions import db
from models import Pocketshow, Post, Comment, User, Vote

api_bp = Blueprint('api', __name__)


# ==================== AUTHENTICATION ENDPOINTS ====================

@api_bp.route('/auth/register', methods=['POST'])
def register():
    """API endpoint to register a new user"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('display_name'):
        return jsonify({'error': 'Username and display_name are required'}), 400
    
    username = data['username'].strip()
    display_name = data['display_name'].strip()
    password = data.get('password', '').strip()
    is_official = data.get('is_official', False)
    character_data = data.get('character_data', {})
    watched_shows = data.get('watched_shows', {})
    
    # Support for setting initial watched episodes during registration
    # Can be passed as: { "show_name": episode_number } or via initial_episodes parameter
    initial_episodes = data.get('initial_episodes', {})
    if initial_episodes and isinstance(initial_episodes, dict):
        # Merge initial_episodes into watched_shows
        for show_name, episode in initial_episodes.items():
            if isinstance(episode, (int, str)):
                try:
                    watched_shows[show_name] = int(episode)
                except (ValueError, TypeError):
                    pass
    
    # Check if username already exists
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'A user with this username already exists'}), 400
    
    user = User(
        username=username,
        display_name=display_name,
        is_official=is_official
    )
    
    if password:
        user.set_password(password)
    
    if is_official and character_data:
        user.set_character_data(character_data)
    
    if watched_shows:
        user.set_watched_shows(watched_shows)
    
    db.session.add(user)
    db.session.commit()
    
    # Auto-login after registration
    session['user_id'] = user.id
    session['username'] = user.username
    session['is_official'] = user.is_official
    
    return jsonify({
        'success': True,
        'user': user.to_dict_safe()
    }), 201


@api_bp.route('/auth/login', methods=['POST'])
def login():
    """API endpoint to login a user"""
    data = request.get_json()
    
    if not data or not data.get('username'):
        return jsonify({'error': 'Username is required'}), 400
    
    username = data['username'].strip()
    password = data.get('password', '').strip()
    
    user = User.query.filter_by(username=username).first()
    
    if not user:
        return jsonify({'error': 'Invalid username or password'}), 401
    
    # Check password if provided
    if password and not user.check_password(password):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    # Set session
    session['user_id'] = user.id
    session['username'] = user.username
    session['is_official'] = user.is_official
    
    return jsonify({
        'success': True,
        'user': user.to_dict_safe()
    }), 200


@api_bp.route('/auth/logout', methods=['POST'])
def logout():
    """API endpoint to logout a user"""
    session.clear()
    return jsonify({'success': True}), 200


@api_bp.route('/auth/me', methods=['GET'])
def get_current_user():
    """API endpoint to get current logged-in user"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user.to_dict_safe()), 200


@api_bp.route('/auth/update_watched', methods=['POST'])
def update_watched_episode():
    """API endpoint to update watched episode for a show"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    if not data or 'show_name' not in data or 'episode' not in data:
        return jsonify({'error': 'show_name and episode are required'}), 400
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    show_name = data['show_name']
    episode = data['episode']
    
    watched_shows = user.get_watched_shows()
    watched_shows[show_name] = episode
    user.set_watched_shows(watched_shows)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'watched_shows': user.get_watched_shows()
    }), 200


# ==================== USER ENDPOINTS ====================

@api_bp.route('/users', methods=['POST'])
def create_user():
    """API endpoint to create a user (official or unofficial)"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('display_name'):
        return jsonify({'error': 'Username and display_name are required'}), 400
    
    username = data['username'].strip()
    display_name = data['display_name'].strip()
    password = data.get('password', '').strip()
    is_official = data.get('is_official', False)
    character_data = data.get('character_data', {})
    
    # Check if username already exists
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'A user with this username already exists'}), 400
    
    user = User(
        username=username,
        display_name=display_name,
        is_official=is_official
    )
    
    if password:
        user.set_password(password)
    
    if is_official and character_data:
        user.set_character_data(character_data)
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify(user.to_dict_safe()), 201


@api_bp.route('/characters/available', methods=['GET'])
def get_available_characters():
    """API endpoint to get available characters from PromoCanon that haven't been created as users yet"""
    try:
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        canon_directory = os.path.join(project_root, 'PromoCanon_Show_33adb096b04ecd6b23ce9341160b199f2d489311_1_100')
        
        from modules.promo_canon_parser import PromoCanonLoader
        canon_loader = PromoCanonLoader(canon_directory)
        characters = canon_loader.load_characters()
        
        # Get all existing official users
        existing_users = User.query.filter_by(is_official=True).all()
        existing_character_names = set()
        for user in existing_users:
            char_data = user.get_character_data()
            char_name = char_data.get('character_name') if char_data else None
            if char_name:
                existing_character_names.add(char_name)
            # Also check display_name
            existing_character_names.add(user.display_name)
        
        # Filter out characters that already exist
        available_characters = []
        for char_name, char_data in characters.items():
            if char_name not in existing_character_names:
                available_characters.append({
                    'name': char_name,
                    'description': char_data.get('description', ''),
                    'personality': char_data.get('personality', ''),
                })
        
        print(f"[API] Found {len(available_characters)} available characters from PromoCanon")
        return jsonify({
            'success': True,
            'characters': available_characters
        }), 200
        
    except Exception as e:
        print(f"[API] Error loading available characters: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/characters/create', methods=['POST'])
def create_character_from_promocanon():
    """API endpoint to create an official user from PromoCanon character data"""
    data = request.get_json()
    
    if not data or not data.get('character_name'):
        return jsonify({'error': 'character_name is required'}), 400
    
    character_name = data['character_name'].strip()
    password = data.get('password', '').strip()
    show_name = data.get('show_name', 'Default Show').strip()
    
    try:
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        canon_directory = os.path.join(project_root, 'PromoCanon_Show_33adb096b04ecd6b23ce9341160b199f2d489311_1_100')
        
        from modules.promo_canon_parser import PromoCanonLoader
        canon_loader = PromoCanonLoader(canon_directory)
        characters = canon_loader.load_characters()
        
        if character_name not in characters:
            return jsonify({'error': f'Character "{character_name}" not found in PromoCanon'}), 404
        
        # Check if character already exists
        existing_users = User.query.filter_by(is_official=True).all()
        for user in existing_users:
            char_data = user.get_character_data()
            if char_data and char_data.get('character_name') == character_name:
                return jsonify({'error': f'Character "{character_name}" already exists as a user'}), 400
            if user.display_name == character_name:
                return jsonify({'error': f'Character "{character_name}" already exists as a user'}), 400
        
        # Get character data from PromoCanon
        canon_char = characters[character_name]
        
        # Create username from character name (sanitize)
        username = character_name.lower().replace(' ', '_').replace("'", '').replace('-', '_')
        # Ensure username is unique
        base_username = username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}_{counter}"
            counter += 1
        
        # Create user with character data
        user = User(
            username=username,
            display_name=character_name,
            is_official=True
        )
        
        if password:
            user.set_password(password)
        
        # Set character data
        character_data = {
            'character_name': character_name,
            'show_name': show_name,
            'bio': canon_char.get('description', ''),
            'personality': canon_char.get('personality', ''),
            'description': canon_char.get('description', ''),
        }
        user.set_character_data(character_data)
        
        db.session.add(user)
        db.session.commit()
        
        print(f"[API] ✅ Created official user for character: {character_name}")
        return jsonify({
            'success': True,
            'user': user.to_dict_safe()
        }), 201
        
    except Exception as e:
        print(f"[API] Error creating character: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/users', methods=['GET'])
def list_users():
    """API endpoint to list all users"""
    is_official = request.args.get('is_official', type=bool)
    query = User.query
    
    if is_official is not None:
        query = query.filter_by(is_official=is_official)
    
    users = query.order_by(User.created_at.desc()).all()
    return jsonify([u.to_dict() for u in users]), 200


@api_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """API endpoint to get a user"""
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict()), 200


@api_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """API endpoint to update a user"""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if data.get('display_name'):
        user.display_name = data['display_name'].strip()
    
    if 'is_official' in data:
        user.is_official = data['is_official']
    
    if data.get('character_data') and user.is_official:
        user.set_character_data(data['character_data'])
    
    db.session.commit()
    return jsonify(user.to_dict()), 200


@api_bp.route('/pocketshows', methods=['POST'])
def create_pocketshow():
    """API endpoint to create a pocketshow"""
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'error': 'Name is required'}), 400
    
    name = data['name'].strip()
    description = data.get('description', '').strip()
    
    # Check if pocketshow already exists
    if Pocketshow.query.filter_by(name=name).first():
        return jsonify({'error': 'A pocketshow with this name already exists'}), 400
    
    pocketshow = Pocketshow(name=name, description=description)
    db.session.add(pocketshow)
    db.session.commit()
    
    return jsonify(pocketshow.to_dict()), 201


@api_bp.route('/pocketshows', methods=['GET'])
def list_pocketshows():
    """API endpoint to list all pocketshows"""
    pocketshows = Pocketshow.query.order_by(Pocketshow.created_at.desc()).all()
    return jsonify([p.to_dict() for p in pocketshows]), 200


@api_bp.route('/pocketshows/<int:pocketshow_id>/posts', methods=['POST'])
def create_post(pocketshow_id):
    """API endpoint to create a post in a pocketshow"""
    print(f"[API] POST /pocketshows/{pocketshow_id}/posts - Creating post...")
    
    pocketshow = Pocketshow.query.get_or_404(pocketshow_id)
    print(f"[API] Pocketshow: {pocketshow.name}")
    
    data = request.get_json()
    print(f"[API] Request data: {list(data.keys()) if data else 'None'}")
    
    if not data or not data.get('title'):
        print(f"[API] ❌ Missing title")
        return jsonify({'error': 'Title is required'}), 400
    
    title = data['title'].strip()
    content = data.get('content', '').strip()
    description = data.get('description', '').strip()
    image_url = data.get('image_url', '').strip() or None
    video_url = data.get('video_url', '').strip() or None
    author_id = data.get('author_id')
    if author_id is not None:
        try:
            author_id = int(author_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'author_id must be an integer'}), 400
    metadata = data.get('metadata', {})
    
    # Episode-based tagging
    show_name = data.get('show_name', '').strip() or None
    episode_tag = data.get('episode_tag')
    if episode_tag is not None:
        try:
            episode_tag = int(episode_tag)
            if episode_tag < 0:
                return jsonify({'error': 'episode_tag must be a non-negative integer'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'episode_tag must be an integer'}), 400
    
    # Validate author_id if provided
    if author_id:
        author = User.query.get(author_id)
        if not author:
            return jsonify({'error': 'Invalid author_id'}), 400
    
    post = Post(
        title=title,
        content=content,
        description=description,
        pocketshow_id=pocketshow_id,
        author_id=author_id,
        image_url=image_url,
        video_url=video_url,
        show_name=show_name,
        episode_tag=episode_tag
    )
    
    if metadata:
        post.set_metadata(metadata)
    
    db.session.add(post)
    db.session.commit()
    
    # Trigger automatic comment generation from official characters
    try:
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        canon_directory = os.path.join(project_root, 'PromoCanon_Show_33adb096b04ecd6b23ce9341160b199f2d489311_1_100')
        
        from services.comment_generator import CommentGenerator
        comment_generator = CommentGenerator(canon_directory=canon_directory)
        comment_generator.generate_comments_for_post(post, trigger_type="post_created")
    except Exception as e:
        print(f"[API] ⚠️ Error generating automatic comments: {e}")
        import traceback
        traceback.print_exc()
    
    return jsonify(post.to_dict()), 201


@api_bp.route('/posts', methods=['GET'])
def list_all_posts():
    """API endpoint to list all posts, filtered by user's watched episodes"""
    query = Post.query
    
    # Filter by episode if user is authenticated
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            watched_shows = user.get_watched_shows()
            if watched_shows:
                # Build filter: show posts where:
                # 1. No show_name/episode_tag (not tagged, show to everyone)
                # 2. show_name not in user's watched_shows (different show, show to everyone)
                # 3. show_name in watched_shows AND episode_tag <= user's watched episode
                from sqlalchemy import or_, and_  # noqa: F401
                
                conditions = [
                    Post.show_name.is_(None),  # Posts without show tags
                    Post.episode_tag.is_(None),  # Posts without episode tags
                ]
                
                # For each show the user watches, add condition
                for show_name, watched_episode in watched_shows.items():
                    try:
                        watched_episode = int(watched_episode)
                        conditions.append(
                            and_(
                                Post.show_name == show_name,
                                Post.episode_tag <= watched_episode
                            )
                        )
                    except (ValueError, TypeError):
                        # Skip invalid episode numbers
                        continue
                
                # Also show posts from shows user hasn't watched (different shows)
                if conditions:
                    query = query.filter(or_(*conditions))
    
    posts = query.order_by(Post.created_at.desc()).all()
    return jsonify([p.to_dict() for p in posts]), 200


@api_bp.route('/pocketshows/<int:pocketshow_id>/posts', methods=['GET'])
def list_posts(pocketshow_id):
    """API endpoint to list posts in a pocketshow, filtered by user's watched episodes"""
    Pocketshow.query.get_or_404(pocketshow_id)
    query = Post.query.filter_by(pocketshow_id=pocketshow_id)
    
    # Filter by episode if user is authenticated
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            watched_shows = user.get_watched_shows()
            if watched_shows:
                # Build filter: show posts where:
                # 1. No show_name/episode_tag (not tagged, show to everyone)
                # 2. show_name not in user's watched_shows (different show, show to everyone)
                # 3. show_name in watched_shows AND episode_tag <= user's watched episode
                from sqlalchemy import or_, and_  # noqa: F401
                
                conditions = [
                    Post.show_name.is_(None),  # Posts without show tags
                    Post.episode_tag.is_(None),  # Posts without episode tags
                ]
                
                # For each show the user watches, add condition
                for show_name, watched_episode in watched_shows.items():
                    try:
                        watched_episode = int(watched_episode)
                        conditions.append(
                            and_(
                                Post.show_name == show_name,
                                Post.episode_tag <= watched_episode
                            )
                        )
                    except (ValueError, TypeError):
                        # Skip invalid episode numbers
                        continue
                
                # Also show posts from shows user hasn't watched (different shows)
                if conditions:
                    query = query.filter(or_(*conditions))
    
    posts = query.order_by(Post.created_at.desc()).all()
    return jsonify([p.to_dict() for p in posts]), 200


@api_bp.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    """API endpoint to get a post"""
    post = Post.query.get_or_404(post_id)
    return jsonify(post.to_dict()), 200


@api_bp.route('/posts/<int:post_id>/comments', methods=['POST'])
def create_comment(post_id):
    """API endpoint to create a comment on a post"""
    post = Post.query.get_or_404(post_id)
    data = request.get_json()
    
    if not data or not data.get('content'):
        return jsonify({'error': 'Content is required'}), 400
    
    content = data['content'].strip()
    author_id = data.get('author_id')
    if author_id is not None:
        try:
            author_id = int(author_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'author_id must be an integer'}), 400
    author = data.get('author', '').strip() or None  # Legacy support
    parent_id = data.get('parent_id')
    if parent_id is not None:
        try:
            parent_id = int(parent_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'parent_id must be an integer'}), 400
    
    # Validate author_id if provided
    if author_id:
        user = User.query.get(author_id)
        if not user:
            return jsonify({'error': 'Invalid author_id'}), 400
    
    # Validate parent_id if provided
    if parent_id:
        parent_comment = Comment.query.get(parent_id)
        if not parent_comment or parent_comment.post_id != post_id:
            return jsonify({'error': 'Invalid parent comment'}), 400
    
    comment = Comment(
        content=content,
        post_id=post_id,
        author_id=author_id,
        author=author,  # Legacy support
        parent_id=parent_id
    )
    
    db.session.add(comment)
    db.session.commit()
    
    # Trigger automatic character reply using new Character Chatbot
    character_reply = None
    try:
        # Only generate reply if post has an official character author
        if post.author_user and post.author_user.is_official:
            from services.character_chatbot import CharacterChatbot
            
            chatbot = CharacterChatbot(context_dir="context")
            
            # Get commenter's episode progress
            commenter = User.query.get(author_id) if author_id else None
            show_name = post.show_name or "saving_nora"
            user_episode = 1
            
            if commenter:
                watched_shows = commenter.get_watched_shows()
                user_episode = watched_shows.get(show_name, 1)
            
            # Get post's episode tag
            post_episode = post.episode_tag or user_episode
            
            # Get character info
            char_data = post.author_user.get_character_data()
            character_id = None
            if char_data:
                character_id = char_data.get("character_name", "").lower().replace(" ", "_")
            if not character_id:
                character_id = post.author_user.display_name.lower().replace(" ", "_")
            
            print(f"[API] Generating character reply: {character_id} for user at EP{user_episode}")
            
            # Generate reply
            reply_content = chatbot.generate_reply(
                character_id=character_id,
                user_episode=user_episode,
                post_episode=post_episode,
                post_content=f"{post.title}\n{post.content or ''}",
                user_comment=content,
                show_id=show_name.lower().replace(" ", "_"),
                template_version="v1"  # Can be made configurable
            )
            
            if reply_content:
                # Create the character's reply comment
                character_reply = Comment(
                    content=reply_content,
                    post_id=post_id,
                    author_id=post.author_user.id,
                    parent_id=comment.id  # Reply to user's comment
                )
                db.session.add(character_reply)
                db.session.commit()
                print(f"[API] ✅ Created character reply from {post.author_user.display_name}")
        else:
            print(f"[API] ℹ️ Post author is not an official character, skipping auto-reply")
            
    except Exception as e:
        print(f"[API] ⚠️ Error generating character reply: {e}")
        import traceback
        traceback.print_exc()
    
    # Return both the user's comment and the character's reply if any
    response_data = comment.to_dict()
    if character_reply:
        response_data['character_reply'] = character_reply.to_dict()
    
    return jsonify(response_data), 201


@api_bp.route('/posts/<int:post_id>/comments', methods=['GET'])
def list_comments(post_id):
    """API endpoint to list comments on a post"""
    Post.query.get_or_404(post_id)
    comments = Comment.query.filter_by(post_id=post_id, parent_id=None).order_by(Comment.created_at.desc()).all()
    
    def comment_with_replies(comment):
        """Include nested replies in comment dict"""
        data = comment.to_dict()
        # Include nested replies (character responses)
        data['replies'] = [comment_with_replies(r) for r in comment.replies]
        return data
    
    return jsonify([comment_with_replies(c) for c in comments]), 200


# ==================== VOTING ENDPOINTS ====================

@api_bp.route('/posts/<int:post_id>/vote', methods=['POST'])
def vote_post(post_id):
    """API endpoint to vote on a post"""
    post = Post.query.get_or_404(post_id)
    data = request.get_json()
    
    if not data or 'user_id' not in data or 'is_upvote' not in data:
        return jsonify({'error': 'user_id and is_upvote are required'}), 400
    
    user_id = data['user_id']
    is_upvote = bool(data['is_upvote'])
    
    # Validate user
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Invalid user_id'}), 400
    
    # Check if vote already exists
    existing_vote = Vote.query.filter_by(user_id=user_id, post_id=post_id).first()
    
    if existing_vote:
        # Update existing vote
        if existing_vote.is_upvote == is_upvote:
            # Same vote type, remove the vote
            db.session.delete(existing_vote)
        else:
            # Different vote type, update it
            existing_vote.is_upvote = is_upvote
    else:
        # Create new vote
        vote = Vote(user_id=user_id, post_id=post_id, is_upvote=is_upvote)
        db.session.add(vote)
    
    db.session.commit()
    
    # Return updated post with vote score
    return jsonify(post.to_dict()), 200


@api_bp.route('/comments/<int:comment_id>/vote', methods=['POST'])
def vote_comment(comment_id):
    """API endpoint to vote on a comment"""
    comment = Comment.query.get_or_404(comment_id)
    data = request.get_json()
    
    if not data or 'user_id' not in data or 'is_upvote' not in data:
        return jsonify({'error': 'user_id and is_upvote are required'}), 400
    
    user_id = data['user_id']
    is_upvote = bool(data['is_upvote'])
    
    # Validate user
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Invalid user_id'}), 400
    
    # Check if vote already exists
    existing_vote = Vote.query.filter_by(user_id=user_id, comment_id=comment_id).first()
    
    if existing_vote:
        # Update existing vote
        if existing_vote.is_upvote == is_upvote:
            # Same vote type, remove the vote
            db.session.delete(existing_vote)
        else:
            # Different vote type, update it
            existing_vote.is_upvote = is_upvote
    else:
        # Create new vote
        vote = Vote(user_id=user_id, comment_id=comment_id, is_upvote=is_upvote)
        db.session.add(vote)
    
    db.session.commit()
    
    # Return updated comment with vote score
    return jsonify(comment.to_dict()), 200


@api_bp.route('/posts/<int:post_id>/votes', methods=['GET'])
def get_post_votes(post_id):
    """API endpoint to get votes for a post"""
    post = Post.query.get_or_404(post_id)
    votes = Vote.query.filter_by(post_id=post_id).all()
    return jsonify({
        'post_id': post_id,
        'vote_score': post.get_vote_score(),
        'votes': [v.to_dict() for v in votes]
    }), 200


@api_bp.route('/comments/<int:comment_id>/votes', methods=['GET'])
def get_comment_votes(comment_id):
    """API endpoint to get votes for a comment"""
    comment = Comment.query.get_or_404(comment_id)
    votes = Vote.query.filter_by(comment_id=comment_id).all()
    return jsonify({
        'comment_id': comment_id,
        'vote_score': comment.get_vote_score(),
        'votes': [v.to_dict() for v in votes]
    }), 200


# ==================== CHARACTER CHATBOT TEST ENDPOINTS ====================

@api_bp.route('/chatbot/test', methods=['POST'])
def test_character_chatbot():
    """
    API endpoint to test the character chatbot.
    
    Request body:
    {
        "character_id": "nora_smith",
        "user_episode": 25,
        "post_episode": 23,
        "post_content": "Angela got what she deserved",
        "user_comment": "Do you think Justin knows you're Athena?",
        "template_version": "v1"  // optional: "v1", "v2", or "v3"
    }
    
    Returns:
    {
        "success": true,
        "character_id": "nora_smith",
        "user_episode": 25,
        "template_version": "v1",
        "prompt_length": 5000,
        "response": "Why would he? I'm just someone who wants to sleep...",
        "debug": {...}
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body is required'}), 400
    
    # Required fields
    character_id = data.get('character_id')
    user_episode = data.get('user_episode')
    user_comment = data.get('user_comment')
    
    if not character_id:
        return jsonify({'error': 'character_id is required'}), 400
    if not user_episode:
        return jsonify({'error': 'user_episode is required'}), 400
    if not user_comment:
        return jsonify({'error': 'user_comment is required'}), 400
    
    # Optional fields with defaults
    post_episode = data.get('post_episode', user_episode)
    post_content = data.get('post_content', '')
    template_version = data.get('template_version', 'v1')
    show_id = data.get('show_id', 'saving_nora')
    include_prompt = data.get('include_prompt', False)
    
    try:
        from services.character_chatbot import CharacterChatbot
        
        chatbot = CharacterChatbot(context_dir="context")
        
        # Generate with debug info
        result = chatbot.test_generation(
            character_id=character_id,
            user_episode=int(user_episode),
            post_episode=int(post_episode),
            post_content=post_content,
            user_comment=user_comment,
            template_version=template_version
        )
        
        response_data = {
            'success': True,
            'character_id': character_id,
            'user_episode': user_episode,
            'post_episode': post_episode,
            'template_version': template_version,
            'prompt_length': result.get('prompt_length', 0),
            'response': result.get('response'),
            'current_beat': result.get('current_beat', {}),
            'emotional_state': result.get('character_emotional_state', '')
        }
        
        # Include full prompt if requested
        if include_prompt:
            response_data['full_prompt'] = result.get('full_prompt', '')
        
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"[API] Error testing chatbot: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/chatbot/context', methods=['POST'])
def get_chatbot_context():
    """
    API endpoint to get story context without generating a reply.
    Useful for debugging and understanding what context the chatbot uses.
    
    Request body:
    {
        "character_id": "nora_smith",
        "user_episode": 25,
        "post_episode": 23,
        "show_id": "saving_nora"  // optional
    }
    
    Returns the complete context that would be used for generation.
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body is required'}), 400
    
    character_id = data.get('character_id')
    user_episode = data.get('user_episode')
    
    if not character_id:
        return jsonify({'error': 'character_id is required'}), 400
    if not user_episode:
        return jsonify({'error': 'user_episode is required'}), 400
    
    post_episode = data.get('post_episode', user_episode)
    show_id = data.get('show_id', 'saving_nora')
    
    try:
        from services.story_context import StoryContextService
        
        service = StoryContextService(context_dir="context")
        context = service.build_complete_context(
            character_id=character_id,
            user_episode=int(user_episode),
            post_episode=int(post_episode),
            show_id=show_id
        )
        
        # Return a summarized version (full context can be very large)
        return jsonify({
            'success': True,
            'character_id': character_id,
            'user_episode': user_episode,
            'post_episode': post_episode,
            'show_id': show_id,
            'current_beat': context.get('current_beat', {}),
            'character_knowledge': context.get('character_knowledge', {}),
            'previous_plots_count': len(context.get('previous_plots', [])),
            'spoiler_rules': context.get('spoiler_rules', {}),
            
            # Formatted versions for prompt
            'persona_formatted': context.get('persona_formatted', ''),
            'voice_rules': context.get('voice_rules', {}),
            'previous_plots_formatted': context.get('previous_plots_formatted', ''),
            'episode_progression_formatted': context.get('episode_progression_formatted', ''),
            'spoiler_rules_formatted': context.get('spoiler_rules_formatted', ''),
            'character_knowledge_formatted': context.get('character_knowledge_formatted', '')
        }), 200
        
    except Exception as e:
        print(f"[API] Error getting context: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/chatbot/templates', methods=['GET'])
def list_prompt_templates():
    """
    API endpoint to list available prompt templates.
    
    Returns:
    {
        "templates": ["v1", "v2", "v3"],
        "descriptions": {
            "v1": "Full context - detailed prompt with all sections",
            "v2": "Concise - shorter prompt with essential context",
            "v3": "Minimal - very short prompt for testing"
        }
    }
    """
    return jsonify({
        'templates': ['v1', 'v2', 'v3'],
        'descriptions': {
            'v1': 'Full context - detailed prompt with all sections (persona, previous plots, episode progression, spoiler rules, character knowledge)',
            'v2': 'Concise - shorter prompt with essential context only',
            'v3': 'Minimal - very short prompt for quick testing'
        },
        'default': 'v1'
    }), 200

