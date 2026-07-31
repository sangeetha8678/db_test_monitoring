"""
Model Registry & Persistence Module.
Saves and loads trained models, scalers, and configuration metadata under the models/ directory.
Does NOT retrain models on server startup.
"""

import os
import json
from config import MODELS_DIR

class ModelRegistry:
    @staticmethod
    def save_model_metadata(model_name, metadata):
        if not os.path.exists(MODELS_DIR):
            os.makedirs(MODELS_DIR, exist_ok=True)
        path = os.path.join(MODELS_DIR, f"{model_name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        print(f"Saved model metadata for '{model_name}' to {path}")

    @staticmethod
    def load_model_metadata(model_name):
        path = os.path.join(MODELS_DIR, f"{model_name}.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
