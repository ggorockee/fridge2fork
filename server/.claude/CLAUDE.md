# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Django-based backend for Fridge2Fork (냉털레시피)** - Korean recipe recommendation service based on refrigerator ingredients.

This is a fresh Django 5.2.7 project with Django Ninja for API development, currently in initial setup phase.

## Technology Stack

- **Framework**: Django 5.2.7
- **API Layer**: Django Ninja (REST API framework)
- **Database**: PostgreSQL (configured via `.env`, currently using SQLite default)
- **Python Version**: 3.12+
- **Package Manager**: uv

## Project Structure

```
server/
├── app/                      # Django project root
│   ├── settings/             # Settings module
│   │   ├── settings.py       # Main Django settings
│   │   ├── urls.py           # Root URL configuration
│   │   ├── wsgi.py           # WSGI entry point
│   │   └── asgi.py           # ASGI entry point
│   ├── core/                 # Core app (utilities, base models)
│   ├── recipes/              # Recipes app
│   ├── users/                # Users app
│   ├── manage.py             # Django management script
│   └── db.sqlite3            # SQLite database (temporary)
├── .env                      # Environment variables (PostgreSQL config)
├── pyproject.toml            # Project dependencies
└── uv.lock                   # Dependency lock file
```

## Development Commands

### Environment Setup

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
uv pip install -e .

# Or sync from lock file
uv pip sync uv.lock
```

### Database Operations

```bash
# Run migrations
python app/manage.py migrate

# Create new migration
python app/manage.py makemigrations

# Create superuser for admin
python app/manage.py createsuperuser

# Database shell
python app/manage.py dbshell
```

### Development Server

```bash
# Run development server (default port 8000)
python app/manage.py runserver

# Run on specific port
python app/manage.py runserver 8080

# Access Django admin
# http://localhost:8000/admin/
```

### Testing

```bash
# Run all tests
python app/manage.py test

# Run tests for specific app
python app/manage.py test app.recipes

# Run tests with coverage (requires coverage package)
coverage run app/manage.py test
coverage report
```

### Django Shell

```bash
# Django shell with auto-imports
python app/manage.py shell

# IPython shell (if installed)
python app/manage.py shell -i ipython
```

## Architecture Decisions

### Settings Module Pattern

The project uses `settings/` directory instead of single `settings.py`:
- Enables environment-specific settings (dev, prod, test)
- `DJANGO_SETTINGS_MODULE` is set to `settings.settings`
- Future expansion: Create `settings/dev.py`, `settings/prod.py` inheriting from base

### App Organization

Three Django apps with specific responsibilities:
- **core**: Shared utilities, base models, common functionality
- **recipes**: Recipe models, views, API endpoints
- **users**: User authentication, profiles, preferences

### Database Configuration

PostgreSQL credentials in `.env`:
```
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=f2f
POSTGRES_PASSWORD=<password>
POSTGRES_DB=f2f
```

**Current state**: Using SQLite (Django default)
**Next step**: Update `settings/settings.py` to use PostgreSQL via environment variables

### Django Ninja Integration

Django Ninja is included in dependencies for API development:
- Provides FastAPI-like experience in Django
- Type hints and automatic OpenAPI schema
- Better performance than Django REST Framework

## Development Workflow

### Adding New Features

1. **Create or update models** in appropriate app (`recipes/models.py`, `users/models.py`)
2. **Generate migrations**: `python app/manage.py makemigrations`
3. **Review migration files** in `app/<appname>/migrations/`
4. **Apply migrations**: `python app/manage.py migrate`
5. **Register models** in `admin.py` for Django admin access
6. **Create API endpoints** using Django Ninja

### Database Migrations Best Practices

- Always review auto-generated migrations before applying
- Use descriptive migration names: `python app/manage.py makemigrations --name add_recipe_difficulty`
- Test migrations in development before production
- Keep migrations reversible when possible

### Testing Guidelines

- Write tests in `app/<appname>/tests/` or `app/<appname>/tests.py`
- Use Django's `TestCase` for database-dependent tests
- Use `SimpleTestCase` for tests without database
- Test models, views, and API endpoints separately

## Environment Variables

The `.env` file is git-ignored and contains:
- Database connection settings (PostgreSQL)
- Secret keys (will be needed when configured)
- Environment-specific configuration

**Security Note**: Never commit `.env` files. Use `.env.example` template for documentation.

## Integration with Monorepo

This server is part of the Fridge2Fork monorepo:
- **Monorepo root**: `../` (contains mobile, admin, scrape, docs)
- **Shared documentation**: `../.claude/CLAUDE.md` (monorepo-level guide)
- **Deployment**: Kubernetes configurations in `k8s/` (to be added)

## Next Steps

This is a fresh Django project. Expected next development steps:

1. **Database Migration**: Switch from SQLite to PostgreSQL
2. **Model Definition**: Define Recipe, Ingredient, User models
3. **API Layer**: Implement Django Ninja endpoints
4. **Authentication**: JWT or session-based auth for API
5. **Admin Interface**: Configure Django admin for data management

## Common Issues

### Import Errors

If you see "Couldn't import Django" error:
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Verify Django installation
python -c "import django; print(django.get_version())"
```

### Database Connection Issues

Currently using SQLite by default. To switch to PostgreSQL:
1. Update `DATABASES` in `settings/settings.py`
2. Install `psycopg2-binary`: `uv pip install psycopg2-binary`
3. Ensure PostgreSQL server is running
4. Run migrations: `python app/manage.py migrate`

### Secret Key Security

The current `SECRET_KEY` in `settings.py` is marked as insecure (development-only).
For production:
1. Generate new secret key: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
2. Store in environment variable or `.env` file
3. Update settings to read from environment
