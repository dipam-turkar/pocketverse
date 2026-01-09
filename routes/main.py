from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app, send_from_directory
from extensions import db
from models import Pocketshow, Post, Comment, User, Vote
from functools import wraps
import os
from werkzeug.utils import secure_filename
import base64
from datetime import datetime

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
    
    # Trigger automatic character reply using Character Chatbot
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
            
            print(f"[MAIN] Generating character reply: {character_id} for user at EP{user_episode}")
            
            # Generate reply
            reply_content = chatbot.generate_reply(
                character_id=character_id,
                user_episode=user_episode,
                post_episode=post_episode,
                post_content=f"{post.title}\n{post.content or ''}",
                user_comment=content,
                show_id=show_name.lower().replace(" ", "_"),
                template_version="v1"
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
                print(f"[MAIN] ✅ Created character reply from {post.author_user.display_name}")
                flash('Comment added and character replied!', 'success')
            else:
                flash('Comment added successfully!', 'success')
        else:
            print(f"[MAIN] ℹ️ Post author is not an official character, skipping auto-reply")
            flash('Comment added successfully!', 'success')
            
    except Exception as e:
        print(f"[MAIN] ⚠️ Error generating character reply: {e}")
        import traceback
        traceback.print_exc()
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
    print(f"[LOGIN] Request method: {request.method}")
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        print(f"[LOGIN] Attempting login for: {username}")
        
        if not username or not password:
            print(f"[LOGIN] ❌ Missing username or password")
            flash('Username and password are required', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user:
            print(f"[LOGIN] User found: ID {user.id}, checking password...")
            if user.check_password(password):
                print(f"[LOGIN] ✅ Password correct - logging in user {user.id}")
                session['user_id'] = user.id
                session['username'] = user.username
                session['is_official'] = user.is_official
                flash(f'Welcome back, {user.display_name}!', 'success')
                
                if user.is_official:
                    print(f"[LOGIN] Redirecting official user to dashboard")
                    return redirect(url_for('main.dashboard'))
                else:
                    print(f"[LOGIN] Redirecting regular user to index")
                    return redirect(url_for('main.index'))
            else:
                print(f"[LOGIN] ❌ Invalid password")
        else:
            print(f"[LOGIN] ❌ User not found: {username}")
        
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
    # Get image URL from hidden field (set by JavaScript after verification)
    image_url = request.form.get('image_url', '').strip() or None
    video_url = request.form.get('video_url', '').strip() or None
    
    # Clear any pending image session data
    # Also clean up any temporary image files
    temp_filename = session.get('pending_image_filename')
    if temp_filename:
        try:
            upload_folder = current_app.config['UPLOAD_FOLDER']
            temp_filepath = os.path.join(upload_folder, temp_filename)
            if os.path.exists(temp_filepath):
                print(f"[POST CREATE] Cleaning up temp file: {temp_filename}")
                os.remove(temp_filepath)
        except Exception as e:
            print(f"[POST CREATE] Warning: Could not delete temp file: {str(e)}")
    
    session.pop('pending_image', None)
    session.pop('pending_image_filename', None)
    session.pop('pending_image_url', None)
    session.pop('pending_image_type', None)
    session.pop('pending_image_prompt', None)
    
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
        
        # Trigger automatic comment generation from official characters
        try:
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            canon_directory = os.path.join(project_root, 'PromoCanon_Show_33adb096b04ecd6b23ce9341160b199f2d489311_1_100')
            
            from services.comment_generator import CommentGenerator
            comment_generator = CommentGenerator(canon_directory=canon_directory)
            comment_generator.generate_comments_for_post(post, trigger_type="post_created")
        except Exception as e:
            print(f"[MAIN] ⚠️ Error generating automatic comments: {e}")
            import traceback
            traceback.print_exc()
        
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
        
        # Trigger automatic comment generation from official characters
        try:
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            canon_directory = os.path.join(project_root, 'PromoCanon_Show_33adb096b04ecd6b23ce9341160b199f2d489311_1_100')
            
            from services.comment_generator import CommentGenerator
            comment_generator = CommentGenerator(canon_directory=canon_directory)
            comment_generator.generate_comments_for_post(post, trigger_type="user_commented", user_comment=comment)
        except Exception as e:
            print(f"[MAIN] ⚠️ Error generating automatic comments: {e}")
            import traceback
            traceback.print_exc()
        
        flash('Comment created successfully!', 'success')
        return redirect(url_for('main.view_post', post_id=post_id))
    except Exception as e:
        flash(f'Error creating comment: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))


# ==================== IMAGE HANDLING ROUTES ====================

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


@main_bp.route('/dashboard/generate_image', methods=['POST'])
@official_user_required
def generate_image():
    """Generate an image using AI based on prompt and story context"""
    print(f"[IMAGE GEN] Starting image generation...")
    
    from services.image_generator import ImageGenerator
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    print(f"[IMAGE GEN] User: {user_id} ({user.username if user else 'unknown'})")
    
    prompt = request.form.get('prompt', '').strip()
    custom_prompt = request.form.get('custom_prompt', '').strip()
    
    print(f"[IMAGE GEN] Base prompt: {prompt[:50] if prompt else 'None'}")
    print(f"[IMAGE GEN] Custom prompt: {custom_prompt[:50] if custom_prompt else 'None'}")
    
    if not prompt and not custom_prompt:
        print(f"[IMAGE GEN] ❌ No prompt provided")
        return jsonify({'success': False, 'error': 'Prompt is required'}), 400
    
    # Use custom prompt if provided, otherwise use the base prompt
    final_prompt = custom_prompt if custom_prompt else prompt
    
    # Build story context from user's character data
    story_context = {}
    if user.is_official:
        char_data = user.get_character_data()
        if char_data:
            story_context = {
                'show_name': char_data.get('show_name'),
                'character_details': {
                    'name': char_data.get('character_name'),
                    'bio': char_data.get('bio'),
                    'personality': char_data.get('personality')
                }
            }
    
    # Get additional context from form
    plot_points = request.form.get('plot_points', '').strip()
    subplots = request.form.get('subplots', '').strip()
    cliffhangers = request.form.get('cliffhangers', '').strip()
    
    if plot_points:
        story_context['plot_points'] = [p.strip() for p in plot_points.split(',') if p.strip()]
    if subplots:
        story_context['subplots'] = [s.strip() for s in subplots.split(',') if s.strip()]
    if cliffhangers:
        story_context['cliffhangers'] = [c.strip() for c in cliffhangers.split(',') if c.strip()]
    
    # Generate image
    # Get provider from config or use default (nanobanana)
    provider = current_app.config.get('DEFAULT_IMAGE_PROVIDER', 'nanobanana')
    print(f"[IMAGE GEN] Using provider: {provider}")
    
    # Hardcode PromoCanon directory
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    canon_directory = os.path.join(project_root, 'PromoCanon_Show_33adb096b04ecd6b23ce9341160b199f2d489311_1_100')
    print(f"[IMAGE GEN] Using PromoCanon directory: {canon_directory}")
    
    generator = ImageGenerator(provider=provider, canon_directory=canon_directory)
    result = generator.generate_image(final_prompt, story_context)
    
    if result['success']:
        # Save image to disk immediately to avoid storing large data in session
        image_base64 = result.get('image_base64')
        if image_base64:
            try:
                print(f"[IMAGE GEN] Saving generated image to disk...")
                # Decode base64 image
                image_data = base64.b64decode(image_base64)
                image_size = len(image_data)
                print(f"[IMAGE GEN] Decoded image size: {image_size} bytes")
                
                # Create temporary filename with user ID and timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                temp_filename = f"temp_gen_{user_id}_{timestamp}.png"
                
                upload_folder = current_app.config['UPLOAD_FOLDER']
                filepath = os.path.join(upload_folder, temp_filename)
                
                # Save to disk
                with open(filepath, 'wb') as f:
                    f.write(image_data)
                
                print(f"[IMAGE GEN] ✅ Image saved to: {temp_filename}")
                
                # Store only the filename in session (not the base64 data)
                session['pending_image_filename'] = temp_filename
                session['pending_image_type'] = 'generated'
                session['pending_image_prompt'] = final_prompt
                
                # Return image URL for preview (serve from disk)
                image_url = url_for('main.uploaded_file', filename=temp_filename)
                
                return jsonify({
                    'success': True,
                    'image_url': image_url,  # Return URL instead of base64
                    'prompt': final_prompt
                })
            except Exception as e:
                print(f"[IMAGE GEN] ❌ Error saving image to disk: {str(e)}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    'success': False,
                    'error': f'Error saving image: {str(e)}'
                }), 500
        else:
            print(f"[IMAGE GEN] ❌ No image_base64 in result")
            return jsonify({
                'success': False,
                'error': 'No image data received from generator'
            }), 400
    else:
        return jsonify({
            'success': False,
            'error': result.get('error', 'Failed to generate image')
        }), 400


@main_bp.route('/dashboard/upload_image', methods=['POST'])
@official_user_required
def upload_image():
    """Handle image file upload"""
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to avoid conflicts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        upload_folder = current_app.config['UPLOAD_FOLDER']
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        # Store in session for verification
        image_url = url_for('main.uploaded_file', filename=filename)
        session['pending_image_url'] = image_url
        session['pending_image_type'] = 'uploaded'
        
        return jsonify({
            'success': True,
            'image_url': image_url,
            'filename': filename
        })
    else:
        return jsonify({'success': False, 'error': 'Invalid file type'}), 400


@main_bp.route('/dashboard/reject_image', methods=['POST'])
@official_user_required
def reject_image():
    """Clean up rejected image file"""
    print(f"[IMAGE REJECT] Cleaning up rejected image...")
    
    temp_filename = session.get('pending_image_filename')
    if temp_filename:
        try:
            upload_folder = current_app.config['UPLOAD_FOLDER']
            temp_filepath = os.path.join(upload_folder, temp_filename)
            if os.path.exists(temp_filepath):
                print(f"[IMAGE REJECT] Deleting temp file: {temp_filename}")
                os.remove(temp_filepath)
        except Exception as e:
            print(f"[IMAGE REJECT] Warning: Could not delete temp file: {str(e)}")
    
    # Clear session
    session.pop('pending_image', None)
    session.pop('pending_image_filename', None)
    session.pop('pending_image_type', None)
    session.pop('pending_image_prompt', None)
    
    return jsonify({'success': True})


@main_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    print(f"[UPLOAD SERVE] Request for file: {filename}")
    upload_folder = current_app.config['UPLOAD_FOLDER']
    filepath = os.path.join(upload_folder, filename)
    
    print(f"[UPLOAD SERVE] Full path: {filepath}")
    print(f"[UPLOAD SERVE] File exists: {os.path.exists(filepath)}")
    
    if not os.path.exists(filepath):
        print(f"[UPLOAD SERVE] ❌ File not found: {filepath}")
        from flask import abort
        abort(404)
    
    print(f"[UPLOAD SERVE] ✅ Serving file: {filename}")
    # Use send_from_directory with proper MIME type
    return send_from_directory(
        upload_folder, 
        filename,
        mimetype='image/png' if filename.lower().endswith('.png') else 
                 'image/jpeg' if filename.lower().endswith(('.jpg', '.jpeg')) else
                 'image/gif' if filename.lower().endswith('.gif') else
                 'image/webp' if filename.lower().endswith('.webp') else None
    )


@main_bp.route('/dashboard/save_image', methods=['POST'])
@official_user_required
def save_image():
    """Save the verified image and return URL (image already saved, just rename if needed)"""
    print(f"[IMAGE SAVE] Starting image save...")
    
    image_type = session.get('pending_image_type', 'generated')
    print(f"[IMAGE SAVE] Image type: {image_type}")
    
    if image_type == 'generated':
        print(f"[IMAGE SAVE] Processing generated image...")
        temp_filename = session.get('pending_image_filename')
        if not temp_filename:
            print(f"[IMAGE SAVE] ❌ No pending_image_filename in session")
            return jsonify({'success': False, 'error': 'No image to save'}), 400
        
        try:
            upload_folder = current_app.config['UPLOAD_FOLDER']
            temp_filepath = os.path.join(upload_folder, temp_filename)
            
            # Check if temp file exists
            if not os.path.exists(temp_filepath):
                print(f"[IMAGE SAVE] ❌ Temp file not found: {temp_filename}")
                return jsonify({'success': False, 'error': 'Temporary image file not found'}), 400
            
            # Rename from temp to permanent filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            permanent_filename = f"generated_{timestamp}.png"
            permanent_filepath = os.path.join(upload_folder, permanent_filename)
            
            print(f"[IMAGE SAVE] Renaming from {temp_filename} to {permanent_filename}")
            os.rename(temp_filepath, permanent_filepath)
            
            file_size = os.path.getsize(permanent_filepath)
            print(f"[IMAGE SAVE] ✅ File saved - Size: {file_size} bytes")
            
            image_url = url_for('main.uploaded_file', filename=permanent_filename)
            
            # Clear session
            session.pop('pending_image_filename', None)
            session.pop('pending_image_type', None)
            session.pop('pending_image_prompt', None)
            
            print(f"[IMAGE SAVE] ✅ Image URL: {image_url}")
            
            return jsonify({
                'success': True,
                'image_url': image_url
            })
        except Exception as e:
            print(f"[IMAGE SAVE] ❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 400
    
    elif image_type == 'uploaded':
        print(f"[IMAGE SAVE] Processing uploaded image...")
        image_url = session.get('pending_image_url')
        if image_url:
            print(f"[IMAGE SAVE] ✅ Image URL: {image_url}")
            session.pop('pending_image_url', None)
            session.pop('pending_image_type', None)
            return jsonify({
                'success': True,
                'image_url': image_url
            })
        else:
            print(f"[IMAGE SAVE] ❌ No image_url in session")
            return jsonify({'success': False, 'error': 'No image URL found'}), 400
    
    print(f"[IMAGE SAVE] ❌ Invalid image type: {image_type}")
    return jsonify({'success': False, 'error': 'Invalid image type'}), 400

