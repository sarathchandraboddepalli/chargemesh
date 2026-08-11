"""
ChargeMesh — Encryption Service
Fernet symmetric encryption for sensitive tokens stored at rest.
Used for: OEM adapter auth tokens, charging network API keys.
"""

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


_DEFAULT_ENCRYPTION_KEY = "changeme_fernet_key_must_be_32_bytes"


def _get_fernet() -> Fernet:
    """Get or create Fernet cipher. Key must be 32 url-safe base64 bytes."""
    key = settings.ENCRYPTION_KEY
    if key == _DEFAULT_ENCRYPTION_KEY:
        raise RuntimeError(
            "ENCRYPTION_KEY is set to the insecure default value "
            f"'{_DEFAULT_ENCRYPTION_KEY}'. "
            "Set the ENCRYPTION_KEY environment variable to a securely generated "
            "Fernet key before starting the application. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    fernet_key = key.encode() if isinstance(key, str) else key
    return Fernet(fernet_key)


def encrypt(plaintext: str) -> str:
    """Encrypt a string using Fernet symmetric encryption."""
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Decrypt a Fernet-encrypted string."""
    f = _get_fernet()
    try:
        return f.decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        raise ValueError("Failed to decrypt: invalid token or key")
