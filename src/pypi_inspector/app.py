"""Build an app instance"""

import urllib.parse
from os import getenv

import sentry_sdk
from flask import Flask
from sentry_sdk.integrations.flask import FlaskIntegration

from .routes import pypi_bp


def create_app() -> Flask:
    """Create an app"""
    release_prefix = getenv("PYPI_INSPECTOR_SENTRY_RELEASE_PREFIX", "pypi_inspector")
    git_sha = getenv("GIT_SHA", "development")
    sentry_sdk.init(
        dsn=getenv("PYPI_INSPECTOR_SENTRY_DSN"),
        environment=getenv("PYPI_INSPECTOR_SENTRY_ENV"),
        integrations=[FlaskIntegration()],
        send_default_pii=True,
        traces_sample_rate=0.25,
        profiles_sample_rate=0.25,
        release=f"{release_prefix}@{git_sha}",
    )

    app: Flask = Flask(__name__)

    app.config.update(SECRET_KEY=getenv("PYPI_INSPECTOR_FLASK_SECRET"))

    app.register_blueprint(pypi_bp)

    @app.context_processor
    def inject_data():
        """Inject data into Jinja environment"""
        return dict(git_sha=git_sha)

    app.jinja_env.filters["unquote"] = lambda u: urllib.parse.unquote(u)

    if not app.debug and not app.testing:
        class CustomProxyFix:
            """CustomProxyFix"""

            def __init__(self, app_):
                self.app = app_

            def __call__(self, environ, start_response):
                environ["HTTP_HOST"] = getenv("PYPI_INSPECTOR_HOST")
                environ["wsgi.url_scheme"] = "https"
                return self.app(environ, start_response)

        app.wsgi_app = CustomProxyFix(app.wsgi_app)

    return app
