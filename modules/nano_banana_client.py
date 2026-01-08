"""
Nano Banana API client for image generation.
Uses GCP credentials from creds.py for authentication.
"""

import json
import time
from typing import Dict, Optional, List, Tuple, Any
from pathlib import Path
import sys
import requests
import base64

# Add parent directory to path to import creds
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from creds import get_gcp_creds
except ImportError:
    raise ImportError("creds.py not found. Please ensure creds.py exists in the project root.")

HTTPS_TIMEOUT = 90  # Timeout for API calls

class NanoBananaClient:
    """Client for Nano Banana image generation API"""

    def __init__(self, project_id: Optional[str] = None, region: str = "us-central1"):
        """
        Initialize Nano Banana client with GCP credentials.
        Args:
            project_id: GCP project ID (default: from creds)
            region: GCP region (default: us-central1)
        """
        self.creds = get_gcp_creds()
        self.project_id = project_id or self.creds.get("project_id")
        self.region = region

        # Configuration for the Nano Banana (Gemini) API
        # Using Vertex AI endpoint format for Gemini models
        self.nano_banana_config = {
            "project_id": "pocketfmapp",
            "location_id": "global",
            "api_endpoint": "aiplatform.googleapis.com",
            "models": {
                "gemini-2.5-flash-image": "gemini-2.5-flash-image",
                "gemini-3-pro-image-preview": "gemini-3-pro-image-preview"
            },
            "generate_content_api": "streamGenerateContent"
        }
        self.headers = None
        self._refresh_credentials()

    def _refresh_credentials(self):
        """Refresh bearer token using service account for Nano Banana API"""
        try:
            from google.auth.transport.requests import Request as GoogleAuthRequest
            from google.oauth2 import service_account

            credentials = service_account.Credentials.from_service_account_info(
                self.creds,
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            credentials.refresh(GoogleAuthRequest())
            token = credentials.token
            self.headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        except Exception as e:
            raise RuntimeError(f"Failed to refresh Nano Banana API credentials: {e}")

    def _image_to_base64(self, image) -> str:
        """Convert a PIL Image object (or bytes blob) to a base64-encoded PNG string"""
        if hasattr(image, 'save'):  # PIL Image
            import io
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            return base64.b64encode(buf.getvalue()).decode("utf-8")
        # Accept bytes directly
        if isinstance(image, (bytes, bytearray)):
            return base64.b64encode(image).decode("utf-8")
        raise ValueError("Input image must be a PIL Image or bytes.")

    def _handle_api_error_response(self, response, attempt):
        if response.status_code >= 400:
            try:
                message = response.json()
            except Exception:
                message = response.text
            msg = f"Nano Banana API Error {response.status_code} (attempt {attempt+1}/5): {message}"
            if response.status_code >= 500:
                time.sleep(2**attempt)
            if attempt == 4:
                raise Exception(msg)

    def generate_nano_banana_image(
        self,
        prompt: str,
        aspect_ratio=None,
        input_images=None,
        model_id=None,
        resolution=None,
        num_images=1
    ) -> Tuple[str, List[str], Dict[str, Any]]:
        """
        Generate text + images from Nano Banana (Gemini) using the streamGenerateContent API.

        Args:
            prompt: Text prompt
            aspect_ratio: Aspect ratio for image
            input_images: Input images (PIL Image or list)
            model_id: Model ID to use
            resolution: Resolution for Gemini 3.0 Pro
            num_images: Number of images to generate (1 or 2)
        Returns:
            Tuple of (text_output, images_base64_list, usage_metadata_dict)
        """
        try:
            if not self.headers:
                self._refresh_credentials()

            config = self.nano_banana_config
            if model_id is None:
                model_id = "gemini-2.5-flash-image"

            # For Gemini models, some locations might need to be "us" instead of "us-central1"
            # Try "us" first as it's the default for many Gemini models
            # location = config['location_id']
            # if location == "us-central1":
            #     # Some Gemini models work better with "us" location
            #     location = "us"
            
            # api_url = (
            #     f"https://{config['api_endpoint']}/v1/projects/{config['project_id']}"
            #     f"/locations/{location}/publishers/google/models/"
            #     f"{model_id}:{config['generate_content_api']}"
            # )
            
            api_url = (
                f"https://{config['api_endpoint']}/v1/projects/{config['project_id']}"
                f"/locations/{config['location_id']}/publishers/google/models/"
                f"{model_id}:{config['generate_content_api']}"
            )
            
            # Debug: Uncomment to see the actual endpoint being called
            # print(f"Calling Gemini API endpoint: {api_url}")

            all_images = []
            all_text_output = ""
            total_usage_metadata = {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "thinking_tokens": 0
            }
            # Build request_data once (same for all API calls)
            request_data = {
                "contents": [{
                    "role": "user",
                    "parts": []
                }]
            }

            if prompt.strip():
                request_data["contents"][0]["parts"].append({"text": prompt})
            if input_images:
                images_list = input_images if isinstance(input_images, list) else [input_images]
                for input_image in images_list:
                    img_base64 = self._image_to_base64(input_image)
                    request_data["contents"][0]["parts"].append({
                        "inlineData": {
                            "mimeType": "image/png",
                            "data": img_base64
                        }
                    })
            
            # Build generationConfig - must include responseModalities for image generation
            request_data["generationConfig"] = {
                "temperature": 0.7,
                "maxOutputTokens": 2048,
                "responseModalities": ["IMAGE"]
            }
            
            # Add imageConfig if aspect_ratio or resolution is specified
            # Only add imageConfig if we have at least one valid parameter
            image_config = {}
            if aspect_ratio:
                # Validate aspect ratio format (should be like "1:1", "16:9", etc.)
                if isinstance(aspect_ratio, str) and ":" in aspect_ratio:
                    image_config["aspectRatio"] = aspect_ratio
            if resolution and model_id == "gemini-3-pro-image-preview":
                image_config["imageSize"] = resolution
            
            # Only add imageConfig to request if it has at least one valid field
            if image_config:
                request_data["generationConfig"]["imageConfig"] = image_config

            backoff_delays = [5, 10, 20, 40]
            retry_codes = [504, 499, 429]

            # Make multiple API calls if num_images > 1
            for image_idx in range(num_images):
                response = None
                for attempt in range(5):
                    try:
                        response = requests.post(
                            api_url, headers=self.headers, json=request_data, timeout=HTTPS_TIMEOUT
                        )
                        if response.status_code == 401 and attempt < 4:
                            self._refresh_credentials()
                            continue

                        if response.status_code in retry_codes and attempt < 4:
                            delay = backoff_delays[attempt]
                            print(f"Rate limit hit {response.status_code}, waiting {delay} seconds before retry {attempt + 1}/5...")
                            time.sleep(delay)
                            continue

                        self._handle_api_error_response(response, attempt)
                        response.raise_for_status()
                        break
                    except requests.exceptions.RequestException as e:
                        if attempt == 4:
                            raise Exception(f"API Request Error: {e}")
                        continue
                    except Exception as e:
                        if attempt == 4:
                            raise
                        continue
                if response is None:
                    raise Exception("No response received from API after retries")

                response_json = response.json()
                text_output = ""
                images = []
                usage_metadata = {}
                if isinstance(response_json, list) and len(response_json) > 0:
                    response_data = response_json[-1]
                elif isinstance(response_json, dict):
                    response_data = response_json
                else:
                    print(f"Unexpected response format: {type(response_json)}")
                    continue

                if "usageMetadata" in response_data:
                    usage_metadata = {
                        "input_tokens": response_data["usageMetadata"].get("promptTokenCount", 0),
                        "output_tokens": response_data["usageMetadata"].get("candidatesTokenCount", 0),
                        "total_tokens": response_data["usageMetadata"].get("totalTokenCount", 0),
                        "thinking_tokens": response_data["usageMetadata"].get("thoughtsTokenCount", 0)
                    }
                    total_usage_metadata["input_tokens"] += usage_metadata["input_tokens"]
                    total_usage_metadata["output_tokens"] += usage_metadata["output_tokens"]
                    total_usage_metadata["total_tokens"] += usage_metadata["total_tokens"]
                    total_usage_metadata["thinking_tokens"] += usage_metadata["thinking_tokens"]

                if "candidates" in response_data:
                    for candidate in response_data["candidates"]:
                        if "content" in candidate:
                            for part in candidate["content"].get("parts", []):
                                if "text" in part:
                                    text_output += part["text"]
                                elif "inlineData" in part:
                                    inline_data = part["inlineData"]
                                    if inline_data.get("mimeType", "").startswith("image/"):
                                        image_data = inline_data.get("data", "")
                                        if image_data:
                                            images.append(image_data)

                if images:
                    all_images.append(images[0])
                if text_output:
                    if all_text_output:
                        all_text_output += "\n\n"
                    all_text_output += text_output

                if len(all_images) >= num_images:
                    break

            return all_text_output, all_images, total_usage_metadata
        except Exception as e:
            print("Nano Banana error:", e)
            return f"Error during generation: {e}", [], {}

    def _calculate_aspect_ratio(self, width: int, height: int) -> Optional[str]:
        """
        Convert pixel dimensions to standard aspect ratio format.
        Returns standard ratios like "1:1", "16:9", "9:16", "4:3", "3:4", "2:3", "3:2"
        """
        if not width or not height:
            return None
        
        # Calculate the ratio
        ratio = width / height
        
        # Map to standard aspect ratios (with tolerance)
        if abs(ratio - 1.0) < 0.01:  # 1:1
            return "1:1"
        elif abs(ratio - 16/9) < 0.01:  # 16:9
            return "16:9"
        elif abs(ratio - 9/16) < 0.01:  # 9:16
            return "9:16"
        elif abs(ratio - 4/3) < 0.01:  # 4:3
            return "4:3"
        elif abs(ratio - 3/4) < 0.01:  # 3:4
            return "3:4"
        elif abs(ratio - 2/3) < 0.01:  # 2:3
            return "2:3"
        elif abs(ratio - 3/2) < 0.01:  # 3:2
            return "3:2"
        else:
            # For non-standard ratios, calculate the simplest form
            from math import gcd
            divisor = gcd(width, height)
            simplified_w = width // divisor
            simplified_h = height // divisor
            return f"{simplified_w}:{simplified_h}"
    
    # Convenience method for old interface compatibility
    def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        style: Optional[str] = None,
        output_format: str = "png",
        num_images: int = 1
    ) -> Dict:
        """
        Backward-compatible interface: generate a single image and return URL and metadata.
        """
        # Calculate aspect ratio string as required by API ("1:1", "16:9", etc.)
        aspect_ratio = None
        if width and height:
            aspect_ratio = self._calculate_aspect_ratio(width, height)
        text_output, images_base64_list, usage_metadata = self.generate_nano_banana_image(
            prompt,
            aspect_ratio=aspect_ratio,
            input_images=None,
            model_id=None,
            resolution=None,
            num_images=num_images
        )
        # Compute a fake image URL using base64 (for actual deployment, upload image to GCS or serve endpoint)
        results = []
        for idx, image_b64 in enumerate(images_base64_list):
            image_id = f"nano_banana_{int(time.time())}_{idx}"
            # Return base64 string as "image_url" just as placeholder
            results.append({
                "image_url": f"data:image/png;base64,{image_b64}",
                "image_id": image_id,
                "status": "completed",
                "metadata": {
                    "prompt": prompt,
                    "width": width,
                    "height": height,
                    "aspect_ratio": aspect_ratio,
                    "generated_at": time.time(),
                    "usage": usage_metadata,
                    "text_output": text_output
                }
            })
        return results[0] if results else {
            "status": "failed",
            "error": "No images generated"
        }

    # The async/status/upload methods are not implemented for NanoBananaClient (http API).
    def generate_image_async(self, *args, **kwargs):
        raise NotImplementedError("Async image generation is not supported by the NanoBanana HTTP API client.")

    def check_image_status(self, job_id: str) -> Dict:
        raise NotImplementedError("Async job polling is not supported by the NanoBanana HTTP API client.")

    def save_image_to_disk(self, image_base64: str, filepath: str) -> str:
        """
        Save a base64-encoded image to disk.
        
        Args:
            image_base64: The base64-encoded image string (PNG)
            filepath: Path where to save the image (directory will be created if needed)
            
        Returns:
            Full path to saved image file
        """
        try:
            import os
            from pathlib import Path
            
            # Decode base64 image
            img_bytes = base64.b64decode(image_base64)
            
            # Create directory if it doesn't exist
            file_path = Path(filepath)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write image to disk
            with open(file_path, 'wb') as f:
                f.write(img_bytes)
            
            return str(file_path.absolute())
        except Exception as e:
            raise Exception(f"Failed to save image to disk: {e}")
    
    def upload_to_gcs(self, image_base64: str, bucket_name: str, blob_name: str) -> str:
        """
        Upload a base64-encoded image to Google Cloud Storage.
        Args:
            image_base64: The base64-encoded image string (PNG)
            bucket_name: GCS bucket name
            blob_name: Name for the blob in GCS

        Returns:
            GCS URL of uploaded image
        """
        try:
            from google.cloud import storage
            img_bytes = base64.b64decode(image_base64)

            # Initialize storage client
            storage_client = storage.Client(credentials=self.creds, project=self.project_id)
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)

            blob.upload_from_string(img_bytes, content_type="image/png")
            return f"gs://{bucket_name}/{blob_name}"
        except Exception as e:
            raise Exception(f"Failed to upload to GCS: {e}")

def create_nano_banana_client(project_id: Optional[str] = None, region: str = "us-central1") -> NanoBananaClient:
    """
    Factory function to create a Nano Banana client.

    Args:
        project_id: GCP project ID (optional, uses from creds)
        region: GCP region (default: us-central1)

    Returns:
        NanoBananaClient instance
    """
    return NanoBananaClient(project_id=project_id, region=region)
