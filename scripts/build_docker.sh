#!/bin/bash
# Docker build script for OpenChat

set -e

echo "Building Docker image for OpenChat"
echo "==================================="

# Get version from openchat/__init__.py
VERSION=$(grep "__version__" openchat/__init__.py | grep -oP '"\K[^"]+')
IMAGE_NAME="openchat"
IMAGE_TAG="${IMAGE_NAME}:${VERSION}"
IMAGE_LATEST="${IMAGE_NAME}:latest"

echo "Version: $VERSION"
echo "Image: $IMAGE_TAG"

# Build the image
echo ""
echo "Building Docker image..."
docker build -t "$IMAGE_TAG" -t "$IMAGE_LATEST" .

echo ""
echo "Build complete!"
echo "Image tags:"
echo "  - $IMAGE_TAG"
echo "  - $IMAGE_LATEST"

# Optional: Run the image to test
if [ "$1" == "--test" ]; then
    echo ""
    echo "Testing Docker image..."
    docker run --rm "$IMAGE_LATEST" python -c "from openchat import __version__; print(f'OpenChat v{__version__}')"
fi
