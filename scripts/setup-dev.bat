@echo off
REM MDUS System - Development Setup Script for Windows

echo 🚀 Setting up MDUS Development Environment...

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

REM Create necessary directories
echo 📁 Creating necessary directories...
if not exist "ai-service\models" mkdir "ai-service\models"
if not exist "ai-service\uploads" mkdir "ai-service\uploads"
if not exist "api-backend\uploads" mkdir "api-backend\uploads"
if not exist "web-frontend\build" mkdir "web-frontend\build"
if not exist "database\backups" mkdir "database\backups"
if not exist "logs" mkdir "logs"

REM Build Docker images
echo 🔨 Building Docker images...
docker-compose -f docker-compose.yml -f docker-compose.dev.yml build

REM Start database and redis first
echo 🚀 Starting core services...
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d postgres redis

REM Wait for database
echo ⏳ Waiting for database to be ready...
timeout /t 15 >nul

REM Start all services
echo 🌟 Starting all services...
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

echo.
echo ✅ Development environment is ready!
echo.
echo 🔗 Service URLs:
echo    - Frontend: http://localhost:3000
echo    - API Backend: http://localhost:8000
echo    - AI Service: http://localhost:8001
echo    - API Docs: http://localhost:8000/docs
echo.
echo 📊 Database Connection:
echo    - Host: localhost
echo    - Port: 5432
echo    - Database: mdus_db
echo    - User: mdus_user
echo.
echo 💾 Redis Connection:
echo    - Host: localhost
echo    - Port: 6379
echo.
echo 🔧 Useful commands:
echo    - View logs: docker-compose logs -f [service_name]
echo    - Stop services: docker-compose down
echo    - Restart service: docker-compose restart [service_name]
echo    - Shell access: docker-compose exec [service_name] /bin/bash

pause