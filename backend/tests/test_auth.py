"""Tests for authentication and role authorization (Requirement 7)."""
import pytest
from fastapi import HTTPException

from app import auth
from app.config import Settings
from app.errors import InvalidCredentialsError


@pytest.fixture(autouse=True)
def _clear_secret_cache():
    auth._resolve_secret.cache_clear()
    yield
    auth._resolve_secret.cache_clear()


def _settings():
    s = Settings()
    s.jwt_secret_env = "test-secret-not-in-repo"
    return s


def test_hash_and_verify_password():
    h = auth.hash_password("clave123")
    assert auth.verify_password("clave123", h)
    assert not auth.verify_password("otra", h)


def test_issue_and_decode_token_roundtrip():
    s = _settings()
    token = auth.issue_token("ana", "cajero", settings=s)
    claims = auth.decode_token(token, settings=s)
    assert claims["sub"] == "ana"
    assert claims["role"] == "cajero"


def test_decode_invalid_token_raises():
    s = _settings()
    with pytest.raises(InvalidCredentialsError):
        auth.decode_token("not-a-jwt", settings=s)


def test_authenticate_success(repository, monkeypatch):
    monkeypatch.setenv("POS_JWT_SECRET", "test-secret-not-in-repo")
    repository.upsert_user("ana", auth.hash_password("clave123"), "cajero")
    # get_settings is cached; patch the resolved secret path via env override.
    from app.config import get_settings

    get_settings.cache_clear()
    token = auth.authenticate("ana", "clave123", repository)
    assert isinstance(token, str) and token.count(".") == 2
    get_settings.cache_clear()


def test_authenticate_bad_password(repository, monkeypatch):
    monkeypatch.setenv("POS_JWT_SECRET", "test-secret-not-in-repo")
    from app.config import get_settings

    get_settings.cache_clear()
    repository.upsert_user("ana", auth.hash_password("clave123"), "cajero")
    with pytest.raises(InvalidCredentialsError):
        auth.authenticate("ana", "incorrecta", repository)
    get_settings.cache_clear()


def test_authenticate_unknown_user(repository, monkeypatch):
    monkeypatch.setenv("POS_JWT_SECRET", "test-secret-not-in-repo")
    from app.config import get_settings

    get_settings.cache_clear()
    with pytest.raises(InvalidCredentialsError):
        auth.authenticate("nadie", "x", repository)
    get_settings.cache_clear()


def test_require_role_allows_matching_role():
    s = _settings()
    token = auth.issue_token("dueno", "dueno", settings=s)

    from app.config import get_settings

    get_settings.cache_clear()
    import os

    os.environ["POS_JWT_SECRET"] = "test-secret-not-in-repo"
    dep = auth.require_role("dueno")
    from fastapi.security import HTTPAuthorizationCredentials

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    user = dep(credentials=creds)
    assert user.role == "dueno"
    get_settings.cache_clear()
    del os.environ["POS_JWT_SECRET"]


def test_require_role_denies_wrong_role():
    import os

    os.environ["POS_JWT_SECRET"] = "test-secret-not-in-repo"
    from app.config import get_settings

    get_settings.cache_clear()
    s = _settings()
    token = auth.issue_token("ana", "cajero", settings=s)
    dep = auth.require_role("dueno")
    from fastapi.security import HTTPAuthorizationCredentials

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    with pytest.raises(HTTPException) as exc:
        dep(credentials=creds)
    assert exc.value.status_code == 403
    get_settings.cache_clear()
    del os.environ["POS_JWT_SECRET"]


def test_require_role_missing_token_is_401():
    dep = auth.require_role("cajero")
    with pytest.raises(HTTPException) as exc:
        dep(credentials=None)
    assert exc.value.status_code == 401
