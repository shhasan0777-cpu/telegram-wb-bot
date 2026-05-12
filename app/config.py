from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    bot_token: str
    getcourse_url: str
    admin_id: int
    channel_url: str
    channel_id: int
    groq_api_key: str
    wb_api_secret_key: str
    database_path: str = "database.db"
    log_level: str = "INFO"
    health_host: str = "0.0.0.0"
    health_port: int = 8080


def get_settings() -> Settings:
    return Settings(
        bot_token=os.getenv("BOT_TOKEN", ""),
        getcourse_url=os.getenv("GETCOURSE_URL", "https://example.com"),
        admin_id=int(os.getenv("ADMIN_ID", "0")),
        channel_url=os.getenv("CHANNEL_URL", ""),
        channel_id=int(os.getenv("CHANNEL_ID", "0")),
        groq_api_key=os.getenv("GROQ_API_KEY", ""),
        wb_api_secret_key=os.getenv("WB_API_SECRET_KEY", ""),
        database_path=os.getenv("DATABASE_PATH", "database.db"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        health_host=os.getenv("HEALTH_HOST", "0.0.0.0"),
        health_port=int(os.getenv("HEALTH_PORT", "8080")),
    )
