FROM python:3.11-slim-bullseye

WORKDIR /app

# Install system dependencies for MSSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gnupg2 ca-certificates unixodbc-dev g++ \
    && curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64,arm64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" \
       > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire service
COPY . .

# Ensure the module is discoverable
ENV PYTHONPATH="/app"

# Run as non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Qualification MS port
EXPOSE 8013

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8013"]
