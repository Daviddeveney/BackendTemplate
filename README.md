# Django Backend API

A Django REST API backend with automated CI/CD pipeline and Browserbase integration for web automation, with comprehensive test coverage.

## Project Structure

```
.
├── src/                # Source code
│   ├── apps/          # Application modules
│   │   └── api/       # Main API application
│   ├── core/          # Core configuration
│   └── manage.py      # Django CLI
├── .env              # Environment variables
├── .env.example      # Environment template
├── .gitignore        # Git ignore rules
└── requirements.txt   # Python dependencies
```

## Quick Start

1. Set up environment:
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings
```

2. Initialize database:
```bash
cd src
python manage.py migrate
python manage.py createsuperuser
```

3. Run server:
```bash
# Development
python manage.py runserver
```

## API Endpoints

- `GET /api/health/` - Health check
- `/admin/` - Admin interface

## Development

- Set `DEBUG=True` in `.env` for development
- Access admin at http://localhost:8000/admin/

## Docker Setup

### Development Environment

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Create `.env` file from example:
```bash
cp .env.example .env
```

3. Build and start the development environment:
```bash
docker-compose up --build
```

4. Run migrations:
```bash
docker-compose exec web python src/manage.py migrate
```

5. Create a superuser:
```bash
docker-compose exec web python src/manage.py createsuperuser
```

### Production Environment

1. Build and start the production environment:
```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

2. Check logs:
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

### Database Backups

1. Create a backup:
```bash
./scripts/backup_db.sh
```

Backups are stored in the `backups` directory and are automatically cleaned up after 30 days.

## Architecture

The application uses:
- Django with Django REST Framework
- PostgreSQL for database
- Redis for caching
- Nginx as reverse proxy (production)
- Docker for containerization

## Development

### Running Tests
```bash
docker-compose exec web python src/manage.py test
```

### Code Style
```bash
docker-compose exec web black .
docker-compose exec web isort .
```

## CI/CD

The project uses GitHub Actions for:
- Running tests
- Building Docker images
- Deploying to AWS EC2

## Monitoring

- Health check endpoint: `/health`
- Logs are available via Docker logs
- Database backups are automated

## Security

- HTTPS enforced in production
- CORS configured
- Strong password validation
- Redis for session storage
- Regular security updates

## Contributing

1. Create a feature branch
2. Make changes
3. Run tests
4. Create a pull request

## License

[Your License]