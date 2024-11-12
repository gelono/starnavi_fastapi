# starnavi_fastapi

This project implements a backend API that allows users to create posts and comments, which are then checked by an AI service for inappropriate content.

The AI model used is 'gemini-1.5-flash', which has been tested with English-language content.

# FastAPI Project

## Description
This is a FastAPI project utilizing PostgreSQL as the database and SQLAlchemy for ORM (Object-Relational Mapping). The API provides endpoints to manage posts and comments, with AI-driven moderation for inappropriate content.

## Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL
- Virtual Environment (recommended)

### Installation and Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/gelono/starnavi_fastapi.git
   cd starnavi_fastapi
   
2. Create and activate a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # For Linux/Mac
    venv\Scripts\activate     # For Windows

3. Install dependencies:
    ```bash
   pip install -r requirements.txt
   
4. Configure the PostgreSQL database:
    ```bash
   CREATE DATABASE your_db_name;
    CREATE USER your_db_user WITH PASSWORD 'your_db_password';
    ALTER ROLE your_db_user SET client_encoding TO 'utf8';
    ALTER ROLE your_db_user SET default_transaction_isolation TO 'read committed';
    ALTER ROLE your_db_user SET timezone TO 'UTC';
    GRANT ALL PRIVILEGES ON DATABASE your_db_name TO your_db_user;

5. Update config.py or your environment variables with your PostgreSQL database configuration:
SQLALCHEMY_DATABASE_URL = "postgresql://your_db_user:your_db_password@localhost/your_db_name"


6. Create database tables and apply migrations using Alembic:
   ```bash
   alembic upgrade head
   
7. Run the FastAPI development server:
    ```bash
   uvicorn main:app --reload

The FastAPI server will be available at http://127.0.0.1:8000.

Running Tests
1. To run tests, use the following command:
    ```bash
    pytest -v

API Documentation
FastAPI automatically generates interactive API documentation. Visit the following URL to explore the available endpoints:

- Swagger UI: http://127.0.0.1:8000/docs

- ReDoc UI: http://127.0.0.1:8000/redoc

Notes
- This project uses SQLAlchemy as the ORM and Alembic for database migrations.
- Make sure to set up your PostgreSQL database and update the connection details in config.py before running the application.
- The AI service used for content moderation (gemini-1.5-flash) is assumed to be configured and working as part of the backend.