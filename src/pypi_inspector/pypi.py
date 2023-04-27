"""main"""

from os import getenv

from flask import Blueprint

pypi_bp = Blueprint("pypi", __name__, template_folder="templates")


@pypi_bp.route("/")
async def index():
    """index"""
    release_prefix = getenv("PYPI_INSPECTOR_SENTRY_RELEASE_PREFIX", "pypi_inspector")
    git_sha = getenv("GIT_SHA", "development")
    return f"<h1>{release_prefix}@{git_sha}</h1>"
