import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-only-secret-key-not-for-production",
)
