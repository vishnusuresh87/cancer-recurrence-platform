import joblib
import redis
import json
from pathlib import Path
from app.config import settings


class ModelLoader:
    """
    Loads REAL trained RSF model + encoders + metadata
    """
    
    def __init__(self):
        self.redis_client = None
        self.model = None
        self.encoders = None
        self.feature_names = None
        self.metadata = None
        self.model_version = settings.model_version
    
    def _connect_redis(self):
        """Connect to Redis (lazy initialization)"""
        if self.redis_client is None:
            try:
                self.redis_client = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    decode_responses=False
                )
                self.redis_client.ping()
                print(f"✅ Connected to Redis at {settings.redis_host}:{settings.redis_port}")
            except Exception as e:
                print(f"⚠️  Redis not available: {e}")
                self.redis_client = None
    
    def load_model(self):
        """
        Load model, encoders, and metadata from disk or Redis cache
        """
        # Try Redis cache first
        self._connect_redis()
        if self.redis_client:
            cache_key = f"rsf_model_{self.model_version}"
            try:
                cached_model = self.redis_client.get(cache_key)
                if cached_model:
                    print(f"✅ Model loaded from Redis cache")
                    self.model = joblib.loads(cached_model)
                    
                    # Load encoders and metadata from cache too
                    self.encoders = joblib.loads(self.redis_client.get(f"{cache_key}_encoders"))
                    self.feature_names = joblib.loads(self.redis_client.get(f"{cache_key}_features"))
                    self.metadata = json.loads(self.redis_client.get(f"{cache_key}_metadata"))
                    return self.model
            except Exception as e:
                print(f"⚠️  Redis cache miss: {e}")
        
        # Load from disk
        print(f"📁 Loading model from disk...")
        
        model_path = Path(settings.model_path)
        encoders_path = Path(settings.encoders_path)
        feature_names_path = Path(settings.feature_names_path)
        metadata_path = Path(settings.metadata_path)
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found at: {model_path}")
        
        self.model = joblib.load(model_path)
        self.encoders = joblib.load(encoders_path)
        self.feature_names = joblib.load(feature_names_path)
        
        with open(metadata_path) as f:
            self.metadata = json.load(f)
        
        print(f"✅ Model loaded: {self.metadata['model_version']}")
        print(f"   C-index (test): {self.metadata['c_index_test']:.4f}")
        print(f"   Training date: {self.metadata['training_date']}")
        
        # Cache in Redis
        if self.redis_client:
            try:
                cache_key = f"rsf_model_{self.model_version}"
                self.redis_client.setex(cache_key, settings.redis_model_cache_ttl, joblib.dumps(self.model))
                self.redis_client.setex(f"{cache_key}_encoders", settings.redis_model_cache_ttl, joblib.dumps(self.encoders))
                self.redis_client.setex(f"{cache_key}_features", settings.redis_model_cache_ttl, joblib.dumps(self.feature_names))
                self.redis_client.setex(f"{cache_key}_metadata", settings.redis_model_cache_ttl, json.dumps(self.metadata))
                print(f"✅ Model cached in Redis (TTL: {settings.redis_model_cache_ttl}s)")
            except Exception as e:
                print(f"⚠️  Failed to cache: {e}")
        
        return self.model
    
    def get_model(self):
        """Get cached model or load if not cached"""
        if self.model is None:
            self.load_model()
        return self.model
    
    def get_metadata(self):
        """Get model metadata"""
        if self.metadata is None:
            self.load_model()
        return self.metadata


# Global instance
model_loader = ModelLoader()