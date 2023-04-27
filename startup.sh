# Start script for Azure deployment
python -m pip install .
gunicorn --bind 0.0.0.0:5000 --workers 4 "pypi_inspector.app:create_app()"
