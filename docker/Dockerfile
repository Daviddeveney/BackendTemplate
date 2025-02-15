# Base Python image
FROM python:3.11-slim as python-base

# Python environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# Working directory
WORKDIR /app

# Common build stage with shared dependencies
FROM python-base as builder

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    # Playwright dependencies
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libexpat1 \
    libxcb1 \
    libxkbcommon0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install Playwright browser
RUN playwright install chromium

# Development stage
FROM builder as development
ENV DJANGO_ENV=development

# Accept build arguments
ARG BROWSERBASE_API_KEY
ARG BROWSERBASE_PROJECT_ID
ARG FIREBASE_API_KEY

# Set environment variables
ENV BROWSERBASE_API_KEY=$BROWSERBASE_API_KEY \
    BROWSERBASE_PROJECT_ID=$BROWSERBASE_PROJECT_ID \
    FIREBASE_API_KEY=$FIREBASE_API_KEY

# Create certs directory (credentials will be mounted via volume)
RUN mkdir -p /app/certs

# Copy project files
COPY . .

# Production stage
FROM builder as production
ENV DJANGO_ENV=production

# Accept build arguments
ARG BROWSERBASE_API_KEY
ARG BROWSERBASE_PROJECT_ID
ARG FIREBASE_API_KEY

# Set environment variables
ENV BROWSERBASE_API_KEY=$BROWSERBASE_API_KEY \
    BROWSERBASE_PROJECT_ID=$BROWSERBASE_PROJECT_ID \
    FIREBASE_API_KEY=$FIREBASE_API_KEY

# Create certs directory and add Firebase credentials
RUN mkdir -p /app/certs
RUN --mount=type=secret,id=firebase_credentials,target=/app/certs/firebase-credentials.json \
    cp /app/certs/firebase-credentials.json /app/certs/roundreservemvp-ac1bd-firebase-adminsdk-fbsvc-8b78f624c5.json

# Copy project files
COPY . .

# Collect static files
RUN python src/manage.py collectstatic --noinput

# Run gunicorn
CMD ["gunicorn", "--chdir", "src", "--bind", ":8000", "core.wsgi:application"] 