#!/bin/bash

# =============================================================================
# hata Frontend Build Script (Bash)
#
# DESCRIPTION
#   Build frontend Vue3 application and copy to nginx directory
#   Output: html/dist/
#
# USAGE
#   ./build-frontend.sh            # Basic build
#   ./build-frontend.sh --clean    # Build with cleanup
#   ./build-frontend.sh --no-color # Build without colored output
#   ./build-frontend.sh -h         # Show help
#
# REQUIREMENTS
#   Node.js 18+ and pnpm installed
#   Bash 4.0+
# =============================================================================

set -e  # Exit on error

# =============================================================================
# Configuration
# =============================================================================

FRONTEND_DIR="frontend"
OUTPUT_DIR="html/dist"
BUILD_ENV="production"

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
            echo "  --clean      Clean node_modules and build output before building"
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

echo -e "${GREEN}==== hata Frontend Build Script ====${RESET}"
echo -e "${BLUE}Start time:${RESET} $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Step 1: Check Node.js and pnpm
echo -e "${BLUE}==== Checking Environment ====${RESET}"

if ! command -v node >/dev/null 2>&1; then
    echo -e "${RED}[ERROR] Node.js not found${RESET}"
    echo -e "${YELLOW}Please install Node.js 18+: https://nodejs.org/${RESET}"
    exit 1
fi

NODE_VERSION=$(node -v)
echo -e "${GREEN}[SUCCESS]${RESET} Node.js: $NODE_VERSION"

if ! command -v pnpm >/dev/null 2>&1; then
    echo -e "${RED}[ERROR] pnpm not found${RESET}"
    echo -e "${YELLOW}Installing pnpm globally...${RESET}"
    npm install -g pnpm
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR] Failed to install pnpm${RESET}"
        exit 1
    fi
fi

PNPM_VERSION=$(pnpm -v)
echo -e "${GREEN}[SUCCESS]${RESET} pnpm: $PNPM_VERSION"
echo ""

# Step 2: Check frontend directory
echo -e "${BLUE}==== Checking Frontend Directory ====${RESET}"
if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}[ERROR] Frontend directory not found: $FRONTEND_DIR${RESET}"
    echo -e "${YELLOW}Current directory: $(pwd)${RESET}"
    exit 1
fi

if [ ! -f "$FRONTEND_DIR/package.json" ]; then
    echo -e "${RED}[ERROR] package.json not found in $FRONTEND_DIR${RESET}"
    exit 1
fi
echo -e "${GREEN}[SUCCESS] Frontend directory found${RESET}"
echo ""

# Step 3: Clean old files
if [ "$CLEAN" = true ]; then
    echo -e "${BLUE}==== Cleaning Old Files ====${RESET}"

    # Clean node_modules
    if [ -d "$FRONTEND_DIR/node_modules" ]; then
        echo -e "${YELLOW}[WARN] Removing node_modules${RESET}"
        rm -rf "$FRONTEND_DIR/node_modules"
    fi

    # Clean build output
    if [ -d "$FRONTEND_DIR/dist" ]; then
        echo -e "${YELLOW}[WARN] Removing frontend/dist${RESET}"
        rm -rf "$FRONTEND_DIR/dist"
    fi

    # Clean final output
    if [ -d "$OUTPUT_DIR" ]; then
        echo -e "${YELLOW}[WARN] Removing $OUTPUT_DIR${RESET}"
        rm -rf "$OUTPUT_DIR"
    fi

    # Clean pnpm lock
    if [ -f "$FRONTEND_DIR/pnpm-lock.yaml" ]; then
        echo -e "${YELLOW}[WARN] Removing pnpm-lock.yaml${RESET}"
        rm -f "$FRONTEND_DIR/pnpm-lock.yaml"
    fi

    echo ""
fi

# Step 4: Install dependencies
echo -e "${BLUE}==== Installing Dependencies ====${RESET}"
cd "$FRONTEND_DIR"

if [ ! -d "node_modules" ] || [ "$CLEAN" = true ]; then
    echo "Installing pnpm dependencies..."
    pnpm install
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[SUCCESS] Dependencies installed${RESET}"
    else
        echo -e "${RED}[ERROR] Failed to install dependencies${RESET}"
        exit 1
    fi
else
    echo -e "${GREEN}[SUCCESS] Dependencies already installed${RESET}"
fi
echo ""

# Step 5: Build frontend
echo -e "${BLUE}==== Building Frontend ====${RESET}"
echo "Environment: $BUILD_ENV"
echo ""

pnpm build

if [ $? -eq 0 ]; then
    echo -e "${GREEN}[SUCCESS] Frontend built${RESET}"
else
    echo -e "${RED}[ERROR] Build failed${RESET}"
    exit 1
fi
echo ""

# Step 6: Copy to output directory
echo -e "${BLUE}==== Copying to Output Directory ====${RESET}"

cd ..

# Create output directory
mkdir -p "$(dirname "$OUTPUT_DIR")"

# Remove old output
if [ -d "$OUTPUT_DIR" ]; then
    rm -rf "$OUTPUT_DIR"
fi

# Copy build output
cp -r "$FRONTEND_DIR/dist" "$OUTPUT_DIR"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}[SUCCESS] Files copied to $OUTPUT_DIR${RESET}"

    # Show output size
    if command -v du >/dev/null 2>&1; then
        OUTPUT_SIZE=$(du -sh "$OUTPUT_DIR" 2>/dev/null | cut -f1)
        echo "Output size: $OUTPUT_SIZE"
    fi
else
    echo -e "${RED}[ERROR] Failed to copy files${RESET}"
    exit 1
fi
echo ""

# Step 7: Done
echo -e "${GREEN}==== Build Completed ====${RESET}"
echo -e "${CYAN}Output directory:${RESET} $OUTPUT_DIR"
echo -e "${CYAN}Environment:${RESET} $BUILD_ENV"
echo ""
echo -e "${CYAN}Next steps:${RESET}"
echo "  1. Review the built files in: $OUTPUT_DIR"
echo "  2. Deploy with: docker-compose up -d"
echo ""
echo -e "${BLUE}End time:${RESET} $(date '+%Y-%m-%d %H:%M:%S')"
