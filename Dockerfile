FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy project
COPY . .

# Install Python deps
RUN pip install --no-cache-dir -e . && \
    pip install --no-cache-dir fastapi uvicorn[standard] httpx pydantic python-dotenv

EXPOSE 8080

# Run the simplified backend
CMD ["python3", "backend/backend.py"]
