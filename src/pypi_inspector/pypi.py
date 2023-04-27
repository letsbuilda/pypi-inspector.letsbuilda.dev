"""main"""

from flask import Blueprint

pypi_bp = Blueprint("pypi", __name__, template_folder="templates")


@pypi_bp.route("/")
async def index():
    """index"""
    return "<h1>Hello, World!</h1>"
