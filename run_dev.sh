#!/bin/bash

PORT=3002
SHARED_VOLUME_NAME="shared_memory_volume_sivista_dev" 
IMAGE_NAME=$(grep 'IMAGE_NAME=' create_docker_image.sh | cut -d '"' -f 2)
VERSION=$(grep 'VERSION=' version.conf | cut -d '"' -f 2)
docker volume inspect "$SHARED_VOLUME_NAME" > /dev/null 2>&1 || docker volume create "$SHARED_VOLUME_NAME"
docker run -d \
        -e ML_ENV=.env.dev \
        # -e SHARED_MEMORY=/app/shared_memory/ \
        --mount source=$SHARED_VOLUME_NAME,target=/app/shared_memory \
        -e THIRD_PARTY_GRPC=13.126.133.62:3003 \
        -p $PORT:50051 $IMAGE_NAME:$VERSION
