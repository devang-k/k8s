#!/bin/bash

VERSION="1.0.0.416"

IMAGE_NAME="siclarity/frontend"

# Build Docker image
docker build -t $IMAGE_NAME:$VERSION .