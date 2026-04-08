"""
Configuration Management
Loads configuration from .env file in project root directory
"""

import os
from enum import Enum
from dotenv import load_dotenv

# Load .env file from project root directory
# Path: Aarambh/.env (relative to backend/app/config.py)
project_root_env = os.path.join(os.path.dirname(__file__), '../../.env')

if os.path.exists(project_root_env):
    load_dotenv(project_root_env, override=True)
else:
    # If no .env in root, try loading from environment (for production)
    load_dotenv(override=True)


class LLMProvider(Enum):
    """LLM Provider enum for configuration"""
    OPENAI = "openai"
    GROQ = "groq"
    GLM = "glm"
    OPENROUTER = "openrouter"
    GEMINI = "gemini"
    GOOGLE_AI = "google_ai"


class Config:
    """Flask configuration class"""
    
    # Flask config
    SECRET_KEY = os.environ.get('SECRET_KEY', 'aarambh-secret-key')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    @property
    def debug(self):
        """Alias for DEBUG for compatibility"""
        return self.DEBUG
    
    # JSON config - disable ASCII escaping for proper display
    JSON_AS_ASCII = False
    
    # LLM config (OpenAI format)
    LLM_API_KEY = os.environ.get('LLM_API_KEY')
    LLM_BASE_URL = os.environ.get('LLM_BASE_URL', 'https://api.openai.com/v1')
    LLM_MODEL_NAME = os.environ.get('LLM_MODEL_NAME', 'gpt-4o-mini')
    
    # Alternative LLM provider - GROQ
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    GROQ_BASE_URL = os.environ.get('GROQ_BASE_URL', 'https://api.groq.com/openai/v1')
    GROQ_MODEL_NAME = os.environ.get('GROQ_MODEL_NAME', 'llama-3.3-70b-versatile')
    
    # Alternative LLM provider - GLM (Zhipu AI)
    GLM_API_KEY = os.environ.get('GLM_API_KEY')
    GLM_BASE_URL = os.environ.get('GLM_BASE_URL', 'https://open.bigmodel.cn/api/paas/v4')
    GLM_MODEL_NAME = os.environ.get('GLM_MODEL_NAME', 'glm-4-flash')
    
    # Zep config
    ZEP_API_KEY = os.environ.get('ZEP_API_KEY')
    
    @property
    def default_llm_provider(self):
        """Get default LLM provider enum"""
        return LLMProvider.OPENROUTER

    @property
    def default_llm_model(self):
        """Get default LLM model name"""
        return self.LLM_MODEL_NAME
    
    # File upload config
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'md', 'txt', 'markdown'}
    
    # Text processing config
    DEFAULT_CHUNK_SIZE = 500  # Default chunk size
    DEFAULT_CHUNK_OVERLAP = 50  # Default overlap size
    
    # OASIS simulation config
    OASIS_DEFAULT_MAX_ROUNDS = int(os.environ.get('OASIS_DEFAULT_MAX_ROUNDS', '10'))
    OASIS_SIMULATION_DATA_DIR = os.path.join(os.path.dirname(__file__), '../uploads/simulations')
    
    # OASIS platform available actions config
    OASIS_TWITTER_ACTIONS = [
        'CREATE_POST', 'LIKE_POST', 'REPOST', 'FOLLOW', 'DO_NOTHING', 'QUOTE_POST'
    ]
    OASIS_REDDIT_ACTIONS = [
        'LIKE_POST', 'DISLIKE_POST', 'CREATE_POST', 'CREATE_COMMENT',
        'LIKE_COMMENT', 'DISLIKE_COMMENT', 'SEARCH_POSTS', 'SEARCH_USER',
        'TREND', 'REFRESH', 'DO_NOTHING', 'FOLLOW', 'MUTE'
    ]
    
    # Report Agent config
    REPORT_AGENT_MAX_TOOL_CALLS = int(os.environ.get('REPORT_AGENT_MAX_TOOL_CALLS', '5'))
    REPORT_AGENT_MAX_REFLECTION_ROUNDS = int(os.environ.get('REPORT_AGENT_MAX_REFLECTION_ROUNDS', '2'))
    REPORT_AGENT_TEMPERATURE = float(os.environ.get('REPORT_AGENT_TEMPERATURE', '0.5'))
    
    # Database config
    POSTGRES_URL = os.environ.get('POSTGRES_URL', '')
    
    # Indian Market API configuration
    INDIANAPI_KEY = os.environ.get('INDIANAPI_KEY', '')
    
    @property
    def indianapi_key(self):
        """Alias for INDIANAPI_KEY for service compatibility"""
        return self.INDIANAPI_KEY
    
    @property
    def cors_origins_list(self):
        """Get CORS origins list"""
        origins = os.environ.get('CORS_ORIGINS', '*')
        if origins == '*':
            return ['*']
        return [o.strip() for o in origins.split(',') if o.strip()]
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        errors = []
        if not cls.LLM_API_KEY:
            errors.append("LLM_API_KEY not configured")
        if not cls.ZEP_API_KEY:
            errors.append("ZEP_API_KEY not configured")
        return errors


# Create settings instance for compatibility
settings = Config()
