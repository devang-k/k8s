#!/bin/bash
 
VERSION=$(grep -E '^VERSION=' "version.conf" | sed -E 's/VERSION="([^"]+)"/\1/')
IMAGE_NAME="siclarity/ml_service"
 
# create executable file
# Note: first invoke virtual environment
# source ../../venv_core/bin/activate

# Directory for the virtual environment
VENV_DIR="../sivista_core_venv_temp"

# Check if the virtual environment directory exists
if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment found in '$VENV_DIR'. Activating..."
else
    echo "Virtual environment not found. Creating one in '$VENV_DIR'..."
    python3 -m venv "$VENV_DIR"
    if [ $? -eq 0 ]; then
        echo "Virtual environment created successfully."
    else
        echo "Failed to create virtual environment. Exiting."
        exit 1
    fi
fi

# Source the virtual environment
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
    echo "Virtual environment activated."
else
    echo "Failed to activate virtual environment. Ensure Python3 and venv module are installed."
    exit 1
fi

# installing dependencies
pip install -r requirements.txt

# creating executable package
pyinstaller grpc_server.spec

# Build Docker image
# Note: make sure u are using correct dockerfile (Dockefile.ex_pkg) in following command with -f param
docker build -t $IMAGE_NAME:$VERSION -f Dockerfile.ex_pkg .

# Push Docker image to registry (if needed)
# docker push $IMAGE_NAME:$VERSION
