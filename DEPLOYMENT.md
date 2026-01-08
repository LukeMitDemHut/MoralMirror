# Production Deployment Guide

This guide covers deploying the MoralMirror application to production.

## Prerequisites

- Docker & Docker Compose installed on production server
- Valid OpenRouter API key
- SSL certificate (recommended for production)
- Minimum 2GB RAM, 2 CPU cores
- 20GB disk space

## Environment Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd moralllmassessment
```

### 2. Configure Environment

Copy the example environment file and customize it:

```bash
cp .env.example .env
```

Edit `.env` and set the following **required** values:

```bash
# Generate a random 32-character string for APP_SECRET
APP_SECRET=$(openssl rand -hex 16)

# Set strong database passwords
MYSQL_ROOT_PASSWORD=<strong_random_password>
MYSQL_PASSWORD=<strong_random_password>

# Update DATABASE_URL with your password
DATABASE_URL="mysql://symfony:<strong_random_password>@db:3306/symfony?serverVersion=8.0&charset=utf8mb4"

# Add your OpenRouter API keys
VALIDATION_LLM_API_KEY=sk-or-v1-xxxxxxxxxxxxx
GENERATION_LLM_API_KEY=sk-or-v1-xxxxxxxxxxxxx

# Set your production domain
DEFAULT_URI=https://your-domain.com
```

### 3. Security Checklist

- [ ] Change all default passwords
- [ ] Generate new APP_SECRET
- [ ] Add real API keys
- [ ] Remove or disable PHPMyAdmin in production
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Review worker replica count based on server resources

## Deployment Options

### Option 1: Standard Deployment (Recommended for Development/Staging)

```bash
# Build and start containers
docker compose up -d --build

# Install dependencies (production mode)
docker compose exec web composer install --no-dev --optimize-autoloader

# Set up database
docker compose exec web php bin/console doctrine:database:create
docker compose exec web php bin/console doctrine:migrations:migrate --no-interaction

# Seed vignettes
docker compose exec web php bin/console app:seed-vignettes

# Clear and warm up cache
docker compose exec web php bin/console cache:clear
docker compose exec web php bin/console cache:warmup
```

### Option 2: Production Deployment (Stricter Security)

```bash
# Use the production compose file
docker compose -f docker-compose.prod.yml up -d --build

# Install dependencies
docker compose -f docker-compose.prod.yml exec web composer install --no-dev --optimize-autoloader

# Database setup
docker compose -f docker-compose.prod.yml exec web php bin/console doctrine:database:create
docker compose -f docker-compose.prod.yml exec web php bin/console doctrine:migrations:migrate --no-interaction

# Seed vignettes
docker compose -f docker-compose.prod.yml exec web php bin/console app:seed-vignettes

# Cache operations
docker compose -f docker-compose.prod.yml exec web php bin/console cache:clear --env=prod
docker compose -f docker-compose.prod.yml exec web php bin/console cache:warmup --env=prod
```

## Production Configuration

### Adjust Worker Replicas

Based on your server resources and expected load:

```bash
# In .env
WORKER_REPLICAS=5  # Start with 5, adjust based on monitoring
```

### Database Backups

Set up automated backups:

```bash
# Example backup script
docker compose exec db mysqldump -u symfony -p<password> symfony > backup_$(date +%Y%m%d).sql
```

### Monitoring

View logs:

```bash
# Web server logs
docker compose logs -f web

# Worker logs
docker compose logs -f worker

# Database logs
docker compose logs -f db
```

### Health Checks

Check application status:

```bash
# Check containers
docker compose ps

# Check web server
curl http://localhost:8080

# Check database connection
docker compose exec web php bin/console doctrine:query:sql "SELECT 1"
```

## Nginx Reverse Proxy (Recommended)

For production, place Nginx in front of your application:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Maintenance

### Update Application

```bash
git pull
docker compose down
docker compose up -d --build
docker compose exec web composer install --no-dev --optimize-autoloader
docker compose exec web php bin/console doctrine:migrations:migrate --no-interaction
docker compose exec web php bin/console cache:clear
```

### Scale Workers

```bash
# Update WORKER_REPLICAS in .env, then:
docker compose up -d --scale worker=10
```

### Database Migrations

```bash
docker compose exec web php bin/console doctrine:migrations:migrate
```

## Troubleshooting

### Workers Not Processing Jobs

```bash
# Check worker logs
docker compose logs worker

# Restart workers
docker compose restart worker

# Check messenger failed queue
docker compose exec web php bin/console messenger:failed:show
```

### Database Connection Issues

```bash
# Check database status
docker compose exec db mysql -u symfony -p -e "SELECT 1"

# Verify DATABASE_URL in .env matches credentials
```

### Clear All Cache

```bash
docker compose exec web php bin/console cache:pool:clear cache.global_clearer
docker compose exec web rm -rf var/cache/*
docker compose exec web php bin/console cache:warmup
```

## Security Best Practices

1. **Never commit .env files with real credentials**
2. **Use strong passwords** (20+ characters, random)
3. **Rotate API keys regularly**
4. **Keep Docker images updated**
5. **Monitor logs for suspicious activity**
6. **Disable debug mode in production** (APP_DEBUG=0)
7. **Use HTTPS only**
8. **Implement rate limiting** (consider adding to Nginx)
9. **Regular backups** (database + uploaded files)
10. **Monitor resource usage** (CPU, memory, disk)

## Support

For issues or questions, refer to:

- [Documentation](DOCUMENTATION.md)
- [Quick Reference](QUICK_REFERENCE.md)
- [README](README.md)
