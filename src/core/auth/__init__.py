import jwt
import bcrypt
from datetime import datetime, timezone, timedelta

def _get_config():
    # Import here to avoid circular import with src.core.provider which imports auth providers
    from src.core.provider import CoreProvider
    return CoreProvider().get_config()


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt with rounds from config."""
    conf = _get_config()
    salt = bcrypt.gensalt(rounds=conf.jwt.bcrypt_rounds)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify that a plaintext password matches a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(sub: str, username: str | None = None, **claims) -> str:
    """Create a JWT access token with iat/exp and provided claims.

    The token will include:
    - sub: subject (typically user id)
    - username: optional username
    - iat: issued-at (UTC)
    - exp: expiration (UTC) derived from config.jwt.ttl_minutes
    Any additional keyword claims are merged into the payload.
    """
    conf = _get_config()
    now = datetime.now(tz=timezone.utc)
    exp = now + timedelta(minutes=conf.jwt.ttl_minutes)
    payload = {
        "sub": sub,
        "iat": now,
        "exp": exp,
    }
    if username is not None:
        payload["username"] = username
    if claims:
        payload.update(claims)
    return jwt.encode(payload, conf.jwt.secret_key, algorithm=conf.jwt.algorithm)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token using config secret and algorithm."""
    conf = _get_config()
    return jwt.decode(
        jwt=token,
        key=conf.jwt.secret_key,
        algorithms=[conf.jwt.algorithm],
        options={"verify_signature": True, "verify_exp": True},
    )
