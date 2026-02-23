#!/bin/bash

# =============================================================================
# hata Server Docker Image Build Script (Bash)
#
# DESCRIPTION
#   Build Docker image and export as tar file
#   Output: hata-server-latest.tar
#   Image name: hata-server:latest
#
# USAGE
#   ./build-server.sh              # Basic build
#   ./build-server.sh --clean      # Build with cleanup
#   ./build-server.sh --no-color   # Build without colored output
#   ./build-server.sh -h           # Show help
#
# REQUIREMENTS
#   Docker Engine installed
#   Bash 4.0+
# =============================================================================

set -e  # Exit on error

# =============================================================================
# Configuration
# =============================================================================

IMAGE_NAME="hata-server"
IMAGE_TAG="latest"
DOCKERFILE="fastapi-dockerfile"
OUTPUT_FILE="hata-server-latest.tar"

# Parse command line arguments
CLEAN=false
NO_COLOR=false

for arg in "$@"; do
    case $arg in
        --clean) CLEAN=true ;;
        --no-color) NO_COLOR=true ;;
        -h|--help|help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "OPTIONS:"
            echo "  --clean      Clean old images and files before building"
            echo "  --no-color   Disable colored output"
            echo "  -h, --help   Show this help message"
            exit 0
            ;;
    esac
done

# Color setup
if [ "$NO_COLOR" = true ]; then
    RED='' GREEN='' YELLOW='' BLUE='' CYAN='' RESET=''
else
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    BLUE='\033[0;34m'
    CYAN='\033[0;36m'
    RESET='\033[0m'
fi

# =============================================================================
# Main Build Process
# =============================================================================

echo -e "${GREEN}==== hata Server Build Script ====${RESET}"
echo -e "${BLUE}Start time:${RESET} $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Step 1: Check Docker
echo -e "${BLUE}==== Checking Docker ====${RESET}"
if ! command -v docker >/dev/null 2>&1; then
    echo -e "${RED}[ERROR] Docker not found${RESET}"
    exit 1
fi
echo -e "${GREEN}[SUCCESS]${RESET} Docker: $(docker --version)"
echo ""

# Step 2: Clean old files
if [ "$CLEAN" = true ] || [ -f "$OUTPUT_FILE" ] || docker images -q "${IMAGE_NAME}:${IMAGE_TAG}" >/dev/null 2>&1; then
    echo -e "${BLUE}==== Cleaning Old Files ====${RESET}"

    # Remove old image
    if docker images -q "${IMAGE_NAME}:${IMAGE_TAG}" >/dev/null 2>&1; then
        echo -e "${YELLOW}[WARN] Removing old image${RESET}"
        docker rmi "${IMAGE_NAME}:${IMAGE_TAG}" 2>/dev/null || true
    fi

    # Remove old tar file
    if [ -f "$OUTPUT_FILE" ]; then
        echo -e "${YELLOW}[WARN] Removing old tar file${RESET}"
        rm -f "$OUTPUT_FILE"
    fi

    # Clean dangling images
    if [ "$CLEAN" = true ]; then
        docker image prune -f >/dev/null 2>&1 || true
    fi

    echo ""
fi

# Step 3: Check files
echo -e "${BLUE}==== Checking Files ====${RESET}"
if [ ! -f "$DOCKERFILE" ]; then
    echo -e "${RED}[ERROR] Dockerfile not found: $DOCKERFILE${RESET}"
    echo -e "${YELLOW}Current directory: $(pwd)${RESET}"
    exit 1
fi

if [ ! -d "backend" ]; then
    echo -e "${RED}[ERROR] Backend directory not found${RESET}"
    echo -e "${YELLOW}Expected structure: ./backend/ ${RESET}"
    exit 1
fi
echo -e "${GREEN}[SUCCESS] All files found${RESET}"
echo ""

# Step 4: Build image
echo -e "${BLUE}==== Building Image ====${RESET}"
echo "Image: ${IMAGE_NAME}:${IMAGE_TAG}"
echo "Dockerfile: $DOCKERFILE"
echo ""

docker build -f "$DOCKERFILE" -t "${IMAGE_NAME}:${IMAGE_TAG}" .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}[SUCCESS] Image built${RESET}"
else
    echo -e "${RED}[ERROR] Build failed${RESET}"
    exit 1
fi
echo ""

# Step 5: Export image
echo -e "${BLUE}==== Exporting Image ====${RESET}"
docker save -o "$OUTPUT_FILE" "${IMAGE_NAME}:${IMAGE_TAG}"

if [ $? -eq 0 ] && [ -f "$OUTPUT_FILE" ]; then
    # Get file size and format (using awk instead of bc)
    if stat -c%s "$OUTPUT_FILE" >/dev/null 2>&1; then
        size_bytes=$(stat -c%s "$OUTPUT_FILE")
    elif stat -f%z "$OUTPUT_FILE" >/dev/null 2>&1; then
        size_bytes=$(stat -f%z "$OUTPUT_FILE")
    else
        size_bytes=$(wc -c < "$OUTPUT_FILE")
    fi

    # Format size using awk (no bc needed)
    size_str=$(echo "$size_bytes" | awk '{
        if ($1 >= 1073741824) printf "%.2f GB", $1/1073741824
        else if ($1 >= 1048576) printf "%.2f MB", $1/1048576
        else if ($1 >= 1024) printf "%.2f KB", $1/1024
        else printf "%d B", $1
    }')

    echo -e "${GREEN}[SUCCESS] Image exported${RESET}"
    echo "File: $OUTPUT_FILE"
    echo "Size: $size_str"
else
    echo -e "${RED}[ERROR] Export failed${RESET}"
    exit 1
fi
echo ""

# Step 6: Done
echo -e "${GREEN}==== Build Completed ====${RESET}"
echo -e "${CYAN}Image:${RESET} ${IMAGE_NAME}:${IMAGE_TAG}"
echo -e "${CYAN}File:${RESET} $OUTPUT_FILE"
echo ""
echo -e "${CYAN}Usage:${RESET}"
echo "  Load:  docker load -i $OUTPUT_FILE"
echo "  Run:   docker run -d -p 9099:9099 --name hata-server ${IMAGE_NAME}:${IMAGE_TAG}"
echo ""
echo -e "${BLUE}End time:${RESET} $(date '+%Y-%m-%d %H:%M:%S')"
