#!/bin/bash

# MDUS System - Development Setup Script

set -e

echo "🚀 Setting up MDUS Development Environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p ai-service/models
mkdir -p ai-service/uploads
mkdir -p api-backend/uploads
mkdir -p web-frontend/build
mkdir -p database/backups
mkdir -p logs

# Set proper permissions
chmod 755 ai-service/models
chmod 755 ai-service/uploads
chmod 755 api-backend/uploads

# Build and start services
echo "🔨 Building Docker images..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml build

echo "🚀 Starting development services..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d postgres redis

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 15

# Start all services
echo "🌟 Starting all services..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

echo "✅ Development environment is ready!"
echo ""
echo "🔗 Service URLs:"
echo "   - Frontend: http://localhost:3000"
echo "   - API Backend: http://localhost:8000"
echo "   - AI Service: http://localhost:8001"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "📊 Database Connection:"
echo "   - Host: localhost"
echo "   - Port: 5432"
echo "   - Database: mdus_db"
echo "   - User: mdus_user"
echo ""
echo "💾 Redis Connection:"
echo "   - Host: localhost"
echo "   - Port: 6379"
echo ""
echo "🔧 Useful commands:"
echo "   - View logs: docker-compose logs -f [service_name]"
echo "   - Stop services: docker-compose down"
echo "   - Restart service: docker-compose restart [service_name]"
echo "   - Shell access: docker-compose exec [service_name] /bin/bash"