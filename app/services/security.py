import logging
from cryptography.fernet import Fernet, InvalidToken
from app.config import get_settings

log = logging.getLogger(__name__)


def _cipher() -> Fernet:
    key = get_settings().wb_api_secret_key
    if not key:
        raise RuntimeError("WB_API_SECRET_KEY is not set")
    return Fernet(key.encode())


def encrypt_wb_api_key(api_key: str) -> str:
    return "enc:" + _cipher().encrypt(api_key.encode()).decode()


def decrypt_wb_api_key(value: str | None) -> str | None:
    if not value:
        return None
    if not str(value).startswith("enc:"):
        # Backward compatibility for old plain-text rows.
        return str(value)
    try:
        return _cipher().decrypt(str(value)[4:].encode()).decode()
    except InvalidToken:
        log.exception("Failed to decrypt WB API key")
        return None
