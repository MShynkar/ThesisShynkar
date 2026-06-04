"""Pytest fixtures."""
import os

# Force the tests to use an in-process settings override before anything else loads
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests-only")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("DEBUG", "false")
