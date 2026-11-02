import os
from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings

# Load .env into the environment without reading or exposing its content directly.
load_dotenv()

# Bridge API key variable names for Google Gemini support
if os.environ.get("GOOGLE_API_KEY") and not os.environ.get("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]
elif os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]


class Settings(BaseSettings):
    google_client_id: str
    google_client_secret: str
    google_refresh_token: str
    database_url: str
    classifier_model: str = "google:gemini-3.5-flash-lite"
    agent_model: str = "google:gemini-3.5-flash-lite"
    poll_interval_seconds: int = 60
    dashboard_username: str = "admin"
    dashboard_password: str = ""

    @field_validator("classifier_model", "agent_model", mode="before")
    @classmethod
    def normalize_model(cls, v: str) -> str:
        if isinstance(v, str):
            if v.startswith("gemini:"):
                v = "google:" + v[len("gemini:") :]
            # gemini-2.5-pro is deprecated/retired by Google (returns 404)
            # gemini-2.5-flash has an extremely low 5 RPM quota on free tier causing 429
            # Use gemini-3.5-flash-lite for reliable throughput and speed
            if any(legacy in v for legacy in ("gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0", "gemini-1.5")):
                v = "google:gemini-3.5-flash-lite"
        return v


settings = Settings()
