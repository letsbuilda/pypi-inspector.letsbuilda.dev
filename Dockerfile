FROM --platform=linux/amd64 python:3.11-slim@sha256:551c9529e77896518ac5693d7e98ee5e12051d625de450ac2a68da1eae15ec87

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
