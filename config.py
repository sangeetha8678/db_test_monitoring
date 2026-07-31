"""
Configuration settings for the PostgreSQL Telemetry AI Analytics Platform.
Centralized thresholds, database credentials, and AI / ML model parameters.
"""

import os

# Database Settings
PGHOST = os.getenv("PGHOST", "localhost")
PGPORT = int(os.getenv("PGPORT", 5432))
PGDATABASE = os.getenv("PGDATABASE", "postgres")
PGUSER = os.getenv("PGUSER", "postgres")
PGPASSWORD = os.getenv("PGPASSWORD", "")

# CSV Fallback Path
CSV_FILE_PATH = os.path.join(os.path.dirname(__file__), "energymeter_202607301217.csv")

# Ollama & LLM Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen3:8b")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.0))

# Engineering Thresholds (Configurable)
NOMINAL_FREQUENCY = float(os.getenv("NOMINAL_FREQUENCY", 50.0))  # Hz
POWER_FACTOR_THRESHOLD = float(os.getenv("POWER_FACTOR_THRESHOLD", 0.85))  # Ratio
VOLTAGE_IMBALANCE_THRESHOLD = float(os.getenv("VOLTAGE_IMBALANCE_THRESHOLD", 2.0))  # Percentage (%)
CURRENT_IMBALANCE_THRESHOLD = float(os.getenv("CURRENT_IMBALANCE_THRESHOLD", 10.0))  # Percentage (%)
Z_SCORE_THRESHOLD = float(os.getenv("Z_SCORE_THRESHOLD", 3.0))
IQR_MULTIPLIER = float(os.getenv("IQR_MULTIPLIER", 1.5))

# Model Directory
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

# Allowed metrics for security validation
ALLOWED_METRICS = [
    "activepower", "reactivepower", "apparentpower", "importenergykwh",
    "powerfactor", "frequency", "currentavg", "currenta", "currentb", "currentc",
    "voltageab", "voltagebc", "voltageca", "voltagean", "voltagebn", "voltagecn"
]

ALLOWED_AGGREGATIONS = ["average", "avg", "max", "peak", "min", "count", "sum"]
