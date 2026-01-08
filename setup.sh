#!/bin/bash

# Setup script for Moral LLM Assessment Platform
# This script automates the initial setup process

set -e

# Parse command line arguments
FORCE_RECREATE=false
if [[ "$1" == "--force" ]]; then
    FORCE_RECREATE=true
    echo "================================================"
    echo "Moral Reasoning Survey Platform - Setup Script"
    echo "                  FORCE MODE"
    echo "================================================"
    echo ""
    echo "⚠️  WARNING: This will DROP the existing database!"
    echo "   All data will be permanently deleted."
    echo ""
    read -p "   Are you sure you want to continue? (yes/no) " -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo "❌ Setup cancelled."
        exit 0
    fi
else
    echo "================================================"
    echo "Moral Reasoning Survey Platform - Setup Script"
    echo "================================================"
    echo ""
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Check if .env file exists and has LLM_API_KEY
if [ -f .env ]; then
    if grep -q "LLM_API_KEY=your_openrouter_api_key_here" .env; then
        echo "⚠️  Warning: LLM_API_KEY is not configured in .env"
        echo "   Please edit .env and set your actual OpenRouter API key"
        echo ""
        read -p "   Do you want to set it now? (y/n) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            read -p "   Enter your OpenRouter API key: " api_key
            sed -i "s/LLM_API_KEY=your_openrouter_api_key_here/LLM_API_KEY=$api_key/" .env
            echo "   ✅ API key configured"
        else
            echo "   ⚠️  Skipping API key configuration. You'll need to set it manually."
        fi
    else
        echo "✅ LLM_API_KEY is configured"
    fi
else
    echo "❌ Error: .env file not found"
    exit 1
fi

echo ""
echo "Step 1: Building Docker containers..."
echo "--------------------------------------"
docker compose up -d --build

echo ""
echo "Step 2: Installing Composer dependencies..."
echo "-------------------------------------------"
docker compose exec -T web composer install --no-interaction

echo ""
echo "Step 3: Creating database..."
echo "----------------------------"
sleep 5  # Wait for MySQL to be ready

if [ "$FORCE_RECREATE" = true ]; then
    echo "🗑️  Dropping existing database..."
    docker compose exec -T web php bin/console doctrine:database:drop --force --if-exists
    echo "✅ Database dropped"
    echo ""
    echo "📦 Creating fresh database..."
    docker compose exec -T web php bin/console doctrine:database:create
else
    docker compose exec -T web php bin/console doctrine:database:create --if-not-exists
fi

echo ""
echo "Step 4: Creating database schema..."
echo "------------------------------------"
if [ "$FORCE_RECREATE" = true ]; then
    docker compose exec -T web php bin/console doctrine:schema:create
else
    # Check if database has tables already
    if docker compose exec -T web php bin/console doctrine:schema:validate --no-interaction 2>&1 | grep -q "database schema is in sync"; then
        echo "✅ Database schema is already up to date"
    else
        # Try to run migrations first, if they exist
        if docker compose exec -T web php bin/console doctrine:migrations:migrate --no-interaction 2>/dev/null; then
            echo "✅ Migrations applied successfully"
        else
            # If migrations don't exist or fail, try to create schema
            if docker compose exec -T web php bin/console doctrine:schema:create 2>&1 | grep -q "already exists"; then
                echo "⚠️  Database schema already exists. Use './setup.sh --force' to recreate."
            else
                docker compose exec -T web php bin/console doctrine:schema:create
            fi
        fi
    fi
fi

echo ""
echo "Step 5: Seeding vignettes..."
echo "----------------------------"
docker compose exec -T web php bin/console app:seed-vignettes

echo ""
echo "Step 6: Clearing cache..."
echo "-------------------------"
docker compose exec -T web php bin/console cache:clear

echo ""
echo "================================================"
echo "✅ Setup Complete!"
echo "================================================"
echo ""
if [ "$FORCE_RECREATE" = true ]; then
    echo "🔄 Database has been recreated from scratch"
    echo ""
fi
echo "Your application is ready at: http://localhost:8080"
echo ""
echo "Database access:"
echo "  Host: localhost:3306"
echo "  Database: symfony"
echo "  Username: symfony"
echo "  Password: symfony"
echo ""
echo "Useful commands:"
echo "  View logs:        docker compose logs -f"
echo "  Stop containers:  docker compose down"
echo "  Restart:          docker compose restart"
echo "  Force recreate:   ./setup.sh --force"
echo ""
echo "For more information, see README.md and DOCUMENTATION.md"
echo ""
