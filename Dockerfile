FROM --platform=linux/amd64 python:3.11-slim@sha256:5a67c38a7c28ad09d08f4e153280023a2df77189b55af7804d7ceb96fee6a68f

RUN adduser --disabled-password pypi_inspector
USER pypi-inspector

ENV PATH="${PATH}:/home/pypi-inspector/.local/bin"

# Set Git SHA environment variable
ARG git_sha="development"
ENV GIT_SHA=$git_sha

WORKDIR /app
COPY pyproject.toml src ./
RUN python -m pip install .

EXPOSE 5000

ENTRYPOINT exec gunicorn --bind 0.0.0.0:5000 --workers 4 "pypi_inspector.app:create_app()"
