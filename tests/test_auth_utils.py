from core.auth import hash_password, verify_password
from core.auth import create_access_token, decode_token


def test_hash_and_verify_password():
    pwd = "S3cret!pass"
    h = hash_password(pwd)
    assert h != pwd
    assert verify_password(pwd, h) is True
    assert verify_password("wrong", h) is False


def test_jwt_create_and_decode():
    token = create_access_token("user-id-123", "alice")
    data = decode_token(token)
    assert data["sub"] == "user-id-123"
    assert data["username"] == "alice"
    assert "iat" in data and "exp" in data
    assert data["exp"] > data["iat"]
