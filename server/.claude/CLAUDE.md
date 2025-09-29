# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a **FastAPI-based Korean recipe recommendation API** that suggests recipes based on fridge ingredients. The system uses **PostgreSQL** for persistent data storage and **Redis** for session management.

### Core Architecture
- **FastAPI Application**: Async web framework with automatic OpenAPI documentation
- **Session-Based System**: Uses Redis sessions for both registered and guest users
- **Environment-Aware Configuration**: Dynamic settings based on ENVIRONMENT variable (dev/prod/test)
- **Authentication**: JWT tokens for registered users, session IDs for guests
- **Database**: PostgreSQL with SQLAlchemy async ORM and Alembic migrations

### Key Architectural Patterns
- **Modular Structure**: Separated into `api`, `core`, `models`, and `schemas` packages
- **Dependency Injection**: FastAPI dependencies for database and Redis connections
- **Pydantic Models**: Type-safe request/response validation with schemas
- **Environment Isolation**: Separate configurations for development, production, and testing
- **Async Throughout**: Full async/await pattern for database and Redis operations

## Essential Commands

### Environment Setup
```bash
# Activate conda environment (required)
conda activate fridge2fork

# Install dependencies
pip install -r requirements.dev.txt     # Development
pip install -r requirements.prod.txt    # Production
```

### Development Server
```bash
# Preferred method - uses proper environment loading
python scripts/run_dev.py

# Alternative - direct execution
ENVIRONMENT=development python main.py
```

### Production Server
```bash
python scripts/run_prod.py
# or
ENVIRONMENT=production python main.py
```

### Database Operations
```bash
# Run migrations
python scripts/migrate.py

# Generate new migration
alembic revision --autogenerate -m "description"

# Apply migrations manually
alembic upgrade head
```

### Testing
```bash
# Run all tests with coverage
python scripts/run_tests.py

# Run with coverage report
python scripts/run_tests.py --coverage

# Generate detailed HTML coverage report
python scripts/test_coverage.py

# Run specific test file
python scripts/run_tests.py --file tests/test_recipes.py

# Run specific test function
python scripts/run_tests.py --function test_login_success
```

### Code Quality
```bash
# Format code
black .
isort .

# Lint code
flake8

# Type checking
mypy app/
```

## Configuration System

### Environment Variables Priority
1. **Kubernetes Secrets** → Environment variables (POSTGRES_*)
2. **Environment-specific files** (.env.dev, .env.prod)
3. **Common configuration** (.env.common)
4. **Defaults** in Settings class

### Critical Environment Variables
- `ENVIRONMENT`: Controls which settings class and env files are loaded
- `POSTGRES_*`: Database connection (injected by Kubernetes in production)
- `JWT_SECRET_KEY`: Must be changed in production
- `REDIS_URL`: Session storage connection

### Environment Behavior
- **dev**: Debug enabled, docs available, local database expected
- **prod**: Debug disabled, no docs, Kubernetes secrets expected
- **test**: SQLite in-memory database, isolated Redis DB

## API Structure

### Current Active Endpoints
- `/fridge2fork/v1/recipes/*` - Recipe management and search
- `/fridge2fork/v1/fridge/*` - User ingredient management
- `/fridge2fork/v1/system/*` - Health checks and platform info

### Authentication Architecture
- **Current State**: Auth and User modules are disabled (commented out in api.py:7-8, 16)
- **Planned Migration**: Moving to Supabase authentication
- **Session Management**: Redis-based sessions work independently of authentication

### Session vs Authentication
- **Sessions**: Used for fridge management (works for guests and users)
- **JWT Tokens**: Will be used for user-specific features when auth is re-enabled
- **Current Operation**: System functions without authentication using sessions only

## Database Schema

### Models Location
- `app/models/` - SQLAlchemy ORM models
- `app/schemas/` - Pydantic request/response schemas

### Key Models
- **Recipe**: Core recipe data with ingredients and instructions
- **User**: User accounts (disabled but schema exists)
- **System**: Platform and version information

## Testing Strategy

### Test Configuration
- **Isolated Database**: SQLite in-memory for tests
- **Redis Separation**: Uses DB 15 for test isolation
- **Auto Fixtures**: Test users and recipes auto-generated
- **Coverage Target**: 80% minimum (enforced by pytest config)

### Test Structure
```
tests/
├── conftest.py          # Shared fixtures and test configuration
├── test_recipes.py      # Recipe API tests
├── test_fridge.py       # Fridge management tests
├── test_system.py       # System endpoint tests
└── test_main.py         # Application startup tests
```

## Development Guidelines

### File Organization
- **Never modify** `app/api/v1/api.py` without understanding auth dependencies
- **Check environment files** exist before running (scripts handle this)
- **Use scripts/** for execution rather than direct commands
- **Conda environment required** - most dependency issues stem from wrong environment

### Common Patterns
- **Async functions**: All database operations use `async`/`await`
- **Dependency injection**: Use FastAPI `Depends()` for database sessions
- **Error handling**: Return structured JSON errors with appropriate status codes
- **Logging**: Use structured logging with environment-appropriate levels

### Conda Environment Critical
This project **requires conda environment `fridge2fork`** to be active. Most import errors, dependency issues, and path problems are caused by running outside the conda environment.

## Troubleshooting

### Database Connection Issues
1. Verify PostgreSQL/Redis servers are running
2. Check environment variables in `.env.dev` or `.env.prod`
3. Run `python scripts/migrate.py` to ensure schema is current

### Import Errors
1. Ensure `conda activate fridge2fork` is run
2. Verify `requirements.dev.txt` is installed in conda environment
3. Check `PYTHONPATH` includes project root

### Authentication Disabled
Current authentication modules are intentionally disabled pending Supabase migration. Do not re-enable without updating all dependent user functionality.