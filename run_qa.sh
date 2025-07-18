#!/bin/bash

PORT=8002
SHARED_VOLUME_NAME="shared_memory_volume_sivista_qa"
IMAGE_NAME=$(grep 'IMAGE_NAME=' create_docker_image.sh | cut -d '"' -f 2)
VERSION=$(grep 'VERSION=' version.conf | cut -d '"' -f 2)
docker volume inspect "$SHARED_VOLUME_NAME" > /dev/null 2>&1 || docker volume create "$SHARED_VOLUME_NAME"
docker run -d \
        -e ML_ENV=.env.qa \
        # -e SHARED_MEMORY=/app/shared_memory/ \
        --mount source=$SHARED_VOLUME_NAME,target=/app/shared_memory \
        -e THIRD_PARTY_GRPC=15.206.112.102:8003 \
        -p $PORT:50051 $IMAGE_NAME:$VERSION