FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories with proper permissions
RUN mkdir -p static templates && \
    chmod 755 static templates

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE ${APP_PORT}

# Command to run the application
CMD ["sh", "-c", "uvicorn app.main:app --host ${APP_HOST} --port ${APP_PORT}"] 