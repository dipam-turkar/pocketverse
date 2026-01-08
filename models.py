from datetime import datetime
from extensions import db
import json
import hashlib

class User(db.Model):
    """Model for users (both official characters and unofficial users)"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)  # For authentication
    is_official = db.Column(db.Boolean, default=False, nullable=False, index=True)
    # Character data for official users (JSON field)
    character_data = db.Column(db.Text, nullable=True)  # JSON string: {show_name, character_name, avatar_url, bio, etc}
    # Watched shows tracking: JSON string: {show_id: last_episode_watched, ...}
    watched_shows = db.Column(db.Text, nullable=True)  # JSON string: {"show_name": episode_number, ...}
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    posts = db.relationship('Post', backref='author_user', lazy=True, foreign_keys='Post.author_id')
    comments = db.relationship('Comment', backref='author_user', lazy=True, foreign_keys='Comment.author_id')
    votes = db.relationship('Vote', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def get_character_data(self):
        """Parse and return character data as dict"""
        if self.character_data:
            try:
                return json.loads(self.character_data)
            except:
                return {}
        return {}
    
    def set_character_data(self, data):
        """Set character data from dict"""
        self.character_data = json.dumps(data) if data else None
    
    def get_watched_shows(self):
        """Parse and return watched shows as dict"""
        if self.watched_shows:
            try:
                return json.loads(self.watched_shows)
            except:
                return {}
        return {}
    
    def set_watched_shows(self, data):
        """Set watched shows from dict"""
        self.watched_shows = json.dumps(data) if data else None
    
    def update_watched_episode(self, show_name, episode_number):
        """Update the last watched episode for a show"""
        watched = self.get_watched_shows()
        watched[show_name] = episode_number
        self.set_watched_shows(watched)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    def check_password(self, password):
        """Check if password is correct"""
        if not self.password_hash:
            return False
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'display_name': self.display_name,
            'is_official': self.is_official,
            'character_data': self.get_character_data(),
            'created_at': self.created_at.isoformat()
        }
    
    def to_dict_safe(self):
        """Return user dict without sensitive info"""
        return {
            'id': self.id,
            'username': self.username,
            'display_name': self.display_name,
            'is_official': self.is_official,
            'character_data': self.get_character_data(),
            'watched_shows': self.get_watched_shows(),
            'created_at': self.created_at.isoformat()
        }


class Pocketshow(db.Model):
    """Model for pocketshows (subreddits)"""
    __tablename__ = 'pocketshows'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    posts = db.relationship('Post', backref='pocketshow', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Pocketshow {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'post_count': len(self.posts)
        }


class Post(db.Model):
    """Model for posts"""
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    description = db.Column(db.Text)  # Additional metadata/description
    pocketshow_id = db.Column(db.Integer, db.ForeignKey('pocketshows.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Can be None for backward compatibility
    # Media support
    image_url = db.Column(db.String(500), nullable=True)
    video_url = db.Column(db.String(500), nullable=True)
    # Metadata as JSON string (renamed from 'metadata' to avoid SQLAlchemy conflict)
    post_metadata = db.Column(db.Text, nullable=True)  # JSON string for additional metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    comments = db.relationship('Comment', backref='post', lazy=True, cascade='all, delete-orphan', order_by='Comment.created_at')
    votes = db.relationship('Vote', backref='post', lazy=True, cascade='all, delete-orphan', foreign_keys='Vote.post_id')
    
    def __repr__(self):
        return f'<Post {self.title}>'
    
    def get_metadata(self):
        """Parse and return metadata as dict"""
        if self.post_metadata:
            try:
                return json.loads(self.post_metadata)
            except:
                return {}
        return {}
    
    def set_metadata(self, data):
        """Set metadata from dict"""
        self.post_metadata = json.dumps(data) if data else None
    
    def get_vote_score(self):
        """Calculate total vote score"""
        return sum(1 if v.is_upvote else -1 for v in self.votes)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'description': self.description,
            'pocketshow_id': self.pocketshow_id,
            'author_id': self.author_id,
            'author': self.author_user.to_dict() if self.author_user else None,
            'image_url': self.image_url,
            'video_url': self.video_url,
            'metadata': self.get_metadata(),
            'created_at': self.created_at.isoformat(),
            'comment_count': len(self.comments),
            'vote_score': self.get_vote_score()
        }


class Comment(db.Model):
    """Model for comments on posts"""
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Can be None for backward compatibility
    author = db.Column(db.String(100), nullable=True)  # Legacy field, kept for backward compatibility
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # For nested comments (replies)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy=True, cascade='all, delete-orphan')
    votes = db.relationship('Vote', backref='comment', lazy=True, cascade='all, delete-orphan', foreign_keys='Vote.comment_id')
    
    def __repr__(self):
        return f'<Comment {self.id}>'
    
    def get_author_name(self):
        """Get author name from user if available, otherwise use legacy author field"""
        if self.author_user:
            return self.author_user.display_name
        return self.author or 'Anonymous'
    
    def get_vote_score(self):
        """Calculate total vote score"""
        return sum(1 if v.is_upvote else -1 for v in self.votes)
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'post_id': self.post_id,
            'author_id': self.author_id,
            'author': self.get_author_name(),
            'author_user': self.author_user.to_dict() if self.author_user else None,
            'created_at': self.created_at.isoformat(),
            'parent_id': self.parent_id,
            'reply_count': len(self.replies),
            'vote_score': self.get_vote_score()
        }


class Vote(db.Model):
    """Model for votes on posts and comments"""
    __tablename__ = 'votes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    is_upvote = db.Column(db.Boolean, nullable=False)  # True for upvote, False for downvote
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Table constraints: ensure a vote is either for a post or comment, and one vote per user per post/comment
    __table_args__ = (
        db.UniqueConstraint('user_id', 'post_id', name='unique_user_post_vote'),
        db.UniqueConstraint('user_id', 'comment_id', name='unique_user_comment_vote'),
        db.CheckConstraint('(post_id IS NOT NULL AND comment_id IS NULL) OR (post_id IS NULL AND comment_id IS NOT NULL)'),
    )
    
    def __repr__(self):
        target = f'post_{self.post_id}' if self.post_id else f'comment_{self.comment_id}'
        vote_type = 'upvote' if self.is_upvote else 'downvote'
        return f'<Vote {vote_type} on {target} by user_{self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'post_id': self.post_id,
            'comment_id': self.comment_id,
            'is_upvote': self.is_upvote,
            'created_at': self.created_at.isoformat()
        }

