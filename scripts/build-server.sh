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
# Configuration and Initialization
# =============================================================================

# Script directory and project root detection
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Try to find project root by looking for key files/directories
# The script expects to be run from: <project-root>/scripts/build-server.sh
# Or we can detect the project root automatically
PROJECT_ROOT=""

# First, try to go up one level (assuming script is in scripts/ subdirectory)
if [ -d "${SCRIPT_DIR}/../backend" ] && [ -f "${SCRIPT_DIR}/../fastapi-dockerfile" ]; then
    PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
# Second, try current directory if script is at project root
elif [ -d "./backend" ] && [ -f "./fastapi-dockerfile" ]; then
    PROJECT_ROOT="$(pwd)"
# Third, check if we're already in scripts directory but need to go up
elif [ -f "${SCRIPT_DIR}/fastapi-dockerfile" ]; then
    PROJECT_ROOT="${SCRIPT_DIR}"
else
    # Last resort: search upward for project markers
    SEARCH_DIR="$(pwd)"
    while [ "$SEARCH_DIR" != "/" ]; do
        if [ -f "$SEARCH_DIR/fastapi-dockerfile" ] && [ -d "$SEARCH_DIR/backend" ]; then
            PROJECT_ROOT="$SEARCH_DIR"
            break
        fi
        SEARCH_DIR="$(dirname "$SEARCH_DIR")"
    done
fi

# If still not found, error out
if [ -z "$PROJECT_ROOT" ]; then
    echo "ERROR: Cannot find project root directory!"
    echo "Please run this script from the project root or from the scripts/ directory."
    echo "Expected to find: fastapi-dockerfile and backend/ directory"
    exit 1
fi

# Change to project root
cd "$PROJECT_ROOT"

# Configuration variables
IMAGE_NAME="hata-server"
IMAGE_TAG="latest"
DOCKERFILE_PATH="${PROJECT_ROOT}/fastapi-dockerfile"
OUTPUT_TAR_FILE="${PROJECT_ROOT}/hata-server-latest.tar"
BUILD_CONTEXT="${PROJECT_ROOT}"

# Parse command line arguments
CLEAN=false
NO_COLOR=false

for arg in "$@"; do
    case $arg in
        --clean)
            CLEAN=true
            shift
            ;;
        --no-color)
            NO_COLOR=true
            shift
            ;;
        -h|--help|help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "OPTIONS:"
            echo "  --clean      Clean old images and files before building"
            echo "  --no-color   Disable colored output"
            echo "  -h, --help   Show this help message"
            echo ""
            echo "EXAMPLES:"
            echo "  $0                    # Basic build"
            echo "  $0 --clean            # Build with cleanup"
            echo "  $0 --no-color         # Build without colored output"
            exit 0
            ;;
        *)
            # Unknown option
            ;;
    esac
done

# Color configuration
if [ "$NO_COLOR" = true ]; then
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    CYAN=''
    WHITE=''
    RESET=''
else
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    BLUE='\033[0;34m'
    CYAN='\033[0;36m'
    WHITE='\033[0;37m'
    RESET='\033[0m'
fi

# =============================================================================
# Utility Functions
# =============================================================================

write_step() {
    echo ""
    echo -e "${BLUE}==== $1 ====${RESET}"
    echo ""
}

write_info() {
    echo -e "${BLUE}[INFO]${RESET} $1"
}

write_success() {
    echo -e "${GREEN}[SUCCESS]${RESET} $1"
}

write_warn() {
    echo -e "${YELLOW}[WARN]${RESET} $1"
}

write_error() {
    echo -e "${RED}[ERROR]${RESET} $1"
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

format_file_size() {
    local size=$1
    local units=("B" "KB" "MB" "GB" "TB")
    local unit_index=0
    local size_float=$(echo "$size" | awk '{printf "%.2f", $1}')

    while (( $(echo "$size_float >= 1024" | bc -l) )) && [ $unit_index -lt ${#units[@]}-1 ]; do
        size_float=$(echo "scale=2; $size_float / 1024" | bc)
        unit_index=$((unit_index + 1))
    done

    printf "%.2f %s" "$size_float" "${units[$unit_index]}"
}

# =============================================================================
# Main Functions
# =============================================================================

test_docker_environment() {
    write_step "Checking Docker Environment"

    # Show detected project root
    write_info "Project root: $PROJECT_ROOT"
    write_info "Script location: $SCRIPT_DIR"

    # Check if Docker command is available
    if ! command_exists docker; then
        write_error "Docker is not installed or not in PATH"
        write_info "Please install Docker Engine: https://docs.docker.com/engine/install/"
        exit 1
    fi

    # Display Docker version info
    local docker_version=$(docker --version 2>&1)
    if [ $? -eq 0 ]; then
        write_success "Docker environment check passed"
        write_info "Docker version: $docker_version"
    else
        write_error "Cannot get Docker version"
        exit 1
    fi
}

remove_old_artifacts() {
    write_step "Cleaning Old Files"

    local full_image_name="${IMAGE_NAME}:${IMAGE_TAG}"

    # Clean old images
    local image_id=$(docker images -q "$full_image_name" 2>/dev/null)
    if [ -n "$image_id" ]; then
        write_warn "Found old image $full_image_name, deleting..."
        docker rmi "$full_image_name" 2>/dev/null
        if [ $? -eq 0 ]; then
            write_success "Old image deleted successfully"
        else
            write_warn "Warning: Cannot delete old image, may be in use"
        fi
    fi

    # Clean old tar file
    if [ -f "$OUTPUT_TAR_FILE" ]; then
        write_warn "Found old tar file $OUTPUT_TAR_FILE, deleting..."
        rm -f "$OUTPUT_TAR_FILE"
        if [ $? -eq 0 ]; then
            write_success "Old tar file deleted successfully"
        else
            write_warn "Cannot delete old tar file"
        fi
    fi

    # Clean dangling images (optional)
    if [ "$CLEAN" = true ]; then
        write_info "Cleaning dangling images..."
        docker image prune -f >/dev/null 2>&1
        if [ $? -eq 0 ]; then
            write_success "Dangling images cleanup completed"
        else
            write_warn "Warning while cleaning dangling images"
        fi
    fi
}

build_docker_image() {
    write_step "Building Docker Image"

    local full_image_name="${IMAGE_NAME}:${IMAGE_TAG}"

    write_info "Image name: $full_image_name"
    write_info "Dockerfile path: $DOCKERFILE_PATH"
    write_info "Build context: $BUILD_CONTEXT"

    # Check if Dockerfile exists
    if [ ! -f "$DOCKERFILE_PATH" ]; then
        write_error "Dockerfile not found: $DOCKERFILE_PATH"
        write_info "Current directory: $(pwd)"
        write_info "Project root: $PROJECT_ROOT"
        write_info "Please check the file structure:"
        write_info "  - fastapi-dockerfile should be at: $PROJECT_ROOT/fastapi-dockerfile"
        write_info "  - backend/ directory should be at: $PROJECT_ROOT/backend/"
        exit 1
    fi

    # Check if backend directory exists
    if [ ! -d "${PROJECT_ROOT}/backend" ]; then
        write_error "Backend directory not found: ${PROJECT_ROOT}/backend"
        write_info "The Dockerfile expects a backend/ directory with:"
        write_info "  - backend/requirements.txt"
        write_info "  - backend/requirements-pg.txt"
        write_info "  - backend/ (application code)"
        exit 1
    fi

    write_info "Starting image build..."

    docker build \
        -f "$DOCKERFILE_PATH" \
        -t "$full_image_name" \
        "$BUILD_CONTEXT"

    if [ $? -eq 0 ]; then
        write_success "Image built successfully!"

        # Display image info
        write_info "Image info:"
        docker images "$full_image_name"
    else
        write_error "Image build failed!"
        exit 1
    fi
}

export_docker_image() {
    write_step "Exporting Image to tar File"

    local full_image_name="${IMAGE_NAME}:${IMAGE_TAG}"

    write_info "Exporting image: $full_image_name"
    write_info "Output file: $OUTPUT_TAR_FILE"

    docker save -o "$OUTPUT_TAR_FILE" "$full_image_name"

    if [ $? -eq 0 ] && [ -f "$OUTPUT_TAR_FILE" ]; then
        local file_size=$(stat -f%z "$OUTPUT_TAR_FILE" 2>/dev/null || stat -c%s "$OUTPUT_TAR_FILE" 2>/dev/null || echo "0")
        local formatted_size=$(format_file_size "$file_size")
        write_success "Image exported successfully!"
        write_info "File name: $OUTPUT_TAR_FILE"
        write_info "File size: $formatted_size"
    else
        write_error "Image export failed!"
        exit 1
    fi
}

test_tar_file() {
    write_step "Verifying tar File"

    if [ ! -f "$OUTPUT_TAR_FILE" ]; then
        write_error "tar file not found: $OUTPUT_TAR_FILE"
        exit 1
    fi

    write_info "Verifying file integrity..."

    # Check if valid tar file
    if command_exists tar; then
        tar -tf "$OUTPUT_TAR_FILE" >/dev/null 2>&1
        if [ $? -eq 0 ]; then
            write_success "tar file verification passed!"
        else
            write_error "Invalid tar file format!"
            exit 1
        fi
    else
        write_warn "tar command not available, skipping file format verification"
    fi

    # Display file info
    local file_size=$(stat -f%z "$OUTPUT_TAR_FILE" 2>/dev/null || stat -c%s "$OUTPUT_TAR_FILE" 2>/dev/null || echo "0")
    local formatted_size=$(format_file_size "$file_size")
    local file_path=$(realpath "$OUTPUT_TAR_FILE" 2>/dev/null || echo "$OUTPUT_TAR_FILE")

    write_info "File path: $file_path"
    write_info "File size: $formatted_size"
}

show_build_info() {
    write_step "Build Completed"

    local full_image_name="${IMAGE_NAME}:${IMAGE_TAG}"

    echo -e "${GREEN}Image name:${RESET} $full_image_name"
    echo -e "${GREEN}Output file:${RESET} $OUTPUT_TAR_FILE"

    if [ -f "$OUTPUT_TAR_FILE" ]; then
        local file_path=$(realpath "$OUTPUT_TAR_FILE" 2>/dev/null || echo "$OUTPUT_TAR_FILE")
        echo -e "${GREEN}File path:${RESET} $file_path"
    fi

    echo ""
    echo -e "${CYAN}Usage:${RESET}"
    echo -e "${WHITE}1. Load image:${RESET} docker load -i $OUTPUT_TAR_FILE"
    echo -e "${WHITE}2. Run container:${RESET} docker run -d -p 9099:9099 --name hata-server $full_image_name"
    echo ""
}

cleanup_on_failure() {
    write_warn "Build failed, cleaning up..."

    local full_image_name="${IMAGE_NAME}:${IMAGE_TAG}"

    # Clean image
    docker rmi "$full_image_name" 2>/dev/null || true

    # Clean tar file
    rm -f "$OUTPUT_TAR_FILE" 2>/dev/null || true
}

# =============================================================================
# Main Function
# =============================================================================

start_build_process() {
    echo -e "${GREEN}==== hata Server Build Script (Bash) ====${RESET}"
    echo -e "${BLUE}Start time:${RESET} $(date '+%Y-%m-%d %H:%M:%S')"

    # Execute build process with error handling
    {
        test_docker_environment
        remove_old_artifacts
        build_docker_image
        export_docker_image
        test_tar_file
        show_build_info

        echo -e "\n${GREEN}Build completed! End time:${RESET} $(date '+%Y-%m-%d %H:%M:%S')"
    } || {
        cleanup_on_failure
        exit 1
    }
}

# =============================================================================
# Script Entry Point
# =============================================================================

# Check Bash version
if [ ${BASH_VERSINFO[0]} -lt 4 ]; then
    write_error "Bash 4.0 or higher is required"
    write_info "Current version: $BASH_VERSION"
    exit 1
fi

# Start build process
start_build_process
