# Pocketverse

A Reddit-style community platform built with Flask, featuring pocketshows (subreddits), posts, and comments.

## Features

- **Pocketshows**: Create and manage communities (similar to subreddits)
- **Posts**: Create posts within pocketshows (via API) with support for:
  - Images and videos
  - Metadata (JSON field for additional data)
  - Descriptions
- **Users**: Support for both official and unofficial users
  - Official users are characters from PocketFM stories
  - Character data includes show name, character name, avatar, bio, etc.
  - Visual badges to distinguish official characters
- **Voting**: Upvote/downvote system for both posts and comments
- **Comments**: Add comments to posts with support for:
  - Nested replies
  - User attribution (official or unofficial)
  - Voting
- **Frontend**: User-friendly web interface for browsing and interacting
- **Backend API**: RESTful API for programmatic access

## Project Structure

```
pocketverse/
├── app.py              # Main application entry point
├── config.py           # Configuration settings
├── extensions.py       # Flask extensions (SQLAlchemy)
├── models.py           # Database models
├── requirements.txt    # Python dependencies
├── routes/
│   ├── __init__.py
│   ├── main.py        # Frontend routes
│   └── api.py         # Backend API routes
├── templates/         # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   ├── create_pocketshow.html
│   ├── pocketshow.html
│   ├── post.html
│   └── comment.html
└── static/
    └── css/
        └── style.css  # Stylesheet
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

### Frontend (Web Interface)

- **Home Page** (`/`): Browse all pocketshows
- **Create Pocketshow** (`/create_pocketshow`): Create a new community
- **View Pocketshow** (`/pocketshow/<id>`): View posts in a pocketshow
- **View Post** (`/post/<id>`): View a post and its comments
- **Add Comment**: Use the comment form on any post page

### Backend API

#### Create a Pocketshow
```bash
POST /api/pocketshows
Content-Type: application/json

{
  "name": "technology",
  "description": "Discussions about technology"
}
```

#### List All Pocketshows
```bash
GET /api/pocketshows
```

#### Create a Post
```bash
POST /api/pocketshows/<pocketshow_id>/posts
Content-Type: application/json

{
  "title": "My First Post",
  "content": "This is the content of my post",
  "description": "Optional description/metadata",
  "image_url": "https://example.com/image.jpg",
  "video_url": "https://example.com/video.mp4",
  "author_id": 1,
  "metadata": {
    "tags": ["technology", "ai"],
    "source": "pocketfm"
  }
}
```

#### List Posts in a Pocketshow
```bash
GET /api/pocketshows/<pocketshow_id>/posts
```

#### Get a Post
```bash
GET /api/posts/<post_id>
```

#### Create a Comment
```bash
POST /api/posts/<post_id>/comments
Content-Type: application/json

{
  "content": "This is my comment",
  "author_id": 1,  # Optional: link to user
  "author": "John Doe",  # Optional: legacy support
  "parent_id": null  # Optional: for nested comments
}
```

#### Create a User
```bash
POST /api/users
Content-Type: application/json

{
  "username": "character_name",
  "display_name": "Character Name",
  "is_official": true,
  "character_data": {
    "show_name": "My Story Show",
    "character_name": "Protagonist",
    "avatar_url": "https://example.com/avatar.jpg",
    "bio": "Character description",
    "personality": "Brave and kind"
  }
}
```

#### List Users
```bash
GET /api/users
GET /api/users?is_official=true  # Filter by official status
```

#### Vote on a Post
```bash
POST /api/posts/<post_id>/vote
Content-Type: application/json

{
  "user_id": 1,
  "is_upvote": true
}
```

#### Vote on a Comment
```bash
POST /api/comments/<comment_id>/vote
Content-Type: application/json

{
  "user_id": 1,
  "is_upvote": true
}
```

#### Get Vote Information
```bash
GET /api/posts/<post_id>/votes
GET /api/comments/<comment_id>/votes
```

#### List Comments on a Post
```bash
GET /api/posts/<post_id>/comments
```

## Database

The application uses SQLite by default (configured in `config.py`). The database file `pocketverse.db` will be created automatically on first run.

To use a different database, update the `SQLALCHEMY_DATABASE_URI` in `config.py` or set the `DATABASE_URL` environment variable.

## Character System

The platform supports official characters from PocketFM stories:

1. **Create Official Users**: Use the API to create users with `is_official: true`
2. **Character Data**: Store character information in the `character_data` JSON field:
   - `show_name`: The name of the story/show
   - `character_name`: The character's name
   - `avatar_url`: URL to character avatar
   - `bio`: Character biography
   - Any other custom metadata

3. **Visual Distinction**: Official characters are marked with a ⭐ badge in the UI
4. **Character Posts**: Official characters can create posts and interact via comments

## Extending the Project

The project is structured to be easily extensible:

- **Add new models**: Define them in `models.py`
- **Add new routes**: Create blueprints in the `routes/` directory
- **Add authentication**: Integrate Flask-Login or similar (currently uses user IDs)
- **Add file uploads**: Extend post creation to handle image/video uploads
- **Add search**: Integrate full-text search capabilities
- **Add notifications**: Notify users of replies and votes
- **Add moderation**: Add moderation tools for pocketshows

## Configuration

Key configuration options in `config.py`:

- `SECRET_KEY`: Flask secret key (change in production!)
- `SQLALCHEMY_DATABASE_URI`: Database connection string
- `SQLALCHEMY_TRACK_MODIFICATIONS`: SQLAlchemy configuration
- `DEFAULT_IMAGE_PROVIDER`: Image generation provider (default: 'nanobanana')

### Image Generation API Keys (Optional)

Set these environment variables if you want to use API keys (free tiers available):

```bash
export NANOBANANA_API_KEY="your_key_here"  # Optional - free tier available
export VEO_API_KEY="your_key_here"         # Optional - for Google Veo
export HUGGINGFACE_API_KEY="your_key_here" # Optional - for Hugging Face
export REPLICATE_API_TOKEN="your_token"    # Optional - for Replicate
export IMAGE_PROVIDER="nanobanana"         # Set default provider
```

**Note**: Nano Banana and other providers have free tiers that work without API keys, but using an API key may provide better rate limits and reliability.

## License

MIT
