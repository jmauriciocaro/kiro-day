"""Seed initial POS users into DynamoDB.

Reads credentials from environment variables so no secrets live in the repo:

    POS_SEED_CASHIER_USER / POS_SEED_CASHIER_PASS
    POS_SEED_OWNER_USER   / POS_SEED_OWNER_PASS

Usage:
    POS_TABLE_NAME=pos AWS_REGION=us-east-1 \
    POS_SEED_CASHIER_USER=ana POS_SEED_CASHIER_PASS=... \
    POS_SEED_OWNER_USER=don  POS_SEED_OWNER_PASS=... \
    python scripts/seed_users.py
"""
from __future__ import annotations

import os
import sys

# Allow running from the backend/ directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.auth import hash_password  # noqa: E402
from app.repository import Repository  # noqa: E402


def _seed(repo: Repository, user_env: str, pass_env: str, role: str) -> None:
    username = os.environ.get(user_env)
    password = os.environ.get(pass_env)
    if not username or not password:
        print(f"Skipping {role}: {user_env}/{pass_env} not set")
        return
    repo.upsert_user(username, hash_password(password), role)
    print(f"Seeded {role}: {username}")


def main() -> None:
    repo = Repository()
    _seed(repo, "POS_SEED_CASHIER_USER", "POS_SEED_CASHIER_PASS", "cajero")
    _seed(repo, "POS_SEED_OWNER_USER", "POS_SEED_OWNER_PASS", "dueno")


if __name__ == "__main__":
    main()
