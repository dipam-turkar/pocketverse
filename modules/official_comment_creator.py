"""
Module for creating comments by official users (characters).
This module provides a clean interface to create comments via the API.
"""

import requests
from typing import Optional, Dict, Any


class OfficialCommentCreator:
    """Class to handle comment creation for official users"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        """
        Initialize the comment creator.
        
        Args:
            base_url: Base URL of the Pocketverse API (default: http://localhost:5000)
        """
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/api"
    
    def create_comment(
        self,
        post_id: int,
        content: str,
        author_id: int,
        parent_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a comment on a post.
        
        Args:
            post_id: ID of the post to comment on (required)
            content: Content of the comment (required)
            author_id: ID of the official user creating the comment (required)
            parent_id: ID of parent comment if this is a reply (optional)
        
        Returns:
            Dictionary containing the created comment data
        
        Raises:
            requests.RequestException: If the API request fails
            ValueError: If required fields are missing or invalid
        """
        if not content or not content.strip():
            raise ValueError("Content is required and cannot be empty")
        
        if not author_id:
            raise ValueError("author_id is required")
        
        url = f"{self.api_base}/posts/{post_id}/comments"
        
        payload = {
            "content": content.strip(),
            "author_id": author_id
        }
        
        if parent_id:
            payload["parent_id"] = parent_id
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def create_comment_from_dict(self, comment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a comment from a dictionary of comment data.
        Useful when you have pre-generated comment data.
        
        Args:
            comment_data: Dictionary containing comment information. Must include:
                - post_id (int)
                - content (str)
                - author_id (int)
                Optional fields: parent_id
        
        Returns:
            Dictionary containing the created comment data
        
        Raises:
            requests.RequestException: If the API request fails
            ValueError: If required fields are missing
        """
        required_fields = ['post_id', 'content', 'author_id']
        missing_fields = [field for field in required_fields if field not in comment_data]
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        return self.create_comment(
            post_id=comment_data['post_id'],
            content=comment_data['content'],
            author_id=comment_data['author_id'],
            parent_id=comment_data.get('parent_id')
        )
    
    def reply_to_comment(
        self,
        post_id: int,
        parent_comment_id: int,
        content: str,
        author_id: int
    ) -> Dict[str, Any]:
        """
        Create a reply to an existing comment.
        
        Args:
            post_id: ID of the post
            parent_comment_id: ID of the comment being replied to
            content: Content of the reply
            author_id: ID of the official user creating the reply
        
        Returns:
            Dictionary containing the created reply data
        """
        return self.create_comment(
            post_id=post_id,
            content=content,
            author_id=author_id,
            parent_id=parent_comment_id
        )
    
    def batch_create_comments(
        self,
        comments_data: list[Dict[str, Any]],
        stop_on_error: bool = False
    ) -> list[Dict[str, Any]]:
        """
        Create multiple comments in batch.
        
        Args:
            comments_data: List of dictionaries, each containing comment data
            stop_on_error: If True, stop on first error. If False, continue and collect errors.
        
        Returns:
            List of dictionaries containing created comments and any errors
        """
        results = []
        
        for i, comment_data in enumerate(comments_data):
            try:
                result = self.create_comment_from_dict(comment_data)
                results.append({
                    'index': i,
                    'success': True,
                    'data': result
                })
            except Exception as e:
                error_result = {
                    'index': i,
                    'success': False,
                    'error': str(e),
                    'comment_data': comment_data
                }
                results.append(error_result)
                
                if stop_on_error:
                    break
        
        return results


def create_official_comment(
    post_id: int,
    content: str,
    author_id: int,
    parent_id: Optional[int] = None,
    base_url: str = "http://localhost:5000"
) -> Dict[str, Any]:
    """
    Convenience function to create a comment quickly.
    
    Args:
        post_id: ID of the post
        content: Comment content
        author_id: ID of the official user
        parent_id: Optional parent comment ID for replies
        base_url: API base URL
    
    Returns:
        Dictionary containing the created comment data
    """
    creator = OfficialCommentCreator(base_url=base_url)
    return creator.create_comment(
        post_id=post_id,
        content=content,
        author_id=author_id,
        parent_id=parent_id
    )

