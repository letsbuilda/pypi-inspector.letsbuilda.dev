"""Testing app creation"""

from flask import Flask

from pypi_inspector.app import create_app


def test_create_app_should_build_flask_app() -> None:
    assert isinstance(create_app(), Flask)
