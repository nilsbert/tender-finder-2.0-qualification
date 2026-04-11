# Hardened Production Microservice Dockerfile
FROM python:3.11-slim-bullseye

# System dependencies for msodbcsql18 (Debian Bullseye)
RUN apt-get update && apt-get install -y --no-install-recommends     curl gnupg2 ca-certificates unixodbc-dev g++     && curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg     && echo "deb [arch=amd64,arm64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" > /etc/apt/sources.list.d/mssql-release.list     && apt-get update && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18     && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Ensure we have a root __init__.py
RUN touch /app/__init__.py

# Copy shared core (cached layer)
COPY shared/ ./shared/
RUN pip install --no-cache-dir -e ./shared

# Copy THIS service only
COPY qualification/ ./qualification/
RUN pip install --no-cache-dir -r ./qualification/requirements.txt

# Force set PYTHONPATH to ensure everything is discoverable
ENV PYTHONPATH="/app"

# Explicitly set the service port (overridden in compose.yml, but good to have)
# Note: In uvicorn, the port should match what we use in nginx.conf
# Each service has a specific port in compose.yml, let's stick to 8000 for simplicity?
# No, let's stick to the ones in compose.yml to avoid port binding errors.
CMD ["python3", "-m", "uvicorn", "qualification.main:app", "--host", "0.0.0.0", "--port", "8004"]
