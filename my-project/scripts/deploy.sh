#!/bin/bash

set -e  # Exit on error

# Load config from config.json using jq (make sure jq is installed)
CONFIG_FILE="config.json"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: $CONFIG_FILE not found!"
    exit 1
fi

# Extract values using jq
GITHUB_ACCESS_TOKEN=$(jq -r '.GITHUB_ACCESS_TOKEN' "$CONFIG_FILE")
GITHUB_REPO=$(jq -r '.GITHUB_REPOSITORY' "$CONFIG_FILE")
GITHUB_AGENT_NAME="my-k8s-runner"
ABSPATH_TO_PROJECT=$(jq -r '.ABSPATH_TO_PROJECT' "$CONFIG_FILE")

# Basic validation
if [ -z "$GITHUB_ACCESS_TOKEN" ] || [ -z "$GITHUB_REPO" ] || [ -z "$ABSPATH_TO_PROJECT" ]; then
    echo "Error: Missing required config values in $CONFIG_FILE"
    exit 1
fi

# Build the Docker image
docker build -t "ghcr.io/$GITHUB_REPO:latest" ./app

# Push the Docker image
echo "$GITHUB_ACCESS_TOKEN" | docker login ghcr.io -u "$GITHUB_AGENT_NAME" --password-stdin
docker push "ghcr.io/$GITHUB_REPO:latest"

# Update the Kubernetes deployment
kubectl apply -f app-deployment.yaml
kubectl apply -f app-service.yaml

echo "✅ Deployment updated successfully!"
