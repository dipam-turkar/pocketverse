""" Image generation service using Google AI models (Imagen 3 on Vertex AI). """
import os
import base64
import json
import re
from google.oauth2 import service_account  # ← Use this instead
from typing import Optional, Dict, Any
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

GCP_CREDS = {}
class ImageGenerator:
    """Service for generating images using Google Imagen 3 via Vertex AI"""
    
    def __init__(self, provider: str = "google", canon_directory: Optional[str] = None):
        self.provider = provider
        self.project_id = "pocketfmapp"
        self.location = "us-central1"
        self.canon_directory = canon_directory
        self.canon_loader = None
        
        # Initialize PromoCanon loader if directory provided
        if canon_directory:
            try:
                from modules.promo_canon_parser import PromoCanonLoader
                self.canon_loader = PromoCanonLoader(canon_directory)
                print(f"[IMG_GEN] ✅ PromoCanon loader initialized from: {canon_directory}")
            except Exception as e:
                print(f"[IMG_GEN] ⚠️ Failed to initialize PromoCanon loader: {e}")
        
        self.initialize_client()

    def initialize_client(self):
        print(f"[IMG_GEN] Initializing Vertex AI...")
        
        # Clean existing credentials
        if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
            del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
            print("[IMG_GEN] Cleaned existing GOOGLE_APPLICATION_CREDENTIALS path.")
        
        try:
            # Parse the credentials
            # gcp_creds = json.loads(gcp_creds_raw) if isinstance(gcp_creds_raw, str) else gcp_creds_raw
            gcp_creds = GCP_CREDS
            # Repair the private key
            if "private_key" in gcp_creds:
                gcp_creds["private_key"] = gcp_creds["private_key"].replace("\\n", "\n")
            
            # ✅ FIX: Use google.oauth2.service_account.Credentials instead
            scoped_credentials = service_account.Credentials.from_service_account_info(
                gcp_creds,
                scopes=['https://www.googleapis.com/auth/cloud-platform']  # Add required scope
            )
            
            # Initialize Vertex AI with proper credentials
            vertexai.init(
                project=self.project_id,
                location=self.location,
                credentials=scoped_credentials
            )
            
            print("[IMG_GEN] ✅ Vertex AI initialized with explicit GCP_CREDS.")
            
        except Exception as e:
            print(f"[IMG_GEN] ❌ Failed to initialize client: {str(e)}")
            import traceback
            traceback.print_exc()

    def generate_image(self, prompt: str, story_context: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        enhanced_prompt = self._build_enhanced_prompt(prompt, story_context)
        return self.generate_nano_banana_image(enhanced_prompt, **kwargs)

    def _load_promocanon_context(self, show_name: Optional[str] = None, character_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Load PromoCanon data into usable context for the show.
        Returns all cliffhangers, plots, subplots, and character details without cutting.
        """
        if not self.canon_loader:
            print(f"[IMG_GEN] No PromoCanon loader available")
            return {}
        
        print(f"[IMG_GEN] Loading PromoCanon context for show: {show_name}, character: {character_name}")
        context = {}
        
        try:
            # Load all characters
            characters = self.canon_loader.load_characters()
            if characters:
                context['characters'] = characters
                print(f"[IMG_GEN] Loaded {len(characters)} characters from PromoCanon")
                
                # If character name provided, get their details
                if character_name and character_name in characters:
                    context['character_data'] = characters[character_name]
                    print(f"[IMG_GEN] Found character data for: {character_name}")
            
            # Load all cliffhangers (major and minor) - no filtering or limiting
            major_cliffhangers = self.canon_loader.load_major_cliffhangers()
            minor_cliffhangers = self.canon_loader.load_minor_cliffhangers()
            all_cliffhangers = major_cliffhangers + minor_cliffhangers
            
            if all_cliffhangers:
                context['cliffhangers'] = all_cliffhangers
                print(f"[IMG_GEN] Loaded {len(all_cliffhangers)} cliffhangers (all)")
            
            # Load all episodes for plot/subplot context - no limiting
            episodes = self.canon_loader.load_episodes()
            if episodes:
                context['episodes'] = episodes
                print(f"[IMG_GEN] Loaded {len(episodes)} episodes (all)")
            
        except Exception as e:
            print(f"[IMG_GEN] ⚠️ Error loading PromoCanon context: {e}")
            import traceback
            traceback.print_exc()
        
        return context
    
    def _build_enhanced_prompt(self, prompt: str, story_context: Optional[Dict[str, Any]]) -> str:
        """
        Build an enhanced prompt using character profiles, plots, subplots, and cliffhangers.
        Integrates PromoCanon data and the sophisticated prompt building pipeline from VEO prompt generator.
        Adapted for image generation with concise, visual-focused prompts.
        """
        if not story_context:
            print(f"[IMG_GEN] No story context, using base prompt")
            return prompt
        
        print(f"[IMG_GEN] Building enhanced prompt with story context...")
        
        # Load PromoCanon context if available
        show_name = story_context.get('show_name')
        character_name = story_context.get('character_details', {}).get('name')
        promocanon_context = self._load_promocanon_context(show_name, character_name)
        
        prompt_parts = []

        print(f"[IMG_GEN] PromoCanon context: {promocanon_context}")
        
        # 1. Start with the base user prompt
        if prompt:
            prompt_parts.append(prompt)
        
        # Ensure we only add a string to prompt_parts.
        if promocanon_context:
            if isinstance(promocanon_context, dict):
                # Try to serialize to a brief string
                context_str = ', '.join(f"{k}: {v}" for k, v in promocanon_context.items())
                prompt_parts.append(context_str)
            else:
                prompt_parts.append(str(promocanon_context))
        
        enhanced = ', '.join(prompt_parts)
        
        print(f"[IMG_GEN] Enhanced Prompt (length: {len(enhanced)}): {enhanced}")
        return enhanced

    def generate_nano_banana_image(self, prompt: str, aspect_ratio=None, input_images=None, 
                                   model_id=None, resolution=None, num_images=1):
        """
        Generate images using Google's Imagen 3 on Vertex AI.
        Returns: dict with "success", "image_base64", and "extra_info"
        """
        print(f"[IMG_GEN] Sending request to Imagen 3 using model_id={model_id or 'imagen-3.0-generate-001'}...")
        
        model_to_use = model_id or "imagen-3.0-generate-001"
        images_base64 = []
        extra_info = {}
        
        try:
            model = ImageGenerationModel.from_pretrained(model_to_use)
            
            gen_kwargs = {
                "prompt": prompt,
                "number_of_images": num_images,
                "language": "en",
                "aspect_ratio": aspect_ratio or "1:1",
                "safety_filter_level": "block_none"
            }
            
            if resolution:
                gen_kwargs["resolution"] = resolution

            print(f"[IMG_GEN] Gen kwargs: {gen_kwargs}")
            
            response = model.generate_images(**gen_kwargs)
            print(f"[IMG_GEN] Raw Imagen Response received, Response: {response}")
            
            if hasattr(response, "images") and response.images:
                for img_obj in response.images:
                    img_bytes = getattr(img_obj, "_image_bytes", None)
                    if img_bytes:
                        images_base64.append(base64.b64encode(img_bytes).decode('utf-8'))
                
                if images_base64:
                    print(f"[IMG_GEN] ✅ Success! Received {len(images_base64)} image(s).")
                    extra_info = {
                        "provider": "google_imagen",
                        "prompt": prompt,
                        "aspect_ratio": aspect_ratio or "1:1",
                        "model_id": model_to_use,
                        "num_images": num_images,
                    }
                    
                    return {
                        "success": True,
                        "image_base64": images_base64[0],
                        "extra_info": extra_info
                    }
                else:
                    print("[IMG_GEN] ⚠️ Image objects returned, but no valid image bytes extracted.")
                    return {
                        "success": False,
                        "error": "No valid image bytes received",
                        "extra_info": {}
                    }
            
            print("[IMG_GEN] ⚠️ No images returned in response (possible safety filter trigger).")
            return {
                "success": False,
                "error": "No image generated",
                "extra_info": {}
            }
            
        except Exception as e:
            print(f"[IMG_GEN] ❌ API Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Error during generation: {e}",
                "extra_info": {}
            }