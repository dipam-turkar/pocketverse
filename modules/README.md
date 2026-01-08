# Official User Content Creation Modules

This directory contains modules for creating posts and comments by official users (characters from PocketFM stories).

## Modules

### `official_post_creator.py`
Module for creating posts by official users.

### `official_comment_creator.py`
Module for creating comments by official users.

## Usage Examples

### Creating Posts

#### Using the Class
```python
from modules.official_post_creator import OfficialPostCreator

# Initialize the creator
creator = OfficialPostCreator(base_url="http://localhost:5000")

# Create a post
post = creator.create_post(
    pocketshow_id=1,
    title="Hello from the story world!",
    author_id=1,  # Official user ID
    content="This is my first post as a character!",
    description="Character introduction",
    image_url="https://example.com/image.jpg",
    metadata={
        "show_name": "The Great Adventure",
        "character_role": "protagonist"
    }
)

print(f"Created post with ID: {post['id']}")
```

#### Using the Convenience Function
```python
from modules.official_post_creator import create_official_post

post = create_official_post(
    pocketshow_id=1,
    title="My Post Title",
    author_id=1,
    content="Post content here"
)
```

#### Creating from Pre-generated Data
```python
from modules.official_post_creator import OfficialPostCreator

creator = OfficialPostCreator()

# If you have pre-generated post data
post_data = {
    "pocketshow_id": 1,
    "title": "Generated Post",
    "author_id": 1,
    "content": "This post was generated automatically",
    "metadata": {"source": "ai_generator"}
}

post = creator.create_post_from_dict(post_data)
```

#### Batch Creation
```python
from modules.official_post_creator import OfficialPostCreator

creator = OfficialPostCreator()

posts_data = [
    {
        "pocketshow_id": 1,
        "title": "Post 1",
        "author_id": 1,
        "content": "Content 1"
    },
    {
        "pocketshow_id": 1,
        "title": "Post 2",
        "author_id": 1,
        "content": "Content 2"
    }
]

results = creator.batch_create_posts(posts_data, stop_on_error=False)

for result in results:
    if result['success']:
        print(f"Created post: {result['data']['id']}")
    else:
        print(f"Error: {result['error']}")
```

### Creating Comments

#### Using the Class
```python
from modules.official_comment_creator import OfficialCommentCreator

# Initialize the creator
creator = OfficialCommentCreator(base_url="http://localhost:5000")

# Create a comment
comment = creator.create_comment(
    post_id=1,
    content="This is a great post!",
    author_id=1  # Official user ID
)

print(f"Created comment with ID: {comment['id']}")
```

#### Replying to a Comment
```python
from modules.official_comment_creator import OfficialCommentCreator

creator = OfficialCommentCreator()

# Reply to an existing comment
reply = creator.reply_to_comment(
    post_id=1,
    parent_comment_id=5,
    content="I agree with you!",
    author_id=1
)
```

#### Using the Convenience Function
```python
from modules.official_comment_creator import create_official_comment

comment = create_official_comment(
    post_id=1,
    content="My comment",
    author_id=1
)
```

#### Creating from Pre-generated Data
```python
from modules.official_comment_creator import OfficialCommentCreator

creator = OfficialCommentCreator()

# If you have pre-generated comment data
comment_data = {
    "post_id": 1,
    "content": "This comment was generated automatically",
    "author_id": 1
}

comment = creator.create_comment_from_dict(comment_data)
```

#### Batch Creation
```python
from modules.official_comment_creator import OfficialCommentCreator

creator = OfficialCommentCreator()

comments_data = [
    {
        "post_id": 1,
        "content": "Comment 1",
        "author_id": 1
    },
    {
        "post_id": 1,
        "content": "Comment 2",
        "author_id": 1,
        "parent_id": 1  # Reply to first comment
    }
]

results = creator.batch_create_comments(comments_data)
```

## Integration with Post/Comment Generation

These modules are designed to work with your post and comment generation mechanisms. Once you generate the content, you can use these modules to publish them:

```python
from modules.official_post_creator import OfficialPostCreator
from modules.official_comment_creator import OfficialCommentCreator

# Your generation logic here
generated_post = your_post_generator.generate()
generated_comment = your_comment_generator.generate()

# Publish using the modules
post_creator = OfficialPostCreator()
comment_creator = OfficialCommentCreator()

# Create the post
post = post_creator.create_post_from_dict(generated_post)

# Create comments on the post
for comment_data in generated_comment:
    comment_data['post_id'] = post['id']
    comment = comment_creator.create_comment_from_dict(comment_data)
```

## Error Handling

Both modules raise exceptions on errors. Handle them appropriately:

```python
from modules.official_post_creator import OfficialPostCreator
import requests

creator = OfficialPostCreator()

try:
    post = creator.create_post(
        pocketshow_id=1,
        title="My Post",
        author_id=1
    )
except ValueError as e:
    print(f"Validation error: {e}")
except requests.RequestException as e:
    print(f"API error: {e}")
```

## Requirements

These modules require the `requests` library. Make sure it's installed:

```bash
pip install requests
```

Add it to your `requirements.txt` if not already present.

