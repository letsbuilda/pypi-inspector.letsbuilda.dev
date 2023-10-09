FROM --platform=linux/amd64 python:3.12-slim@sha256:43a49c9cc2e614468e3d1a903aabe17a97a4c788c76cf5337b5cdc3535b07d4f

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
