#!/bin/bash

# Exit on error
set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Load environment variables
ENV_FILE="${PROJECT_ROOT}/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Environment file not found at $ENV_FILE"
    echo "Please ensure .env file exists and is properly configured"
    exit 1
fi

echo "📝 Loading environment variables from $ENV_FILE"
set -a
source "$ENV_FILE"
set +a

echo "🚀 Starting deployment process..."

# Login to ECR
echo "📦 Logging into Amazon ECR..."
if ! aws ecr get-login-password --region ${AWS_REGION:-us-east-2} | docker login --username AWS --password-stdin ${ECR_REGISTRY:-424029273204.dkr.ecr.us-east-2.amazonaws.com}; then
    echo "❌ Failed to login to ECR"
    exit 1
fi

# Pull latest image
echo "⬇️ Pulling latest image..."
if ! docker pull ${ECR_REGISTRY:-424029273204.dkr.ecr.us-east-2.amazonaws.com}/${ECR_REPOSITORY:-roundreserve-backend}:latest; then
    echo "❌ Failed to pull latest image"
    exit 1
fi

# Stop and remove ALL containers including orphaned ones
echo "🛑 Stopping all containers..."
docker-compose -f "$PROJECT_ROOT/docker/docker-compose.prod.yml" down --remove-orphans || true

# Additional cleanup to ensure no containers are using our ports
echo "🧹 Performing additional cleanup..."
# Find and stop any container using port 80
PORT_80_CONTAINER=$(docker ps -q --filter "publish=80")
if [ ! -z "$PORT_80_CONTAINER" ]; then
    echo "Found container using port 80, stopping it..."
    docker stop $PORT_80_CONTAINER || true
    docker rm $PORT_80_CONTAINER || true
fi

# Remove all stopped containers and unused networks
echo "🧹 Cleaning up docker resources..."
docker system prune -f

# Verify port 80 is free
if lsof -Pi :80 -sTCP:LISTEN -t >/dev/null ; then
    echo "❌ Port 80 is still in use. Please check running processes."
    exit 1
fi

# Start new containers
echo "🌟 Starting new containers..."
if ! docker-compose -f "$PROJECT_ROOT/docker/docker-compose.prod.yml" up -d; then
    echo "❌ Failed to start containers"
    echo "Checking container logs..."
    docker-compose -f "$PROJECT_ROOT/docker/docker-compose.prod.yml" logs
    exit 1
fi

# Wait for containers to be healthy
echo "⏳ Waiting for containers to be healthy..."
TIMEOUT=60
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    if docker-compose -f "$PROJECT_ROOT/docker/docker-compose.prod.yml" ps | grep -q "healthy"; then
        echo "✅ Containers are healthy!"
        break
    fi
    sleep 5
    ELAPSED=$((ELAPSED + 5))
    if [ $ELAPSED -eq $TIMEOUT ]; then
        echo "❌ Timeout waiting for containers to be healthy"
        echo "Container logs:"
        docker-compose -f "$PROJECT_ROOT/docker/docker-compose.prod.yml" logs
        exit 1
    fi
done

# Run database migrations
echo "🔄 Running database migrations..."
if ! docker-compose -f "$PROJECT_ROOT/docker/docker-compose.prod.yml" exec -T backend python src/manage.py migrate; then
    echo "❌ Failed to run migrations"
    exit 1
fi

echo "✅ Deployment completed successfully!" 