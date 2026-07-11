FROM python:3.12-slim

# Install system dependencies for audio rendering and ffmpeg codec decoders
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency manifest
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose API port
EXPOSE 8000

# Run API by default
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
