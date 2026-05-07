# URL Shortener Web Application

A modern, production-ready URL shortener web application built with Python.

## Tech Stack

- **Framework**: FastAPI 0.133
- **Database**: PostgreSQL 18.3
- **ORM**: SQLModel
- **Authentication**: JWT with OAuth2 password flow (ROPC)
- **Migrations**: Alembic
- **Frontend**: HTML5 & Vanilla Javascript
- **Validation**: Pydantic
- **Testing**: Pytest

## Requirements

- Docker & Docker Compose (for containerized deployment)
- Python 3.14+ (if running without Docker)
- PostgreSQL 18.3+ (if running without Docker)

## Getting Started

### Using Docker Compose (Recommended)

The easiest way to get the application running:

```bash
# Clone the repository
git clone https://github.com/wcxt/py-link-shortener.git
cd py-link-shortener

# Create environment file
cp .env.example .env  # Edit with your configuration

# Start all services
docker compose up

# Application will be available at http://localhost:8000
```