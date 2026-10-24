"""Simple authentication and role-based authorization for the POS MVP.

Login verifies a bcrypt password hash and issues a short-lived JWT carrying the
username and role. The signing secret is read from an environment override (for
local dev/tests) or from AWS SSM Parameter Store by name (production). It is
never stored in code or the repo.

`require_role` is a FastAPI dependency factory that validates the bearer token
and enforces the allowed roles.
"""
from __future__ import annotations

import functools
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings, get_settings
from app.errors import ForbiddenError, InvalidCredentialsError

_bearer = HTTPBearer(auto_error=False)

# bcrypt operates on at most 72 bytes; longer passwords are truncated by the
# algorithm. We accept inputs as-is (bcrypt handles the truncation internally).


def _truncate(plain: str) -> bytes:
    # bcrypt only considers the first 72 bytes; truncate explicitly to avoid
    # ValueError on longer inputs in newer bcrypt versions.
    return plain.encode("utf-8")[:72]


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(_truncate(plain), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(_truncate(plain), password_hash.encode("utf-8"))
    except ValueError:
        return False


@functools.lru_cache(maxsize=1)
def _resolve_secret(param_name: str, env_override: Optional[str], region: str) -> str:
    """Resolve the JWT signing secret.

    Prefers an explicit environment override (dev/test). Otherwise fetches a
    SecureString from SSM Parameter Store by name. Cached to avoid repeated
    SSM calls per invocation.
    """
    if env_override:
        return env_override
    import boto3

    ssm = boto3.client("ssm", region_name=region)
    response = ssm.get_parameter(Name=param_name, WithDecryption=True)
    return response["Parameter"]["Value"]


def _get_secret(settings: Settings) -> str:
    return _resolve_secret(
        settings.jwt_secret_param, settings.jwt_secret_env, settings.aws_region
    )


def issue_token(username: str, role: str, settings: Optional[Settings] = None) -> str:
    """Sign a JWT with subject (username), role and expiry."""
    settings = settings or get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=settings.jwt_ttl_seconds)).timestamp()),
    }
    return jwt.encode(payload, _get_secret(settings), algorithm=settings.jwt_algorithm)


def decode_token(token: str, settings: Optional[Settings] = None) -> dict:
    """Decode and validate a JWT; raise InvalidCredentialsError on failure."""
    settings = settings or get_settings()
    try:
        return jwt.decode(
            token, _get_secret(settings), algorithms=[settings.jwt_algorithm]
        )
    except jwt.PyJWTError as exc:
        raise InvalidCredentialsError("Sesión inválida o expirada") from exc


def authenticate(username: str, password: str, repository) -> str:
    """Verify credentials and return a signed JWT, or raise on failure."""
    user = repository.get_user(username)
    if user is None or not verify_password(password, user["password_hash"]):
        raise InvalidCredentialsError()
    return issue_token(user["username"], user["role"])


class CurrentUser:
    """The authenticated principal extracted from the token."""

    def __init__(self, username: str, role: str) -> None:
        self.username = username
        self.role = role


def require_role(*roles: str):
    """FastAPI dependency: validate the bearer token and enforce roles."""

    def dependency(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    ) -> CurrentUser:
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o clave incorrectos",
            )
        try:
            claims = decode_token(credentials.credentials)
        except InvalidCredentialsError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message
            ) from exc
        role = claims.get("role")
        if roles and role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ForbiddenError().message,
            )
        return CurrentUser(username=claims.get("sub"), role=role)

    return dependency
