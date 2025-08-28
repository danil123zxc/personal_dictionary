#!/bin/bash

# Personal Dictionary API Test Runner
# Usage: ./run_tests.sh [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
CONTAINER_NAME="server"
TEST_COMMAND="pytest"
COVERAGE=false
VERBOSE=false
SPECIFIC_TEST=""

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -c, --container NAME    Docker container name (default: server)"
    echo "  -t, --test PATTERN      Run specific test pattern"
    echo "  -m, --marker MARKER     Run tests with specific marker"
    echo "  -v, --verbose           Verbose output"
    echo "  --coverage              Run with coverage report"
    echo "  --html                  Generate HTML coverage report"
    echo "  --help                  Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Run all tests"
    echo "  $0 --coverage                         # Run with coverage"
    echo "  $0 -t test_register_user             # Run specific test"
    echo "  $0 -m crud                           # Run CRUD tests only"
    echo "  $0 -v --coverage                     # Verbose with coverage"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--container)
            CONTAINER_NAME="$2"
            shift 2
            ;;
        -t|--test)
            SPECIFIC_TEST="$2"
            shift 2
            ;;
        -m|--marker)
            TEST_COMMAND="pytest -m $2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            TEST_COMMAND="pytest -v"
            shift
            ;;
        --coverage)
            COVERAGE=true
            TEST_COMMAND="pytest --cov=src --cov-report=term-missing"
            shift
            ;;
        --html)
            COVERAGE=true
            TEST_COMMAND="pytest --cov=src --cov-report=html --cov-report=term-missing"
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Check if container exists
if ! docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
    print_error "Container '$CONTAINER_NAME' is not running!"
    echo "Available containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}"
    exit 1
fi

# Build test command
if [ -n "$SPECIFIC_TEST" ]; then
    TEST_COMMAND="pytest -v -k '$SPECIFIC_TEST'"
fi

if [ "$COVERAGE" = true ] && [ -n "$SPECIFIC_TEST" ]; then
    TEST_COMMAND="pytest --cov=app --cov-report=term-missing -k '$SPECIFIC_TEST'"
fi

# Run tests
print_status "Running tests in container: $CONTAINER_NAME"
print_status "Command: $TEST_COMMAND"

# Execute tests
if docker exec "$CONTAINER_NAME" $TEST_COMMAND; then
    print_success "Tests completed successfully!"
    
    if [ "$COVERAGE" = true ]; then
        print_status "Coverage report generated"
        print_status "To view HTML coverage report, run:"
        echo "  docker exec $CONTAINER_NAME python -m http.server 8001 -d htmlcov"
        echo "  Then open http://localhost:8001 in your browser"
    fi
else
    print_error "Tests failed!"
    exit 1
fi
