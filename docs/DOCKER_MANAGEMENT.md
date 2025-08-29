# Docker & Requirements Management

This document explains the comprehensive Docker and requirements management system for the Personal Dictionary API.

## 📁 Simplified Project Structure

```
personal_dictionary/
├── requirements.txt      # All dependencies in one file
├── Dockerfile            # Development Dockerfile
├── Dockerfile.prod       # Production Dockerfile (multi-stage)
├── Dockerfile.test       # Testing Dockerfile
├── compose.yaml          # Docker Compose configuration
└── scripts/
    └── manage.sh         # Management script
```

## 🐳 Docker Configuration

### Dockerfiles

#### 1. **Dockerfile** (Development)
- **Purpose**: Development environment with hot reload
- **Features**: 
  - All dependencies included
  - Volume mounting for live code changes
  - Health checks
  - Non-root user for security

#### 2. **Dockerfile.prod** (Production)
- **Purpose**: Production deployment
- **Features**:
  - Multi-stage build for smaller images
  - Gunicorn for production serving
  - Optimized for performance
  - Security hardening

#### 3. **Dockerfile.test** (Testing)
- **Purpose**: Running tests
- **Features**:
  - Minimal dependencies
  - Fast build times
  - Test-specific optimizations

### Docker Compose Profiles

The `compose.yaml` uses profiles to organize services:

#### **Default Profile** (Core Services)
- `db` - PostgreSQL with pgvector
- `redis` - Redis cache
- `ollama` - Local LLM
- `server` - Development API server

#### **production Profile** (Production)
- `server-prod` - Production API server (port 8001)

#### **test Profile** (Testing)
- `test` - Test runner

## 📦 Requirements Management

### Single Requirements File

All dependencies are now consolidated into a single `requirements.txt` file:

```txt
# Personal Dictionary API - Complete Requirements
# This file includes all dependencies for the entire application

# =============================================================================
# API / Backend Framework
# =============================================================================
fastapi>=0.103.0
uvicorn[standard]>=0.35.0

# =============================================================================
# Database & ORM
# =============================================================================
sqlalchemy>=2.0.42
alembic>=1.16.4
psycopg2-binary>=2.9.10
pgvector>=0.4.1

# =============================================================================
# Machine Learning & AI
# =============================================================================
torch>=2.0.0
transformers>=4.44.0
sentence-transformers>=2.7.0
langchain>=0.2.0
langchain-ollama>=0.1.0

# =============================================================================
# Testing & Development
# =============================================================================
pytest>=7.4.0
black>=23.0.0
isort>=5.12.0

# =============================================================================
# Production
# =============================================================================
gunicorn>=21.2.0
uvloop>=0.17.0; sys_platform != "win32"
```

## 🛠️ Management Script

The `scripts/manage.sh` script provides comprehensive management capabilities:

### Usage
```bash
./scripts/manage.sh [COMMAND] [OPTIONS]
```

### Available Commands

#### **🐳 Docker Management**
```bash
# Start services
./scripts/manage.sh start dev          # Development environment
./scripts/manage.sh start prod         # Production environment
./scripts/manage.sh start test         # Test environment
./scripts/manage.sh start monitoring   # Monitoring stack

# Stop services
./scripts/manage.sh stop

# Build images
./scripts/manage.sh build              # Build all images
./scripts/manage.sh build server       # Build specific service

# View logs
./scripts/manage.sh logs               # All services
./scripts/manage.sh logs server        # Specific service

# Shell access
./scripts/manage.sh shell server       # Open shell in container

# Cleanup
./scripts/manage.sh clean              # Clean containers and images
```

#### **🧪 Testing**
```bash
# Run tests
./scripts/manage.sh test               # Full test suite
./scripts/manage.sh test-light         # Lightweight tests
./scripts/manage.sh test-coverage      # Tests with coverage
```

#### **📦 Requirements Management**
```bash
# Install requirements
./scripts/manage.sh install            # Install all dependencies

# Update requirements
./scripts/manage.sh update             # Update all requirements

# Freeze versions
./scripts/manage.sh freeze             # Freeze current versions
```

#### **🗄️ Database Management**
```bash
# Database operations
./scripts/manage.sh db-migrate         # Run migrations
./scripts/manage.sh db-reset           # Reset database
./scripts/manage.sh db-backup          # Backup database
./scripts/manage.sh db-restore file    # Restore from backup
```

#### **🔧 Development**
```bash
# Development environment
./scripts/manage.sh dev-start          # Start development
./scripts/manage.sh dev-stop           # Stop development
./scripts/manage.sh dev-logs           # View logs
```

#### **🚀 Production**
```bash
# Production environment
./scripts/manage.sh prod-start         # Start production
./scripts/manage.sh prod-stop          # Stop production
./scripts/manage.sh prod-deploy        # Deploy to production
```

#### **📊 Monitoring**
```bash
# Monitoring stack
./scripts/manage.sh monitor-start      # Start monitoring
./scripts/manage.sh monitor-stop       # Stop monitoring
```

#### **🛠️ Utilities**
```bash
# Health and status
./scripts/manage.sh health             # Check service health
./scripts/manage.sh status             # Show service status

# Backup and restore
./scripts/manage.sh backup             # Backup all data
./scripts/manage.sh restore file       # Restore from backup
```

## 🚀 Quick Start Guide

### 1. **Development Environment**
```bash
# Start development environment
./scripts/manage.sh dev-start

# Access services
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# pgAdmin: http://localhost:5050
# Redis Commander: http://localhost:8081
```

### 2. **Running Tests**
```bash
# Run all tests
./scripts/manage.sh test

# Run lightweight tests (faster)
./scripts/manage.sh test-light

# Run tests with coverage
./scripts/manage.sh test-coverage
```

### 3. **Production Deployment**
```bash
# Deploy to production
./scripts/manage.sh prod-deploy

# Access production API
# http://localhost:8001
```

### 4. **Testing**
```bash
# Run tests
./scripts/manage.sh test

# Run lightweight tests
./scripts/manage.sh test-light
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with your configuration:

```bash
# Database
DB_PASSWORD=your_secure_password

# LangSmith (optional)
LANGSMITH_TRACING=false
LANGSMITH_ENDPOINT=
LANGSMITH_API_KEY=

# Development tools
PGADMIN_EMAIL=admin@example.com
PGADMIN_PASSWORD=admin

# Monitoring
GRAFANA_PASSWORD=admin
```

### Service Ports

| Service | Port | Description |
|---------|------|-------------|
| API (Dev) | 8000 | Development API server |
| API (Prod) | 8001 | Production API server |
| Database | 5432 | PostgreSQL |
| Redis | 6379 | Redis cache |

## 📊 Performance Optimization

### Build Optimization
- **Multi-stage builds** for production images
- **Layer caching** for faster rebuilds
- **Minimal base images** for smaller sizes
- **CPU-only PyTorch** for production

### Runtime Optimization
- **Health checks** for service monitoring
- **Resource limits** for container management
- **Volume mounting** for persistent data
- **Network isolation** for security

### Development Optimization
- **Hot reload** for fast development
- **Volume mounting** for live code changes
- **Separate test environment** for isolation
- **Lightweight test images** for speed

## 🔒 Security Features

### Container Security
- **Non-root users** in all containers
- **Minimal base images** to reduce attack surface
- **Health checks** for service monitoring
- **Network isolation** between services

### Data Security
- **Volume encryption** for sensitive data
- **Backup encryption** for data protection
- **Environment variable** management
- **Secret management** for credentials

## 🐛 Troubleshooting

### Common Issues

#### **Build Failures**
```bash
# Clean and rebuild
./scripts/manage.sh clean
./scripts/manage.sh build

# Check logs
./scripts/manage.sh logs
```

#### **Service Health Issues**
```bash
# Check health
./scripts/manage.sh health

# Restart services
./scripts/manage.sh restart dev
```

#### **Database Issues**
```bash
# Run migrations
./scripts/manage.sh db-migrate

# Reset database (careful!)
./scripts/manage.sh db-reset
```

#### **Memory Issues**
```bash
# Check resource usage
docker stats

# Clean up resources
./scripts/manage.sh clean
```

### Logs and Debugging

#### **View Service Logs**
```bash
# All services
./scripts/manage.sh logs

# Specific service
./scripts/manage.sh logs server
```

#### **Shell Access**
```bash
# Access container shell
./scripts/manage.sh shell server
```

## 📈 Monitoring and Observability

### Metrics Collection
- **Prometheus** for metrics collection
- **Grafana** for visualization
- **Health checks** for service monitoring
- **Custom metrics** for application monitoring

### Logging
- **Structured logging** for better analysis
- **Log aggregation** for centralized monitoring
- **Log rotation** for storage management
- **Error tracking** for debugging

## 🔄 CI/CD Integration

### GitHub Actions Example
```yaml
name: Test and Deploy

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Tests
        run: ./scripts/manage.sh test-light

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Production
        run: ./scripts/manage.sh prod-deploy
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
