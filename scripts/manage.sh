#!/bin/bash

# Personal Dictionary API - Docker & Requirements Management Script
# This script provides comprehensive management of Docker containers and requirements

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

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

print_header() {
    echo -e "${PURPLE}================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}================================${NC}"
}

# Function to show usage
show_usage() {
    echo "Personal Dictionary API - Management Script"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo ""
    echo "  🐳 Docker Management:"
    echo "    start [profile]     Start services (dev|prod|test|monitoring)"
    echo "    stop               Stop all services"
    echo "    restart [profile]   Restart services"
    echo "    build [service]     Build Docker images"
    echo "    logs [service]      Show service logs"
    echo "    shell [service]     Open shell in container"
    echo "    clean              Clean up containers and images"
    echo ""
    echo "  🧪 Testing:"
    echo "    test               Run tests"
    echo "    test-light         Run lightweight tests"
    echo "    test-coverage      Run tests with coverage"
    echo ""
    echo "  📦 Requirements:"
echo "    install [type]     Install requirements (all)"
echo "    update [type]      Update requirements"
echo "    freeze [type]      Freeze current versions"
    echo ""
    echo "  🗄️  Database:"
    echo "    db-migrate         Run database migrations"
    echo "    db-reset           Reset database"
    echo "    db-backup          Backup database"
    echo "    db-restore [file]  Restore database"
    echo ""
    echo "  🔧 Development:"
    echo "    dev-start          Start development environment"
    echo "    dev-stop           Stop development environment"
    echo "    dev-logs           Show development logs"
    echo ""
    echo "  🚀 Production:"
    echo "    prod-start         Start production environment"
    echo "    prod-stop          Stop production environment"
    echo "    prod-deploy        Deploy to production"
    echo ""
    echo "  📊 Monitoring:"
    echo "    monitor-start      Start monitoring stack"
    echo "    monitor-stop       Stop monitoring stack"
    echo ""
    echo "  🛠️  Utilities:"
    echo "    health             Check service health"
    echo "    status             Show service status"
    echo "    backup             Backup all data"
    echo "    restore [file]     Restore from backup"
    echo "    help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start dev         # Start development environment"
    echo "  $0 test              # Run tests"
    echo "  $0 install           # Install all requirements"
    echo "  $0 db-migrate        # Run database migrations"
    echo "  $0 health            # Check service health"
}

# Docker Management Functions
start_services() {
    local profile=${1:-dev}
    print_header "Starting Services (Profile: $profile)"
    
    case $profile in
        "dev")
            docker-compose --profile dev up -d
            ;;
        "prod")
            docker-compose --profile production up -d
            ;;
        "test")
            docker-compose --profile test up -d
            ;;
        "monitoring")
            docker-compose --profile monitoring up -d
            ;;
        *)
            docker-compose up -d
            ;;
    esac
    
    print_success "Services started successfully!"
}

stop_services() {
    print_header "Stopping Services"
    docker-compose down
    print_success "Services stopped successfully!"
}

restart_services() {
    local profile=${1:-dev}
    print_header "Restarting Services (Profile: $profile)"
    stop_services
    start_services $profile
}

build_images() {
    local service=${1:-}
    print_header "Building Docker Images"
    
    if [ -n "$service" ]; then
        docker-compose build $service
    else
        docker-compose build
    fi
    
    print_success "Images built successfully!"
}

show_logs() {
    local service=${1:-}
    if [ -n "$service" ]; then
        docker-compose logs -f $service
    else
        docker-compose logs -f
    fi
}

open_shell() {
    local service=${1:-server}
    print_header "Opening Shell in $service"
    docker-compose exec $service /bin/bash
}

clean_docker() {
    print_header "Cleaning Docker"
    
    # Stop and remove containers
    docker-compose down
    
    # Remove images
    docker rmi personal_dictionary-server 2>/dev/null || true
    docker rmi personal_dictionary-test 2>/dev/null || true
    
    # Clean up unused resources
    docker system prune -f
    docker volume prune -f
    
    print_success "Docker cleanup completed!"
}

# Testing Functions
run_tests() {
    print_header "Running Tests"
    docker-compose --profile test run --rm test pytest -v
}

run_tests_light() {
    print_header "Running Lightweight Tests"
    docker-compose --profile test run --rm test pytest -v -m "not ml_required"
}

run_tests_coverage() {
    print_header "Running Tests with Coverage"
    docker-compose --profile test run --rm test pytest --cov=src --cov-report=html --cov-report=term
}

# Requirements Management Functions
install_requirements() {
    local type=${1:-all}
    print_header "Installing Requirements ($type)"
    
    case $type in
        "all"|*)
            pip install -r requirements.txt
            ;;
    esac
    
    print_success "Requirements installed successfully!"
}

update_requirements() {
    local type=${1:-all}
    print_header "Updating Requirements ($type)"
    
    # Update pip first
    pip install --upgrade pip
    
    # Update requirements
    case $type in
        "all"|*)
            pip install --upgrade -r requirements.txt
            ;;
    esac
    
    print_success "Requirements updated successfully!"
}

freeze_requirements() {
    local type=${1:-all}
    print_header "Freezing Requirements ($type)"
    
    case $type in
        "all"|*)
            pip freeze > requirements-frozen.txt
            ;;
    esac
    
    print_success "Requirements frozen to requirements-frozen.txt"
}

# Database Functions
run_migrations() {
    print_header "Running Database Migrations"
    docker-compose exec server alembic upgrade head
    print_success "Migrations completed!"
}

reset_database() {
    print_warning "This will delete all data! Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_header "Resetting Database"
        docker-compose down
        docker volume rm personal_dictionary_db-data
        docker-compose up -d db
        sleep 10
        run_migrations
        print_success "Database reset completed!"
    else
        print_status "Database reset cancelled"
    fi
}

backup_database() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="backup_${timestamp}.sql"
    print_header "Backing up Database"
    
    docker-compose exec db pg_dump -U postgres dictionary > "backups/$backup_file"
    print_success "Database backed up to backups/$backup_file"
}

restore_database() {
    local file=${1:-}
    if [ -z "$file" ]; then
        print_error "Please specify backup file"
        exit 1
    fi
    
    print_header "Restoring Database from $file"
    docker-compose exec -T db psql -U postgres dictionary < "backups/$file"
    print_success "Database restored from $file"
}

# Development Functions
dev_start() {
    print_header "Starting Development Environment"
    start_services dev
    print_success "Development environment started!"
    echo ""
    echo "Services available at:"
    echo "  🌐 API: http://localhost:8000"
    echo "  📚 API Docs: http://localhost:8000/docs"
}

dev_stop() {
    print_header "Stopping Development Environment"
    stop_services
    print_success "Development environment stopped!"
}

dev_logs() {
    print_header "Development Logs"
    show_logs
}

# Production Functions
prod_start() {
    print_header "Starting Production Environment"
    start_services prod
    print_success "Production environment started!"
    echo ""
    echo "Production API available at: http://localhost:8001"
}

prod_stop() {
    print_header "Stopping Production Environment"
    docker-compose --profile production down
    print_success "Production environment stopped!"
}

prod_deploy() {
    print_header "Deploying to Production"
    build_images
    prod_stop
    prod_start
    print_success "Production deployment completed!"
}

# Monitoring Functions (simplified)
monitor_start() {
    print_header "Monitoring not available in simplified setup"
    print_warning "Monitoring services have been removed for simplicity"
}

monitor_stop() {
    print_header "Monitoring not available in simplified setup"
    print_warning "Monitoring services have been removed for simplicity"
}

# Utility Functions
check_health() {
    print_header "Checking Service Health"
    
    # Check if services are running
    if docker-compose ps | grep -q "Up"; then
        print_success "Services are running"
        
        # Check API health
        if curl -f http://localhost:8000/health >/dev/null 2>&1; then
            print_success "API is healthy"
        else
            print_warning "API health check failed"
        fi
        
        # Check database
        if docker-compose exec db pg_isready -U postgres >/dev/null 2>&1; then
            print_success "Database is healthy"
        else
            print_warning "Database health check failed"
        fi
        
        # Check Redis
        if docker-compose exec redis redis-cli ping >/dev/null 2>&1; then
            print_success "Redis is healthy"
        else
            print_warning "Redis health check failed"
        fi
    else
        print_error "No services are running"
    fi
}

show_status() {
    print_header "Service Status"
    docker-compose ps
}

backup_all() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_dir="backups/full_${timestamp}"
    
    print_header "Creating Full Backup"
    mkdir -p "$backup_dir"
    
    # Backup database
    backup_database
    
    # Backup Redis (if needed)
    docker-compose exec redis redis-cli BGSAVE
    
    # Backup volumes
    docker run --rm -v personal_dictionary_redis-data:/data -v "$(pwd)/$backup_dir:/backup" alpine tar czf /backup/redis-data.tar.gz -C /data .
    
    print_success "Full backup created in $backup_dir"
}

restore_all() {
    local backup_dir=${1:-}
    if [ -z "$backup_dir" ]; then
        print_error "Please specify backup directory"
        exit 1
    fi
    
    print_header "Restoring from Backup"
    
    # Restore database
    restore_database "$backup_dir/backup_*.sql"
    
    # Restore Redis (if needed)
    docker run --rm -v personal_dictionary_redis-data:/data -v "$(pwd)/$backup_dir:/backup" alpine tar xzf /backup/redis-data.tar.gz -C /data
    
    print_success "Restore completed from $backup_dir"
}

# Main script logic
case "${1:-help}" in
    # Docker Management
    "start")
        start_services $2
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        restart_services $2
        ;;
    "build")
        build_images $2
        ;;
    "logs")
        show_logs $2
        ;;
    "shell")
        open_shell $2
        ;;
    "clean")
        clean_docker
        ;;
    
    # Testing
    "test")
        run_tests
        ;;
    "test-light")
        run_tests_light
        ;;
    "test-coverage")
        run_tests_coverage
        ;;
    
    # Requirements
    "install")
        install_requirements $2
        ;;
    "update")
        update_requirements $2
        ;;
    "freeze")
        freeze_requirements $2
        ;;
    
    # Database
    "db-migrate")
        run_migrations
        ;;
    "db-reset")
        reset_database
        ;;
    "db-backup")
        backup_database
        ;;
    "db-restore")
        restore_database $2
        ;;
    
    # Development
    "dev-start")
        dev_start
        ;;
    "dev-stop")
        dev_stop
        ;;
    "dev-logs")
        dev_logs
        ;;
    
    # Production
    "prod-start")
        prod_start
        ;;
    "prod-stop")
        prod_stop
        ;;
    "prod-deploy")
        prod_deploy
        ;;
    
    # Monitoring
    "monitor-start")
        monitor_start
        ;;
    "monitor-stop")
        monitor_stop
        ;;
    
    # Utilities
    "health")
        check_health
        ;;
    "status")
        show_status
        ;;
    "backup")
        backup_all
        ;;
    "restore")
        restore_all $2
        ;;
    
    # Help
    "help"|*)
        show_usage
        exit 1
        ;;
esac

print_success "Command completed successfully!"
