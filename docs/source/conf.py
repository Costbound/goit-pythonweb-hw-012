from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock

# Set path FIRST
sys.path.insert(0, os.path.abspath("../.."))

# Set environment variables BEFORE any imports
os.environ.setdefault("DB_URL", "postgresql+asyncpg://user:pass@localhost/db")
os.environ.setdefault("JWT_SECRET", "dummy_secret_key_123456")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_SECONDS", "900")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_SECONDS", "604800")
os.environ.setdefault("VERIFICATION_TOKEN_EXPIRE_SECONDS", "86400")
os.environ.setdefault("SMTP_USER", "dummy@example.com")
os.environ.setdefault("SMTP_PASSWORD", "dummy_password")
os.environ.setdefault("SMTP_FROM", "noreply@example.com")
os.environ.setdefault("SMTP_PORT", "587")
os.environ.setdefault("SMTP_HOST", "smtp.example.com")
os.environ.setdefault("CLOUDINARY_CLOUD_NAME", "dummy_cloud")
os.environ.setdefault("CLOUDINARY_API_KEY", "123456789")
os.environ.setdefault("CLOUDINARY_API_SECRET", "dummy_api_secret")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_MAX_MEMORY", "256mb")


# Mock modules that require environment variables
class Mock(MagicMock):
    def __getattr__(self, name):
        return MagicMock()

    def __or__(self, other):
        return MagicMock()

    def __ror__(self, other):
        return MagicMock()


MOCK_MODULES = [
    "pydantic_settings",
    "cloudinary",
    "cloudinary.uploader",
    "sqlalchemy.engine",
    "sqlalchemy.ext.asyncio",
    "redis",
    "redis.asyncio",
]

# Apply mocks BEFORE any imports happen
for mod_name in MOCK_MODULES:
    sys.modules[mod_name] = Mock()

# -- Project information -----------------------------------------------------
project = "goit-pythonweb-hw-12"
copyright = "2024, Your Name"
author = "Your Name"
release = "1.0.0"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]

templates_path = ["_templates"]
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}

# Napoleon settings for better docstring parsing
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_type_aliases = None

# Autodoc settings to avoid import errors
autodoc_mock_imports = [
    "cloudinary",
    "pydantic_settings",
    "sqlalchemy",
    "redis",
    "redis.asyncio",
    "fastapi",
    "slowapi",
    "passlib",
    "jose",
    "python-jose",
]

# Don't show type hints in signatures (they're in the docstring)
autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"

# Intersphinx mapping for external docs
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "fastapi": ("https://fastapi.tiangolo.com", None),
}
