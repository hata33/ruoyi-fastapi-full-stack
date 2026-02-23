#!/bin/bash

# =============================================================================
# hata Full Stack Build Script (Bash)
#
# DESCRIPTION
#   Build both frontend and backend for production deployment
#
# USAGE
#   ./build-all.sh                # Build both frontend and backend
#   ./build-all.sh --clean        # Build with cleanup
#   ./build-all.sh --no-color     # Build without colored output
#   ./build-all.sh -h             # Show help
#
# REQUIREMENTS
#   Node.js 18+, pnpm, and Docker
#   Bash 4.0+
# =============================================================================

set -e  # Exit on error

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

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
            echo "  --clean      Clean old files before building"
            echo "  --no-color   Disable colored output"
            echo "  -h, --help   Show this help message"
            exit 0
            ;;
    esac
done

# Color setup
if [ "$NO_COLOR" = true ]; then
    GREEN='' BLUE='' RESET=''
else
    GREEN='\033[0;32m'
    BLUE='\033[0;34m'
    RESET='\033[0m'
fi

# =============================================================================
# Main Build Process
# =============================================================================

echo -e "${GREEN}==== hata Full Stack Build Script ====${RESET}"
echo -e "${BLUE}Start time:${RESET} $(date '+%Y-%m-%d %H:%M:%S')"
echo -e "${BLUE}Project root:${RESET} $PROJECT_ROOT"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Build arguments
BUILD_ARGS=""
if [ "$CLEAN" = true ]; then
    BUILD_ARGS="$BUILD_ARGS --clean"
fi
if [ "$NO_COLOR" = true ]; then
    BUILD_ARGS="$BUILD_ARGS --no-color"
fi

# Step 1: Build Frontend
echo -e "${GREEN}========================================${RESET}"
echo -e "${GREEN}Building Frontend${RESET}"
echo -e "${GREEN}========================================${RESET}"
echo ""

./scripts/build-frontend.sh $BUILD_ARGS

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Frontend build failed${RESET}"
    exit 1
fi

echo ""
echo ""

# Step 2: Build Backend
echo -e "${GREEN}========================================${RESET}"
echo -e "${GREEN}Building Backend${RESET}"
echo -e "${GREEN}========================================${RESET}"
echo ""

./scripts/build-server.sh $BUILD_ARGS

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Backend build failed${RESET}"
    exit 1
fi

echo ""
echo ""

# Step 3: Summary
echo -e "${GREEN}========================================${RESET}"
echo -e "${GREEN}Build Summary${RESET}"
echo -e "${GREEN}========================================${RESET}"
echo ""
echo -e "${GREEN}✓ Frontend:${RESET} Built and copied to html/dist/"
echo -e "${GREEN}✓ Backend:${RESET} Docker image exported to hata-server-latest.tar"
echo ""
echo -e "${BLUE}Next steps:${RESET}"
echo "  1. Load backend image: docker load -i hata-server-latest.tar"
echo "  2. Start services: docker-compose up -d"
echo ""
echo -e "${BLUE}End time:${RESET} $(date '+%Y-%m-%d %H:%M:%S')"
