# MDUS System - Docker Environment Setup

## Overview

The Multi-Modal Document Understanding System (MDUS) is containerized using Docker for consistent development and deployment environments. This setup includes:

- **AI Processing Service**: Python-based ML service with LayoutLMv3 and Donut models
- **API Backend**: FastAPI-based REST API and WebSocket server
- **Web Frontend**: React-based user interface with hot-reload
- **Database**: PostgreSQL for persistent data storage
- **Cache/Queue**: Redis for caching and background job processing
- **Reverse Proxy**: Nginx for production load balancing

## Prerequisites

### Required Software
- Docker Engine 20.10+
- Docker Compose 2.0+
- Git

### System Requirements
- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Storage**: 20GB available disk space
- **CPU**: Multi-core processor (4+ cores recommended)
- **OS**: Windows 10/11, macOS 10.15+, or Linux

## Quick Start

### 1. Navigate to Project Directory
```bash
cd C:\Users\wisdo\OneDrive\Desktop\Data-Science-ML\MDUS-system
```

### 2. Environment Configuration
The `.env` file is already created with default values. Update passwords and secrets as needed:
- `POSTGRES_PASSWORD`
- `REDIS_PASSWORD`  
- `JWT_SECRET`

### 3. Development Setup

#### For Windows:
```batch
scripts\setup-dev.bat
```

#### For Linux/macOS:
```bash
chmod +x scripts/setup-dev.sh
./scripts/setup-dev.sh
```

### 4. Manual Setup (if scripts fail)
```bash
# Build all services
docker-compose -f docker-compose.yml -f docker-compose.dev.yml build

# Start core services
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d postgres redis

# Wait 15 seconds for database initialization
timeout /t 15

# Start all services
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

## Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | React web interface |
| API Backend | http://localhost:8000 | FastAPI REST API |
| AI Service | http://localhost:8001 | ML processing service |
| API Documentation | http://localhost:8000/docs | Swagger/OpenAPI docs |
| Database | localhost:5432 | PostgreSQL direct access |
| Redis | localhost:6379 | Redis direct access |

## Development Workflow

### Hot Reload
All services support hot-reload in development:
- **Frontend**: React hot-reload enabled
- **API Backend**: Uvicorn auto-reload on file changes
- **AI Service**: Uvicorn auto-reload on file changes

### Code Changes
1. Edit files in respective service directories
2. Changes are automatically detected and services reload
3. Database migrations run automatically on API service start

### Debugging
```bash
# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f api_backend

# Access service shell
docker-compose exec api_backend /bin/bash

# Run commands in service
docker-compose exec api_backend python -c "print('Hello')"
```

## Environment Variables

Key environment variables in `.env`:

### Database
- `POSTGRES_DB`: Database name (mdus_db)
- `POSTGRES_USER`: Database username (mdus_user)
- `POSTGRES_PASSWORD`: Database password
- `POSTGRES_PORT`: Database port (5432)

### Redis
- `REDIS_PASSWORD`: Redis password
- `REDIS_PORT`: Redis port (6379)

### Security
- `JWT_SECRET`: JWT token signing secret
- `CORS_ORIGINS`: Allowed CORS origins

### Services
- `API_PORT`: API backend port (8000)
- `AI_SERVICE_PORT`: AI service port (8001)
- `FRONTEND_PORT`: Frontend port (3000)

## Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check what's using the port
netstat -ano | findstr :3000

# Kill process using port (Windows)
taskkill /PID [PID] /F
```

#### Docker Issues
```bash
# Check Docker status
docker info

# Restart Docker Desktop
# Stop and start Docker Desktop application
```

#### Database Connection Issues
```bash
# Check database logs
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

#### Memory Issues
```bash
# Check container resource usage
docker stats

# Increase Docker memory limits in Docker Desktop settings
```

### Service-Specific Debugging

#### AI Service
```bash
# Check model downloads
docker-compose exec ai_service ls -la /app/models

# Test Python environment
docker-compose exec ai_service python --version
```

#### API Backend
```bash
# Check Python environment
docker-compose exec api_backend pip list

# Test database connection
docker-compose exec api_backend python -c "import asyncpg; print('OK')"
```

#### Frontend
```bash
# Check npm installation
docker-compose exec web_frontend npm list --depth=0

# Rebuild if needed
docker-compose exec web_frontend npm install
```

## File Structure

```
C:\Users\wisdo\OneDrive\Desktop\Data-Science-ML\MDUS-system\
├── docker-compose.yml          # Main Docker Compose file
├── docker-compose.dev.yml      # Development overrides
├── .env                        # Environment variables
├── ai-service/
│   ├── Dockerfile
│   └── requirements.txt
├── api-backend/
│   ├── Dockerfile
│   └── requirements.txt
├── web-frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── nginx.conf
├── database/
│   └── init/
│       └── 01_init_schema.sql
├── nginx/
│   └── nginx.conf
└── scripts/
    ├── setup-dev.bat
    └── setup-dev.sh
```

## Next Steps

1. **Run the setup script** to start all services
2. **Access the frontend** at http://localhost:3000
3. **Check API documentation** at http://localhost:8000/docs
4. **Begin development** by adding application code to each service directory

## Common Commands

```bash
# Start all services
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Stop all services
docker-compose down

# View all logs
docker-compose logs -f

# Restart specific service
docker-compose restart api_backend

# Build and restart service
docker-compose up -d --build ai_service

# Remove all containers and volumes
docker-compose down -v
```

## Support

For issues:
1. Check service logs: `docker-compose logs [service]`
2. Verify Docker is running: `docker info`
3. Check environment variables: `docker-compose config`
4. Restart services: `docker-compose restart`