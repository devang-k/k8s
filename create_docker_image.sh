#!/bin/bash


VERSION=$(grep -E '^VERSION=' "version.conf" | sed -E 's/VERSION="([^"]+)"/\1/')


IMAGE_NAME="siclarity/ml_service"
 
# Build Docker image
docker build -t $IMAGE_NAME:$VERSION .
 
# Push Docker image to registry (if needed)
# docker push $IMAGE_NAME:$VERSION

