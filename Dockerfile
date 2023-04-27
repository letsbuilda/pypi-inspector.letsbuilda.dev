FROM --platform=linux/amd64 python:3.11-slim@sha256:286f2f1d6f2f730a44108656afb04b131504b610a6cb2f3413918e98dabba67e

RUN adduser --disabled-password pypi_inspector
USER pypi_inspector

ENV PATH="${PATH}:/home/pypi_inspector/.local/bin"

# Set Git SHA environment variable
ARG git_sha="development"
ENV GIT_SHA=$git_sha

WORKDIR /app
COPY pyproject.toml src ./
RUN python -m pip install .

EXPOSE 5000

ENTRYPOINT exec gunicorn --bind 0.0.0.0:5000 --workers 4 "pypi_inspector.app:create_app()"
