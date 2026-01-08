from flask import Blueprint, request, jsonify
from extensions import db
from models import Pocketshow, Post, Comment, User, Vote

api_bp = Blueprint('api', __name__)


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
        video_url=video_url
    )
    
    if metadata:
        post.set_metadata(metadata)
    
    db.session.add(post)
    db.session.commit()
    
    return jsonify(post.to_dict()), 201


@api_bp.route('/pocketshows/<int:pocketshow_id>/posts', methods=['GET'])
def list_posts(pocketshow_id):
    """API endpoint to list posts in a pocketshow"""
    Pocketshow.query.get_or_404(pocketshow_id)
    posts = Post.query.filter_by(pocketshow_id=pocketshow_id).order_by(Post.created_at.desc()).all()
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
    
    return jsonify(comment.to_dict()), 201


@api_bp.route('/posts/<int:post_id>/comments', methods=['GET'])
def list_comments(post_id):
    """API endpoint to list comments on a post"""
    Post.query.get_or_404(post_id)
    comments = Comment.query.filter_by(post_id=post_id, parent_id=None).order_by(Comment.created_at.desc()).all()
    return jsonify([c.to_dict() for c in comments]), 200


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

