from flask import Flask
from config import Config
from extensions import db

def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Set secret key for sessions if not already set
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    
    # Initialize extensions with app
    db.init_app(app)
    
    # Register blueprints
    from routes.main import main_bp
    from routes.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Import models to register them with SQLAlchemy
    from models import Pocketshow, Post, Comment, User, Vote
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
