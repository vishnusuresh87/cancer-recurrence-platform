import joblib
import redis
import json
import httpx
import threading
import time
from datetime import datetime
from pathlib import Path
from app.config import settings


class ModelLoader:
    """
    Loads REAL trained RSF model + encoders + metadata
    """
    
    def __init__(self):
        self.redis_client = None
        self.model = None
        self.encoders = {}
        self.feature_names = []
        self.metadata = None
        self.model_version = "None"
        self.last_check_time = 0
        self.shutdown_event = threading.Event()
        
        # Start background polling thread
        self._start_poller()
    
    def _start_poller(self):
        """Starts a background thread to poll for model updates"""
        thread = threading.Thread(target=self._poll_loop, daemon=True)
        thread.start()
        print("⏲️  Model poller started (6-hour interval)")

    def _poll_loop(self):
        """Infinite loop for polling the management service"""
        while not self.shutdown_event.is_set():
            try:
                self.sync_with_production()
            except Exception as e:
                print(f"⚠️  Model sync failed: {e}")
            
            # Sleep for configured interval OR until shutdown event is set
            self.shutdown_event.wait(settings.model_poll_interval)

    def stop(self):
        """Signal the background thread to stop immediately"""
        print("🛑 Stopping model poller...")
        self.shutdown_event.set()

    def sync_with_production(self):
        """
        Check with model-management-service if there is a newer production model.
        If yes, reload it in memory.
        """
        url = f"{settings.model_management_url}/api/v1/models/production"
        print(f"🔍 Checking for model updates at {url}...")
        
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                if response.status_code == 200:
                    prod_info = response.json()
                    new_version = prod_info['version']
                    new_path = prod_info['storage_path']
                    
                    if new_version != self.model_version:
                        print(f"✨ New production model detected: {new_version}. Reloading...")
                        self.load_model(custom_path=new_path, version_name=new_version)
                    else:
                        print(f"✅ Model up to date ({self.model_version})")
                else:
                    print(f"⚠️  Model management service returned {response.status_code}")
        except Exception as e:
            print(f"⚠️  Could not reach model-management-service: {e}")
    
    
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
    
    def load_model(self, custom_path=None, version_name=None):
        """
        Load logical pipeline from disk.
        Supports both legacy multi-file models and new unified pipelines.
        """
        self._connect_redis()
        
        # Determine path
        model_path_str = custom_path or settings.model_path
        model_path = Path(model_path_str)
        
        if not model_path.exists():
            # Try absolute path if relative fails (for docker mounts)
            alt_path = Path("/ml-pipeline/models") / model_path.name
            if alt_path.exists():
                model_path = alt_path
            else:
                print(f"❌ Model not found at {model_path} or {alt_path}")
                return None

        print(f"📁 Loading model from {model_path}...")
        
        try:
            loaded_obj = joblib.load(model_path)
            # Legacy/Unified loading
            self.model = loaded_obj
            self.model_version = version_name or model_path.stem

            # Load Encoders
            encoders_path = model_path.with_name(model_path.stem + "_encoders.pkl")
            if encoders_path.exists():
                self.encoders = joblib.load(encoders_path)
                print(f"✅ Loaded {len(self.encoders)} categorical encoders")
            
            # Load Feature Names
            features_path = model_path.with_name(model_path.stem + "_feature_names.pkl")
            if features_path.exists():
                self.feature_names = joblib.load(features_path)
                print(f"✅ Loaded feature list ({len(self.feature_names)} features)")
            
            # Log success
            print(f"✅ Model swapped in-memory: {self.model_version}")
            
            # Simple metadata mock if json doesn't exist for the new path
            metadata_path = model_path.with_name(model_path.stem + "_metadata.json")
            if metadata_path.exists():
                with open(metadata_path) as f:
                    self.metadata = json.load(f)
            else:
                self.metadata = {
                    "model_version": self.model_version,
                    "last_reloaded": datetime.utcnow().isoformat()
                }

            # Cache in Redis for other workers
            if self.redis_client:
                try:
                    cache_key = f"active_model_pipeline"
                    self.redis_client.setex(cache_key, settings.redis_model_cache_ttl, joblib.dumps(self.model))
                    self.redis_client.set(f"active_model_version", self.model_version)
                except Exception as e:
                    print(f"⚠️  Failed to cache in Redis: {e}")
            
            return self.model
            
        except Exception as e:
            print(f"❌ Critical error loading model: {e}")
            return None
    
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

    def get_encoders(self):
        """Get categorical encoders"""
        if not self.encoders:
            self.load_model()
        return self.encoders

    def get_feature_names(self):
        """Get list of features in training order"""
        if not self.feature_names:
            self.load_model()
        return self.feature_names


# Global instance
model_loader = ModelLoader()