"""
Configuration loader for HyperGraphRAG
Supports loading from .env file or environment variables
"""
import os
from pathlib import Path
from typing import Optional


class Config:
    """Configuration class for HyperGraphRAG and DynHyperRAG"""

    def __init__(self):
        # Try to load from .env file if it exists
        self._load_env_file()

        # Load basic configuration
        self.openai_api_key = self._get_env("OPENAI_API_KEY")
        self.openai_base_url = self._get_env("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.embedding_model = self._get_env("EMBEDDING_MODEL", "text-embedding-3-small")
        self.llm_model = self._get_env("LLM_MODEL", "gpt-4o-mini")
        self.log_level = self._get_env("LOG_LEVEL", "INFO")
        
        # DynHyperRAG: Quality Assessment Configuration
        self.quality_enabled = self._get_bool_env("DYNHYPERRAG_QUALITY_ENABLED", True)
        self.quality_feature_weights = {
            "degree_centrality": float(self._get_env("QUALITY_WEIGHT_DEGREE", "0.2")),
            "betweenness": float(self._get_env("QUALITY_WEIGHT_BETWEENNESS", "0.15")),
            "clustering": float(self._get_env("QUALITY_WEIGHT_CLUSTERING", "0.15")),
            "coherence": float(self._get_env("QUALITY_WEIGHT_COHERENCE", "0.3")),
            "text_quality": float(self._get_env("QUALITY_WEIGHT_TEXT", "0.2")),
        }
        self.quality_mode = self._get_env("QUALITY_MODE", "unsupervised")  # unsupervised or supervised
        
        # DynHyperRAG: Dynamic Weight Update Configuration
        self.dynamic_update_enabled = self._get_bool_env("DYNHYPERRAG_DYNAMIC_ENABLED", True)
        self.update_strategy = self._get_env("DYNAMIC_UPDATE_STRATEGY", "ema")  # ema, additive, multiplicative
        self.update_alpha = float(self._get_env("DYNAMIC_UPDATE_ALPHA", "0.1"))
        self.decay_factor = float(self._get_env("DYNAMIC_DECAY_FACTOR", "0.99"))
        self.feedback_method = self._get_env("DYNAMIC_FEEDBACK_METHOD", "embedding")  # embedding, citation, attention
        self.feedback_threshold = float(self._get_env("DYNAMIC_FEEDBACK_THRESHOLD", "0.7"))
        
        # DynHyperRAG: Hyperedge Refinement Configuration
        self.refiner_enabled = self._get_bool_env("DYNHYPERRAG_REFINER_ENABLED", False)
        self.quality_threshold = float(self._get_env("REFINER_QUALITY_THRESHOLD", "0.5"))
        self.soft_filter = self._get_bool_env("REFINER_SOFT_FILTER", True)
        
        # DynHyperRAG: Efficient Retrieval Configuration
        self.entity_filter_enabled = self._get_bool_env("DYNHYPERRAG_ENTITY_FILTER_ENABLED", True)
        self.domain = self._get_env("RETRIEVAL_DOMAIN", "medical")  # medical, legal, academic
        self.entity_taxonomy = self._load_entity_taxonomy()
        self.similarity_weight = float(self._get_env("RETRIEVAL_SIMILARITY_WEIGHT", "0.5"))
        self.quality_weight = float(self._get_env("RETRIEVAL_QUALITY_WEIGHT", "0.3"))
        self.dynamic_weight = float(self._get_env("RETRIEVAL_DYNAMIC_WEIGHT", "0.2"))
        
        # DynHyperRAG: Lite Mode Configuration
        self.lite_mode = self._get_bool_env("DYNHYPERRAG_LITE_MODE", False)
        self.cache_size = int(self._get_env("LITE_CACHE_SIZE", "1000"))

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
    
    def _get_bool_env(self, key: str, default: bool = False) -> bool:
        """Get boolean environment variable"""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")
    
    def _load_entity_taxonomy(self) -> dict:
        """Load entity taxonomy for different domains"""
        # Default taxonomies - aligned with CAIL2019Loader.ENTITY_TYPES and AcademicLoader.ENTITY_TYPES
        default_taxonomy = {
            "medical": ["disease", "symptom", "treatment", "medication", "procedure", "anatomy"],
            "legal": ["law", "article", "court", "party", "crime", "penalty"],  # CAIL2019 legal domain
            "academic": ["paper", "author", "institution", "keyword", "conference", "journal"],  # Academic domain
        }
        
        # Allow custom taxonomy from environment (comma-separated)
        custom_types = os.getenv(f"ENTITY_TYPES_{self.domain.upper()}")
        if custom_types:
            default_taxonomy[self.domain] = [t.strip() for t in custom_types.split(",")]
        
        return default_taxonomy

    def validate(self):
        """Validate that all required configuration is present"""
        if not self.openai_api_key or self.openai_api_key == "your_api_key_here":
            raise ValueError(
                "OPENAI_API_KEY is not configured properly.\n"
                "Please set it in .env file or environment variable."
            )

        # Validate DynHyperRAG configuration
        self._validate_dynhyperrag_config()

        print("✅ Configuration validated successfully")
        print(f"   API Base URL: {self.openai_base_url}")
        print(f"   Embedding Model: {self.embedding_model}")
        print(f"   LLM Model: {self.llm_model}")
        
        if self.quality_enabled or self.dynamic_update_enabled or self.entity_filter_enabled:
            print("\n🔬 DynHyperRAG Features:")
            if self.quality_enabled:
                print(f"   ✓ Quality Assessment: {self.quality_mode} mode")
            if self.dynamic_update_enabled:
                print(f"   ✓ Dynamic Update: {self.update_strategy} strategy (α={self.update_alpha})")
            if self.entity_filter_enabled:
                print(f"   ✓ Entity Filtering: {self.domain} domain")
            if self.lite_mode:
                print(f"   ✓ Lite Mode: Enabled (cache={self.cache_size})")
        
        return True
    
    def _validate_dynhyperrag_config(self):
        """Validate DynHyperRAG-specific configuration"""
        # Validate quality feature weights sum to 1.0
        if self.quality_enabled:
            weight_sum = sum(self.quality_feature_weights.values())
            if not (0.99 <= weight_sum <= 1.01):  # Allow small floating point error
                raise ValueError(
                    f"Quality feature weights must sum to 1.0, got {weight_sum:.3f}\n"
                    f"Current weights: {self.quality_feature_weights}"
                )
            
            if self.quality_mode not in ["unsupervised", "supervised"]:
                raise ValueError(
                    f"Invalid quality_mode: {self.quality_mode}. "
                    f"Must be 'unsupervised' or 'supervised'"
                )
        
        # Validate update strategy
        if self.dynamic_update_enabled:
            if self.update_strategy not in ["ema", "additive", "multiplicative"]:
                raise ValueError(
                    f"Invalid update_strategy: {self.update_strategy}. "
                    f"Must be 'ema', 'additive', or 'multiplicative'"
                )
            
            if not (0.0 < self.update_alpha <= 1.0):
                raise ValueError(
                    f"update_alpha must be in (0, 1], got {self.update_alpha}"
                )
            
            if not (0.0 < self.decay_factor <= 1.0):
                raise ValueError(
                    f"decay_factor must be in (0, 1], got {self.decay_factor}"
                )
            
            if self.feedback_method not in ["embedding", "citation", "attention"]:
                raise ValueError(
                    f"Invalid feedback_method: {self.feedback_method}. "
                    f"Must be 'embedding', 'citation', or 'attention'"
                )
        
        # Validate retrieval weights
        if self.entity_filter_enabled:
            weight_sum = self.similarity_weight + self.quality_weight + self.dynamic_weight
            if not (0.99 <= weight_sum <= 1.01):
                raise ValueError(
                    f"Retrieval weights must sum to 1.0, got {weight_sum:.3f}\n"
                    f"similarity={self.similarity_weight}, quality={self.quality_weight}, "
                    f"dynamic={self.dynamic_weight}"
                )
            
            if self.domain not in self.entity_taxonomy:
                raise ValueError(
                    f"Invalid domain: {self.domain}. "
                    f"Must be one of {list(self.entity_taxonomy.keys())}"
                )

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
    
    def get_quality_config(self) -> dict:
        """Get quality assessment configuration"""
        return {
            "enabled": self.quality_enabled,
            "feature_weights": self.quality_feature_weights,
            "mode": self.quality_mode,
        }
    
    def get_dynamic_config(self) -> dict:
        """Get dynamic weight update configuration"""
        return {
            "enabled": self.dynamic_update_enabled,
            "strategy": self.update_strategy,
            "update_alpha": self.update_alpha,
            "decay_factor": self.decay_factor,
            "feedback_method": self.feedback_method,
            "feedback_threshold": self.feedback_threshold,
        }
    
    def get_refiner_config(self) -> dict:
        """Get hyperedge refiner configuration"""
        return {
            "enabled": self.refiner_enabled,
            "quality_threshold": self.quality_threshold,
            "soft_filter": self.soft_filter,
        }
    
    def get_retrieval_config(self) -> dict:
        """Get efficient retrieval configuration"""
        return {
            "entity_filter_enabled": self.entity_filter_enabled,
            "domain": self.domain,
            "entity_taxonomy": self.entity_taxonomy,
            "similarity_weight": self.similarity_weight,
            "quality_weight": self.quality_weight,
            "dynamic_weight": self.dynamic_weight,
        }
    
    def get_lite_config(self) -> dict:
        """Get lite mode configuration"""
        return {
            "enabled": self.lite_mode,
            "cache_size": self.cache_size,
        }
    
    def get_dynhyperrag_config(self) -> dict:
        """Get complete DynHyperRAG configuration"""
        return {
            "quality": self.get_quality_config(),
            "dynamic": self.get_dynamic_config(),
            "refiner": self.get_refiner_config(),
            "retrieval": self.get_retrieval_config(),
            "lite": self.get_lite_config(),
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
