# Services package

# Import story context (no external dependencies)
from services.story_context import StoryContextService, get_story_context

# Try to import LLM-dependent modules (may fail if dependencies not installed)
try:
    from services.llm_client import GeminiLLMClient, GeminiModels
    from services.character_chatbot import CharacterChatbot, generate_character_reply
    __all__ = [
        'GeminiLLMClient',
        'GeminiModels',
        'StoryContextService',
        'get_story_context',
        'CharacterChatbot',
        'generate_character_reply'
    ]
except ImportError as e:
    print(f"[SERVICES] ⚠️ LLM modules not available: {e}")
    __all__ = [
        'StoryContextService',
        'get_story_context'
    ]
