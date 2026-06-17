from pathlib import Path
import os

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "backend" / "data"
DB_PATH = DATA_DIR / "prelegal.db"

JWT_SECRET = os.getenv("JWT_SECRET", "change-this-secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
LITELLM_MODEL = os.getenv(
    "LITELLM_MODEL", "openrouter/openai/gpt-oss-120b"
)
LITELLM_PROVIDER = os.getenv("LITELLM_PROVIDER", "cerebras")
