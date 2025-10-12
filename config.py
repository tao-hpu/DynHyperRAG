"""
Configuration loader for HyperGraphRAG
Supports loading from .env file or environment variables
"""
import os
from pathlib import Path
from typing import Optional


class Config:
    """Configuration class for HyperGraphRAG"""

    def __init__(self):
        # Try to load from .env file if it exists
        self._load_env_file()

        # Load configuration
        self.openai_api_key = self._get_env("OPENAI_API_KEY")
        self.openai_base_url = self._get_env("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.embedding_model = self._get_env("EMBEDDING_MODEL", "text-embedding-3-small")
        self.llm_model = self._get_env("LLM_MODEL", "gpt-4o-mini")
        self.log_level = self._get_env("LOG_LEVEL", "INFO")

    def _load_env_file(self):
        """Load environment variables from .env file"""
        env_file = Path(__file__).parent / ".env"

        if not env_file.exists():
            print(f"⚠️  No .env file found at {env_file}")
            print(f"   Please copy .env.example to .env and configure it")
            return

        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue

                    # Parse KEY=VALUE
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()

                        # Only set if not already in environment
                        if key and not os.getenv(key):
                            os.environ[key] = value

            print(f"✅ Loaded configuration from {env_file}")
        except Exception as e:
            print(f"❌ Error loading .env file: {e}")

    def _get_env(self, key: str, default: Optional[str] = None) -> str:
        """Get environment variable with optional default"""
        value = os.getenv(key, default)
        if value is None:
            raise ValueError(f"Required environment variable {key} is not set")
        return value

    def validate(self):
        """Validate that all required configuration is present"""
        if not self.openai_api_key or self.openai_api_key == "your_api_key_here":
            raise ValueError(
                "OPENAI_API_KEY is not configured properly.\n"
                "Please set it in .env file or environment variable."
            )

        print("✅ Configuration validated successfully")
        print(f"   API Base URL: {self.openai_base_url}")
        print(f"   Embedding Model: {self.embedding_model}")
        print(f"   LLM Model: {self.llm_model}")
        return True

    def get_llm_kwargs(self):
        """Get kwargs for LLM initialization"""
        return {
            "base_url": self.openai_base_url,
            "api_key": self.openai_api_key,
        }

    def get_embedding_kwargs(self):
        """Get kwargs for embedding initialization"""
        return {
            "base_url": self.openai_base_url,
            "api_key": self.openai_api_key,
            "model": self.embedding_model,
        }


# Global config instance
_config = None


def get_config() -> Config:
    """Get or create global config instance"""
    global _config
    if _config is None:
        _config = Config()
    return _config


def setup_environment():
    """Setup environment with configuration"""
    config = get_config()
    config.validate()

    # Set environment variables for OpenAI SDK
    os.environ["OPENAI_API_KEY"] = config.openai_api_key

    return config


if __name__ == "__main__":
    # Test configuration
    config = setup_environment()
    print("\n📋 Current Configuration:")
    print(f"   API Key: {config.openai_api_key[:8]}...{config.openai_api_key[-4:]}")
    print(f"   Base URL: {config.openai_base_url}")
    print(f"   Embedding Model: {config.embedding_model}")
    print(f"   LLM Model: {config.llm_model}")
