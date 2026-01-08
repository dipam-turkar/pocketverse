"""
Example usage of the official post and comment creator modules.
This demonstrates how to use these modules once you have generated content.
"""

from official_post_creator import OfficialPostCreator
from official_comment_creator import OfficialCommentCreator


def example_create_post():
    """Example: Create a single post"""
    creator = OfficialPostCreator(base_url="http://localhost:5000")
    
    post = creator.create_post(
        pocketshow_id=1,
        title="Hello from the story world!",
        author_id=1,  # Official user/character ID
        content="This is my first post as a character from PocketFM!",
        description="Character introduction post",
        image_url="https://example.com/character.jpg",
        metadata={
            "show_name": "The Great Adventure",
            "character_role": "protagonist",
            "episode": "Episode 1"
        }
    )
    
    print(f"Created post: {post['id']} - {post['title']}")
    return post


def example_create_comment(post_id: int):
    """Example: Create a comment on a post"""
    creator = OfficialCommentCreator(base_url="http://localhost:5000")
    
    comment = creator.create_comment(
        post_id=post_id,
        content="This is a great post! I'm excited to be here!",
        author_id=1  # Official user/character ID
    )
    
    print(f"Created comment: {comment['id']}")
    return comment


def example_batch_creation():
    """Example: Create multiple posts and comments in batch"""
    post_creator = OfficialPostCreator()
    comment_creator = OfficialCommentCreator()
    
    # Generate multiple posts (your generation logic would go here)
    posts_data = [
        {
            "pocketshow_id": 1,
            "title": "Post 1: Introduction",
            "author_id": 1,
            "content": "This is the first generated post",
            "metadata": {"batch": "1", "type": "intro"}
        },
        {
            "pocketshow_id": 1,
            "title": "Post 2: Update",
            "author_id": 1,
            "content": "This is the second generated post",
            "metadata": {"batch": "1", "type": "update"}
        }
    ]
    
    # Create posts
    post_results = post_creator.batch_create_posts(posts_data)
    
    # Create comments on the created posts
    for result in post_results:
        if result['success']:
            post_id = result['data']['id']
            
            # Generate comments for this post (your generation logic would go here)
            comments_data = [
                {
                    "post_id": post_id,
                    "content": "First comment on this post",
                    "author_id": 1
                },
                {
                    "post_id": post_id,
                    "content": "Second comment on this post",
                    "author_id": 1
                }
            ]
            
            # Create comments
            comment_results = comment_creator.batch_create_comments(comments_data)
            
            for comment_result in comment_results:
                if comment_result['success']:
                    print(f"Created comment {comment_result['data']['id']} on post {post_id}")
                else:
                    print(f"Failed to create comment: {comment_result['error']}")


def example_with_generated_content():
    """
    Example: How to use with your content generation system
    
    This shows the pattern you'll use once you have your generation logic ready.
    """
    post_creator = OfficialPostCreator()
    comment_creator = OfficialCommentCreator()
    
    # Step 1: Generate post content (your generation logic)
    # generated_post = your_post_generator.generate(character_id=1, context=...)
    
    # For now, using example data:
    generated_post = {
        "pocketshow_id": 1,
        "title": "Generated Post Title",
        "author_id": 1,
        "content": "Generated post content here...",
        "description": "Generated description",
        "metadata": {
            "generated_by": "your_system",
            "timestamp": "2024-01-01T00:00:00"
        }
    }
    
    # Step 2: Create the post
    post = post_creator.create_post_from_dict(generated_post)
    print(f"Published post: {post['id']}")
    
    # Step 3: Generate comments (your generation logic)
    # generated_comments = your_comment_generator.generate(post_id=post['id'], ...)
    
    # For now, using example data:
    generated_comments = [
        {
            "post_id": post['id'],
            "content": "Generated comment 1",
            "author_id": 1
        },
        {
            "post_id": post['id'],
            "content": "Generated comment 2",
            "author_id": 1
        }
    ]
    
    # Step 4: Create comments
    for comment_data in generated_comments:
        comment = comment_creator.create_comment_from_dict(comment_data)
        print(f"Published comment: {comment['id']}")


if __name__ == "__main__":
    # Uncomment the example you want to run:
    
    # example_create_post()
    # example_create_comment(post_id=1)
    # example_batch_creation()
    # example_with_generated_content()
    
    print("See the examples above. Uncomment the one you want to test.")

