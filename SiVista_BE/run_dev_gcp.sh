#!/bin/bash

# DJANGO_SETTINGS_MODULE=SiVista_BE.settings.dev
DJANGO_ENV=.env.dev
PORT=8001

IMAGE_NAME=$(grep 'IMAGE_NAME=' build.sh | cut -d '"' -f 2)
VERSION=$(grep 'VERSION=' build.sh | cut -d '"' -f 2)

# Read the JSON file and escape it for use in an environment variable
GOOGLE_APPLICATION_CREDENTIALS_DEV_JSON=$(jq -Rs . < kubernetes-test-456506-17362232516c.json)

docker run \
  -e DJANGO_ENV="$DJANGO_ENV" \
  -v "$(pwd)/kubernetes-test-456506-17362232516c.json:/app/kubernetes-test-456506-17362232516c.json" \
  -e GOOGLE_APPLICATION_CREDENTIALS_DEV="$GOOGLE_APPLICATION_CREDENTIALS_DEV_JSON" \
  -e GOOGLE_APPLICATION_CREDENTIALS="/app/kubernetes-test-456506-17362232516c.json" \
  -d -p $PORT:8000 "$IMAGE_NAME:$VERSION"