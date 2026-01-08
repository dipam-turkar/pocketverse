from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from extensions import db
from models import Pocketshow, Post, Comment, User, Vote
from functools import wraps

main_bp = Blueprint('main', __name__)


def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function


def official_user_required(f):
    """Decorator to require official user login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('main.login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_official:
            flash('This page is only accessible to official users', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


@main_bp.route('/')
def index():
    """Home page - list all pocketshows"""
    pocketshows = Pocketshow.query.order_by(Pocketshow.created_at.desc()).all()
    return render_template('index.html', pocketshows=pocketshows)


@main_bp.route('/pocketshow/<int:pocketshow_id>')
def view_pocketshow(pocketshow_id):
    """View a pocketshow and its posts"""
    pocketshow = Pocketshow.query.get_or_404(pocketshow_id)
    # Order by vote score (descending) then by creation date
    posts = Post.query.filter_by(pocketshow_id=pocketshow_id).all()
    # Sort by vote score (calculated)
    posts.sort(key=lambda p: p.get_vote_score(), reverse=True)
    users = User.query.order_by(User.display_name).all()
    return render_template('pocketshow.html', pocketshow=pocketshow, posts=posts, users=users)


@main_bp.route('/post/<int:post_id>')
def view_post(post_id):
    """View a post and its comments"""
    post = Post.query.get_or_404(post_id)
    # Get top-level comments (no parent), sorted by vote score
    comments = Comment.query.filter_by(post_id=post_id, parent_id=None).all()
    # Sort by vote score (calculated) then by creation date
    comments.sort(key=lambda c: (c.get_vote_score(), c.created_at), reverse=True)
    users = User.query.order_by(User.display_name).all()
    return render_template('post.html', post=post, comments=comments, users=users)


@main_bp.route('/create_pocketshow', methods=['GET', 'POST'])
def create_pocketshow():
    """Create a new pocketshow"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name:
            flash('Pocketshow name is required', 'error')
            return render_template('create_pocketshow.html')
        
        # Check if pocketshow already exists
        if Pocketshow.query.filter_by(name=name).first():
            flash('A pocketshow with this name already exists', 'error')
            return render_template('create_pocketshow.html')
        
        pocketshow = Pocketshow(name=name, description=description)
        db.session.add(pocketshow)
        db.session.commit()
        
        flash(f'Pocketshow "{name}" created successfully!', 'success')
        return redirect(url_for('main.view_pocketshow', pocketshow_id=pocketshow.id))
    
    return render_template('create_pocketshow.html')


@main_bp.route('/post/<int:post_id>/comment', methods=['POST'])
def add_comment(post_id):
    """Add a comment to a post"""
    post = Post.query.get_or_404(post_id)
    
    content = request.form.get('content', '').strip()
    author_id = request.form.get('author_id', type=int)
    author = request.form.get('author', '').strip() or None  # Legacy support
    parent_id = request.form.get('parent_id', type=int)
    
    if not content:
        flash('Comment content is required', 'error')
        return redirect(url_for('main.view_post', post_id=post_id))
    
    # Validate author_id if provided
    if author_id:
        user = User.query.get(author_id)
        if not user:
            flash('Invalid user selected', 'error')
            return redirect(url_for('main.view_post', post_id=post_id))
    
    # Validate parent_id if provided
    if parent_id:
        parent_comment = Comment.query.get(parent_id)
        if not parent_comment or parent_comment.post_id != post_id:
            flash('Invalid parent comment', 'error')
            return redirect(url_for('main.view_post', post_id=post_id))
    
    comment = Comment(
        content=content,
        post_id=post_id,
        author_id=author_id,
        author=author,  # Legacy support
        parent_id=parent_id
    )
    
    db.session.add(comment)
    db.session.commit()
    
    flash('Comment added successfully!', 'success')
    return redirect(url_for('main.view_post', post_id=post_id))


@main_bp.route('/post/<int:post_id>/vote', methods=['POST'])
def vote_post(post_id):
    """Vote on a post (AJAX endpoint)"""
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
    
    return jsonify({
        'success': True,
        'vote_score': post.get_vote_score()
    }), 200


@main_bp.route('/comment/<int:comment_id>/vote', methods=['POST'])
def vote_comment(comment_id):
    """Vote on a comment (AJAX endpoint)"""
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
    
    return jsonify({
        'success': True,
        'vote_score': comment.get_vote_score()
    }), 200


# ==================== AUTHENTICATION ROUTES ====================

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page for users"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_official'] = user.is_official
            flash(f'Welcome back, {user.display_name}!', 'success')
            
            if user.is_official:
                return redirect(url_for('main.dashboard'))
            else:
                return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')


@main_bp.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('main.index'))


@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        display_name = request.form.get('display_name', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        is_official = request.form.get('is_official') == 'on'
        
        # Character data for official users
        show_name = request.form.get('show_name', '').strip()
        character_name = request.form.get('character_name', '').strip()
        avatar_url = request.form.get('avatar_url', '').strip()
        bio = request.form.get('bio', '').strip()
        
        # Validation
        if not username or not display_name or not password:
            flash('Username, display name, and password are required', 'error')
            return render_template('register.html')
        
        if password != password_confirm:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        # Create user
        user = User(
            username=username,
            display_name=display_name,
            is_official=is_official
        )
        user.set_password(password)
        
        # Set character data if official
        if is_official and (show_name or character_name or avatar_url or bio):
            character_data = {}
            if show_name:
                character_data['show_name'] = show_name
            if character_name:
                character_data['character_name'] = character_name
            if avatar_url:
                character_data['avatar_url'] = avatar_url
            if bio:
                character_data['bio'] = bio
            user.set_character_data(character_data)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'User "{display_name}" created successfully!', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('register.html')


# ==================== DASHBOARD ROUTES ====================

@main_bp.route('/dashboard')
@official_user_required
def dashboard():
    """Dashboard for official users to create posts and comments"""
    user = User.query.get(session['user_id'])
    pocketshows = Pocketshow.query.order_by(Pocketshow.name).all()
    recent_posts = Post.query.filter_by(author_id=user.id).order_by(Post.created_at.desc()).limit(5).all()
    recent_comments = Comment.query.filter_by(author_id=user.id).order_by(Comment.created_at.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                         user=user, 
                         pocketshows=pocketshows,
                         recent_posts=recent_posts,
                         recent_comments=recent_comments)


@main_bp.route('/dashboard/create_post', methods=['POST'])
@official_user_required
def create_post_dashboard():
    """Create a post from the dashboard"""
    user_id = session['user_id']
    pocketshow_id = request.form.get('pocketshow_id', type=int)
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    description = request.form.get('description', '').strip()
    image_url = request.form.get('image_url', '').strip() or None
    video_url = request.form.get('video_url', '').strip() or None
    
    if not pocketshow_id or not title:
        flash('Pocketshow and title are required', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        # Create post directly using the API logic instead of HTTP request
        from models import Post
        
        post = Post(
            title=title,
            content=content,
            description=description,
            pocketshow_id=pocketshow_id,
            author_id=user_id,
            image_url=image_url,
            video_url=video_url
        )
        
        db.session.add(post)
        db.session.commit()
        
        flash(f'Post "{title}" created successfully!', 'success')
        return redirect(url_for('main.view_post', post_id=post.id))
    except Exception as e:
        flash(f'Error creating post: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))


@main_bp.route('/dashboard/create_comment', methods=['POST'])
@official_user_required
def create_comment_dashboard():
    """Create a comment from the dashboard"""
    user_id = session['user_id']
    post_id = request.form.get('post_id', type=int)
    content = request.form.get('content', '').strip()
    parent_id = request.form.get('parent_id', type=int) or None
    
    if not post_id or not content:
        flash('Post ID and content are required', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        # Create comment directly using the model instead of HTTP request
        from models import Comment, Post
        
        # Validate post exists
        post = Post.query.get_or_404(post_id)
        
        # Validate parent_id if provided
        if parent_id:
            parent_comment = Comment.query.get(parent_id)
            if not parent_comment or parent_comment.post_id != post_id:
                flash('Invalid parent comment', 'error')
                return redirect(url_for('main.dashboard'))
        
        comment = Comment(
            content=content,
            post_id=post_id,
            author_id=user_id,
            parent_id=parent_id
        )
        
        db.session.add(comment)
        db.session.commit()
        
        flash('Comment created successfully!', 'success')
        return redirect(url_for('main.view_post', post_id=post_id))
    except Exception as e:
        flash(f'Error creating comment: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))

