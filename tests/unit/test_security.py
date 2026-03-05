from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hashing():
    hashed = hash_password("test123")
    assert hashed != "test123"
    assert verify_password("test123", hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_token():
    token = create_access_token({"sub": "user-123"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "user-123"


def test_invalid_jwt():
    payload = decode_access_token("invalid.token.here")
    assert payload is None
