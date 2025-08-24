# Site2MD Production Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libxml2-dev \
    libxslt-dev \
    libz-dev \
    libjpeg-dev \
    libfreetype6-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /home/app

# Copy requirements and install dependencies
COPY --chown=app:app pyproject.toml ./
COPY --chown=app:app src/ ./src/

# Install the application
RUN pip install --user -e ".[web]"

# Add local bin to PATH
ENV PATH="/home/app/.local/bin:${PATH}"

# Copy static files
COPY --chown=app:app src/site2md/web/static ./src/site2md/web/static
COPY --chown=app:app src/site2md/web/templates ./src/site2md/web/templates

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/ || exit 1

# Expose port
EXPOSE ${PORT}

# Run the web application
CMD ["sh", "-c", "python -m site2md.web.main --host 0.0.0.0 --port ${PORT}"]