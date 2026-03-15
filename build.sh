#!/bin/sh
# Build and push multi-arch image to container registry
# Usage: ./build.sh [tag]

set -e

REGISTRY="your-registry.example.com"
PROJECT="your-project"
IMAGE="huawei-sms-pushover"
TAG="${1:-latest}"
FULL_IMAGE="$REGISTRY/$PROJECT/$IMAGE:$TAG"

echo "Building multi-arch image: $FULL_IMAGE"

# Preflight checks
if ! docker info >/dev/null 2>&1; then
    echo "ERROR: Docker daemon not running or not accessible"
    exit 1
fi
if ! docker buildx version >/dev/null 2>&1; then
    echo "ERROR: docker buildx not available — install Docker BuildKit"
    exit 1
fi
echo "NOTE: Ensure you are logged in: docker login $REGISTRY"
echo ""

# Ensure buildx builder exists
docker buildx inspect multiarch >/dev/null 2>&1 || \
    docker buildx create --name multiarch --use

docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t "$FULL_IMAGE" \
    --push .

echo ""
echo "Pushed: $FULL_IMAGE"
echo "Pull:   docker pull $FULL_IMAGE"
