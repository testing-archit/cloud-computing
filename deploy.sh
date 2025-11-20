#!/bin/bash
# Deployment script for Compute Booking System

set -e

echo "🚀 Compute Booking System Deployment Script"
echo "==========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker first.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker found${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose not found. Please install Docker Compose first.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose found${NC}"

# Load environment
if [ -f .env ]; then
    echo -e "${GREEN}✅ .env file found${NC}"
    export $(cat .env | xargs)
else
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}Please edit .env with your configuration and run again.${NC}"
    exit 1
fi

# Create docker network
echo -e "\n${YELLOW}Creating Docker network...${NC}"
docker network create proxy 2>/dev/null || echo -e "${YELLOW}Network proxy already exists${NC}"

# Build and start services
echo -e "\n${YELLOW}Building and starting services...${NC}"
docker-compose up -d --build

echo -e "\n${GREEN}✅ Services started!${NC}"

# Wait for services to be healthy
echo -e "\n${YELLOW}Waiting for services to be healthy...${NC}"
sleep 10

# Check controller health
CONTROLLER_HEALTH=$(curl -s http://localhost:8000/api/auth/login || echo "error")
if [[ $CONTROLLER_HEALTH == *"error"* ]]; then
    echo -e "${YELLOW}⚠️  Controller not responding yet. Give it a moment...${NC}"
else
    echo -e "${GREEN}✅ Controller is healthy${NC}"
fi

# Check agent health
AGENT_HEALTH=$(curl -s http://localhost:5001/health || echo "error")
if [[ $AGENT_HEALTH == *"status"* ]]; then
    echo -e "${GREEN}✅ Agent 1 is healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Agent 1 not responding yet${NC}"
fi

echo -e "\n${GREEN}🎉 Deployment Complete!${NC}"
echo -e "\n📱 Access Points:"
echo -e "  API:               http://localhost:8000/api"
echo -e "  Frontend:          http://localhost:3000"
echo -e "  Traefik Dashboard: http://localhost:8080"
echo -e "  Agent 1:           http://localhost:5001/health"
echo -e "  Agent 2:           http://localhost:5002/health"
echo -e "  Database:          localhost:5432 (postgres)"
echo -e "  Redis:             localhost:6379"

echo -e "\n📖 Next Steps:"
echo -e "  1. View logs:        docker-compose logs -f controller"
echo -e "  2. Run tests:        docker-compose exec controller pytest tests/"
echo -e "  3. Register a user:  POST /api/auth/register"
echo -e "  4. Check status:     docker-compose ps"

echo -e "\n💡 For worker node setup, see NODE_SETUP.md"
