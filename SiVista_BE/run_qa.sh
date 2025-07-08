#!/bin/bash

# DJANGO_SETTINGS_MODULE=SiVista_BE.settings.qa
DJANGO_ENV=.env.qa
PORT=8001

IMAGE_NAME=$(grep 'IMAGE_NAME=' build.sh | cut -d '"' -f 2)
VERSION=$(grep 'VERSION=' build.sh | cut -d '"' -f 2)

# docker run -e DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE -e DJANGO_ENV=$DJANGO_ENV -d -p $PORT:8000 $IMAGE_NAME:$VERSION
docker run -e DJANGO_ENV=$DJANGO_ENV \
-v '/home/ubuntu/sivista_be_data_dev':'/sivista_be_data' \
-d -p $PORT:8000 $IMAGE_NAME:$VERSION