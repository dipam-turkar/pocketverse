"""
LLM client for Gemini models using the new google.genai API.
Used by comment generator and other services for LLM-based operations.
"""
import os
import tempfile
import atexit
import json
import time
from typing import Optional, Any
from google import genai
from google.genai import types
from vertexai.generative_models import (
    HarmCategory,
    HarmBlockThreshold,
    SafetySetting,
)

# Import credentials from creds.py
from creds import get_gcp_creds


class GeminiModels:
    """Gemini model identifiers"""
    TWO_POINT_5_PRO = "gemini-2.5-pro"
    TWO_POINT_5_FLASH_LITE = "gemini-2.5-flash-lite"
    TWO_POINT_5_FLASH = "gemini-2.5-flash"
    THREE_POINT_ZERO_PRO = "gemini-3-pro"
    THREE_POINT_ZERO_PRO_PREVIEW = "gemini-3-pro-preview"


class GeminiLLMClient:
    """LLM client for Gemini models using google.genai API"""
    
    DEFAULT_MODEL_ID = GeminiModels.TWO_POINT_5_FLASH
    PROJECT_ID = "pocketfmapp"
    LOCATION = "global"
    
    def __init__(self, model_id: str = DEFAULT_MODEL_ID):
        self.model_id = model_id
        self.gemini_client = None
        self.temp_key_file_path = None
        self._initialized = False
    
    def initialize_client(self):
        """Initialize the Gemini client with GCP credentials"""
        if self._initialized and self.gemini_client:
            return
        
        try:
            # Get GCP credentials from creds.py
            gcp_creds = get_gcp_creds()
            
            if not gcp_creds:
                print(f"[LLM_CLIENT] ⚠️ No GCP credentials found")
                return
            
            # Clean existing credentials
            if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
                del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
            
            # Create temporary file for credentials
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as temp_key_file:
                json.dump(gcp_creds, temp_key_file, indent=2)
                self.temp_key_file_path = temp_key_file.name
            
            # Register cleanup function
            atexit.register(
                lambda: os.remove(self.temp_key_file_path) 
                if self.temp_key_file_path and os.path.exists(self.temp_key_file_path) 
                else None
            )
            
            # Set environment variable
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.temp_key_file_path
            
            # Initialize Gemini client
            self.gemini_client = genai.Client(
                vertexai=True,
                project=self.PROJECT_ID,
                location=self.LOCATION,
                http_options={
                    "api_version": "v1",  # Use REST instead of gRPC
                    "timeout": 300000,  # 5 minutes timeout in milliseconds
                },
            )
            
            self._initialized = True
            print(f"[LLM_CLIENT] ✅ Gemini client initialized successfully (model: {self.model_id})")
            
        except Exception as e:
            print(f"[LLM_CLIENT] ⚠️ Failed to initialize Gemini client: {e}")
            import traceback
            traceback.print_exc()
            self.gemini_client = None
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: float = 0.8,
        top_k: int = 40,
        model_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instruction
            temperature: Temperature for generation (0.0-1.0)
            max_tokens: Maximum output tokens
            top_p: Top-p sampling parameter
            top_k: Top-k sampling parameter
            model_id: Override default model ID
        
        Returns:
            Generated text or None if error
        """
        if not self.gemini_client:
            self.initialize_client()
        
        if not self.gemini_client:
            print(f"[LLM_CLIENT] ⚠️ Client not initialized, cannot generate")
            return None
        
        if not prompt:
            return None
        
        try:
            # Safety settings - allow all content for character comments
            safety_config = [
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_UNSPECIFIED,
                    threshold=HarmBlockThreshold.BLOCK_NONE,
                ),
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=HarmBlockThreshold.BLOCK_NONE,
                ),
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    threshold=HarmBlockThreshold.BLOCK_NONE,
                ),
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_HARASSMENT,
                    threshold=HarmBlockThreshold.BLOCK_NONE,
                ),
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    threshold=HarmBlockThreshold.BLOCK_NONE,
                ),
            ]
            
            # Generate content config
            generate_content_config = types.GenerateContentConfig(
                temperature=temperature,
                # max_output_tokens=max_tokens,
                system_instruction=system_prompt or "You are a helpful assistant.",
                safety_settings=safety_config,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                tool_config=types.ToolConfig(
                    function_calling_config=types.FunctionCallingConfig(
                        mode="NONE",
                    )
                ),
            )
            
            # Use provided model_id or default
            actual_model_id = model_id or self.model_id
            
            # Create chat
            chat = self.gemini_client.chats.create(
                model=actual_model_id,
                config=generate_content_config,
            )
            
            # Send message
            response = chat.send_message(message=prompt)
            
            # Check for safety blocks
            if not response.text:
                if response.prompt_feedback and response.prompt_feedback.block_reason == "SAFETY":
                    print(f"[LLM_CLIENT] ⚠️ Response blocked due to safety policies")
                    return None
                else:
                    print(f"[LLM_CLIENT] ⚠️ No parsable content found in response")
                    return None
            
            return response.text.strip()
            
        except Exception as e:
            print(f"[LLM_CLIENT] ⚠️ Error generating response: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_simple(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Optional[str]:
        """
        Simplified generate method with default settings.
        Useful for simple yes/no or short responses.
        """
        return self.generate(
            prompt=prompt,
            temperature=temperature,
            # max_tokens=max_tokens,
        )

