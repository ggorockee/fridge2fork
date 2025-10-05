#!/bin/bash

# ============================================
# Docker Build Script
# Fridge2Fork Admin Web
# ============================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
IMAGE_NAME="fridge2fork-admin-web"
VERSION=${1:-"latest"}
REGISTRY=${DOCKER_REGISTRY:-""}

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Building Docker Image${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo "Image: ${IMAGE_NAME}:${VERSION}"
echo "Registry: ${REGISTRY:-"local"}"
echo ""

# Build the image
echo -e "${YELLOW}Building image...${NC}"
docker build -t ${IMAGE_NAME}:${VERSION} .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Build successful!${NC}"
else
    echo -e "${RED}✗ Build failed!${NC}"
    exit 1
fi

# Tag as latest if version is specified
if [ "$VERSION" != "latest" ]; then
    echo -e "${YELLOW}Tagging as latest...${NC}"
    docker tag ${IMAGE_NAME}:${VERSION} ${IMAGE_NAME}:latest
fi

# Push to registry if specified
if [ -n "$REGISTRY" ]; then
    echo -e "${YELLOW}Pushing to registry...${NC}"
    docker tag ${IMAGE_NAME}:${VERSION} ${REGISTRY}/${IMAGE_NAME}:${VERSION}
    docker push ${REGISTRY}/${IMAGE_NAME}:${VERSION}

    if [ "$VERSION" != "latest" ]; then
        docker tag ${IMAGE_NAME}:${VERSION} ${REGISTRY}/${IMAGE_NAME}:latest
        docker push ${REGISTRY}/${IMAGE_NAME}:latest
    fi

    echo -e "${GREEN}✓ Pushed to registry!${NC}"
fi

# Display image info
echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Image Information${NC}"
echo -e "${GREEN}======================================${NC}"
docker images ${IMAGE_NAME}:${VERSION}

echo ""
echo -e "${GREEN}Build complete!${NC}"
echo ""
echo "To run the container:"
echo "  docker run -d -p 3000:3000 --name fridge2fork-admin ${IMAGE_NAME}:${VERSION}"
echo ""
echo "Or use docker-compose:"
echo "  docker-compose up -d"