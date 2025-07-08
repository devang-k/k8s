#!/bin/bash

VERSION="1.0.0.370"

IMAGE_NAME="siclarity/sivista_backend"

# Build Docker image
docker build -t $IMAGE_NAME:$VERSION .

# Push Docker image to registry (if needed)
# docker push $IMAGE_NAME:$VERSION
