"""
Module for creating posts by official users (characters).
This module provides a clean interface to create posts via the API.
"""

import requests
from typing import Optional, Dict, Any


class OfficialPostCreator:
    """Class to handle post creation for official users"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        """
        Initialize the post creator.
        
        Args:
            base_url: Base URL of the Pocketverse API (default: http://localhost:5000)
        """
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/api"
    
    def create_post(
        self,
        pocketshow_id: int,
        title: str,
        author_id: int,
        content: Optional[str] = None,
        description: Optional[str] = None,
        image_url: Optional[str] = None,
        video_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a post in a pocketshow.
        
        Args:
            pocketshow_id: ID of the pocketshow where the post will be created
            title: Title of the post (required)
            author_id: ID of the official user creating the post (required)
            content: Main content of the post
            description: Additional description/metadata
            image_url: URL to an image for the post
            video_url: URL to a video for the post
            metadata: Dictionary of additional metadata (tags, show info, etc.)
        
        Returns:
            Dictionary containing the created post data
        
        Raises:
            requests.RequestException: If the API request fails
            ValueError: If required fields are missing or invalid
        """
        if not title or not title.strip():
            raise ValueError("Title is required and cannot be empty")
        
        if not author_id:
            raise ValueError("author_id is required")
        
        url = f"{self.api_base}/pocketshows/{pocketshow_id}/posts"
        
        payload = {
            "title": title.strip(),
            "author_id": author_id
        }
        
        if content:
            payload["content"] = content.strip()
        
        if description:
            payload["description"] = description.strip()
        
        if image_url:
            payload["image_url"] = image_url.strip()
        
        if video_url:
            payload["video_url"] = video_url.strip()
        
        if metadata:
            payload["metadata"] = metadata
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def create_post_from_dict(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a post from a dictionary of post data.
        Useful when you have pre-generated post data.
        
        Args:
            post_data: Dictionary containing post information. Must include:
                - pocketshow_id (int)
                - title (str)
                - author_id (int)
                Optional fields: content, description, image_url, video_url, metadata
        
        Returns:
            Dictionary containing the created post data
        
        Raises:
            requests.RequestException: If the API request fails
            ValueError: If required fields are missing
        """
        required_fields = ['pocketshow_id', 'title', 'author_id']
        missing_fields = [field for field in required_fields if field not in post_data]
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        return self.create_post(
            pocketshow_id=post_data['pocketshow_id'],
            title=post_data['title'],
            author_id=post_data['author_id'],
            content=post_data.get('content'),
            description=post_data.get('description'),
            image_url=post_data.get('image_url'),
            video_url=post_data.get('video_url'),
            metadata=post_data.get('metadata')
        )
    
    def batch_create_posts(
        self,
        posts_data: list[Dict[str, Any]],
        stop_on_error: bool = False
    ) -> list[Dict[str, Any]]:
        """
        Create multiple posts in batch.
        
        Args:
            posts_data: List of dictionaries, each containing post data
            stop_on_error: If True, stop on first error. If False, continue and collect errors.
        
        Returns:
            List of dictionaries containing created posts and any errors
        """
        results = []
        
        for i, post_data in enumerate(posts_data):
            try:
                result = self.create_post_from_dict(post_data)
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
                    'post_data': post_data
                }
                results.append(error_result)
                
                if stop_on_error:
                    break
        
        return results


def create_official_post(
    pocketshow_id: int,
    title: str,
    author_id: int,
    content: Optional[str] = None,
    description: Optional[str] = None,
    image_url: Optional[str] = None,
    video_url: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    base_url: str = "http://localhost:5000"
) -> Dict[str, Any]:
    """
    Convenience function to create a post quickly.
    
    Args:
        pocketshow_id: ID of the pocketshow
        title: Post title
        author_id: ID of the official user
        content: Post content
        description: Post description
        image_url: Image URL
        video_url: Video URL
        metadata: Additional metadata
        base_url: API base URL
    
    Returns:
        Dictionary containing the created post data
    """
    creator = OfficialPostCreator(base_url=base_url)
    return creator.create_post(
        pocketshow_id=pocketshow_id,
        title=title,
        author_id=author_id,
        content=content,
        description=description,
        image_url=image_url,
        video_url=video_url,
        metadata=metadata
    )

