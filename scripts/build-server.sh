#!/bin/bash
#
# hata Server Docker Image Build Script (Bash)
#
# Usage: ./build-server.sh
#

set -e

# Configuration
IMAGE_NAME="hata-server"
IMAGE_TAG="latest"
DOCKERFILE="./fastapi-dockerfile"
IMAGES_DIR="./images"
OUTPUT_TAR="$IMAGES_DIR/hata-server-latest.tar"

# Ensure images directory exists
if [ ! -d "$IMAGES_DIR" ]; then
    mkdir -p "$IMAGES_DIR"
    echo -e "\033[36mCreated directory: $IMAGES_DIR\033[0m"
fi

# Handle existing image file
if [ -f "$OUTPUT_TAR" ]; then
    BACKUP_PATH="${OUTPUT_TAR}.backup"
    echo -e "\033[33mFound existing image: $OUTPUT_TAR\033[0m"
    echo -e "\033[33mBacking up to: $BACKUP_PATH\033[0m"

    if mv "$OUTPUT_TAR" "$BACKUP_PATH" 2>/dev/null; then
        echo -e "\033[32mBackup created\033[0m"
    else
        echo -e "\033[31mBackup failed, removing old file...\033[0m"
        rm -f "$OUTPUT_TAR"
    fi
fi

# Check Docker
if ! command -v docker >/dev/null 2>&1; then
    echo -e "\033[31mDocker not found\033[0m"
    exit 1
fi
echo -e "\033[32mDocker: $(docker --version)\033[0m"

# Build image
echo ""
echo -e "\033[36mBuilding Docker image...\033[0m"
docker build -f "$DOCKERFILE" -t "${IMAGE_NAME}:${IMAGE_TAG}" .

if [ $? -ne 0 ]; then
    echo -e "\033[31mBuild failed\033[0m"
    exit 1
fi

# Save image
echo ""
echo -e "\033[36mSaving image to $OUTPUT_TAR...\033[0m"
docker save -o "$OUTPUT_TAR" "${IMAGE_NAME}:${IMAGE_TAG}"

if [ $? -eq 0 ] && [ -f "$OUTPUT_TAR" ]; then
    # Get file size in MB
    if stat -c%s "$OUTPUT_TAR" >/dev/null 2>&1; then
        size_mb=$(echo "($(stat -c%s "$OUTPUT_TAR") / 1048576)" | awk '{printf "%.2f", $1}')
    elif stat -f%z "$OUTPUT_TAR" >/dev/null 2>&1; then
        size_mb=$(echo "($(stat -f%z "$OUTPUT_TAR") / 1048576)" | awk '{printf "%.2f", $1}')
    else
        size_mb=$(wc -c < "$OUTPUT_TAR" | awk '{printf "%.2f", $1/1048576}')
    fi

    echo ""
    echo -e "\033[32m==== Build Completed ====\033[0m"
    echo -e "\033[37mImage: ${IMAGE_NAME}:${IMAGE_TAG}\033[0m"
    echo -e "\033[37mFile:  $OUTPUT_TAR\033[0m"
    echo -e "\033[37mSize:  ${size_mb} MB\033[0m"
else
    echo -e "\033[31mSave failed\033[0m"
    exit 1
fi
